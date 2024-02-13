import datetime
import time
import requests
import pickle
import os.path
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
from openpyxl import load_workbook

LOGIN = "login_here"
PASSWORD = "password_here"
RESULTS = 100
VACANCY = 'programmist'
URL = f"https://hh.kz/vacancies/{VACANCY}"

index = 1
n = 1
limiter = False

name_list = []
date_list = []
company_list = []
salary_list = []
address_list = []
vacancyurl_list = []

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
}

# check if cookies already exist else authorize and save cookies
if os.path.isfile('cookies'):
    with open("cookies", "rb") as f:
        cookies = pickle.load(f)
else:
    driver_path = r'path'
    ser = Service(driver_path)

    chrome_options = Options()
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(options=chrome_options)

    driver.get('https://hh.ru/account/login')
    time.sleep(1)

    login = driver.find_element(By.CSS_SELECTOR, 'input[name="login"]')
    login.send_keys(LOGIN)

    select_password_login = driver.find_element(By.CSS_SELECTOR, '[data-qa="expand-login-by-password"]').click()
    password = driver.find_element(By.CSS_SELECTOR, 'input[data-qa="login-input-password"]')
    password.send_keys(PASSWORD, Keys.ENTER)
    time.sleep(3)

    # save cookies from selenium
    with open('cookies', 'wb') as f:
        pickle.dump(driver.get_cookies(), f)

    # load cookies
    with open("cookies", "rb") as f:
        cookies = pickle.load(f)

# Enter URl and prompt to enter again if URl is not correct or cannot be reached
while True:
    url = URL
    check_if_correct = requests.get(url, headers=headers, timeout=10)
    if check_if_correct.status_code == 200:
        break
    print('Указана неверная ссылка либо данной категории не существует.\n')

# Enter how many results you want to see
result_count = RESULTS

while True:
    s = requests.Session()

    # add cookies to our Session by loading cookies file
    for cookie in cookies:
        s.cookies.set(cookie['name'], cookie['value'])

    # send a GET request to the website and increment the page number with each cycle
    response = s.get(f"{url}?page={n}", headers=headers)

    # Use BeatifulSoup to get access to all vacancy blocks on the website
    bs = BeautifulSoup(response.content, 'html.parser')
    vacancies = bs.select('div.serp-item')
    # Get each vacancy block
    for vacancy in vacancies:
        # Iterate until index is no larger than result_count
        if index <= result_count:
            # Get name, company name, salary, publication date, and vacancy url in each block, and append to lists
            name = vacancy.select_one('[data-qa="serp-item__title"]')
            company = vacancy.select_one('[data-qa="vacancy-serp__vacancy-employer"]')
            salary_level = vacancy.select_one('span[data-qa="vacancy-serp__vacancy-compensation"]')
            date = vacancy.select_one('.vacancy-serp-item__publication-date')
            address = vacancy.select_one('[data-qa="vacancy-serp__vacancy-address"]')
            name_list.append(name.text)
            if date:
                date_list.append(date.text)
            else:
                date_list.append('Не найдено')
            if company:
                company_list.append(company.text)
            else:
                company_list.append('Не найдено')
            if salary_level:
                salary_list.append(salary_level.text)
            else:
                salary_list.append('Не указано')
            if address:
                address_list.append(address.text)
            else:
                address.append('Не указано')

        else:
            # As soon as index becomes equal to result_count, set limiter to True to finish the loop
            limiter = True
        index += 1

    # save the results to an Excel file
    if limiter:
        df = pd.DataFrame({'Name': name_list,
                           'Company': company_list,
                           'Salary': salary_list,
                           'Date': date_list,
                           'Address': address_list
                           })

        current_time = time.strftime("%H_%M")
        now = datetime.datetime.now()
        filename = f'vacancies_{VACANCY}_{now.isoformat(timespec="milliseconds")}.xlsx'

        # If file does not exist, write a new one, else load and append results to an existing one
        if not os.path.isfile(filename):
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=current_time, index=False)
        else:
            with pd.ExcelWriter(filename, mode='a', engine='openpyxl', if_sheet_exists='new') as writer:
                writer.book = load_workbook(filename)
                df.to_excel(writer, sheet_name=current_time, index=False)
        break
    n += 1