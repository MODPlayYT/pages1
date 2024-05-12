import json
from urllib.parse import urljoin, quote_plus
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

BASEURL = 'https://megamarket.ru/'

def get_pages_html(url):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.maximize_window()
    ITEMS = []
    try:
        page = 1
        while True:
            print(f"[+] Страница {page}")
            driver.get(url=url.replace('page_num', f'page-{page}'))
            WebDriverWait(driver, 60).until(
                ec.presence_of_element_located((By.CLASS_NAME, "catalog-items-desktop"))
            )
            if not get_items(driver.page_source, ITEMS):
                break
            page += 1
            time.sleep(2)  # добавляем небольшую задержку перед загрузкой следующей страницы
    except Exception as ex:
        print(ex)
    finally:
        driver.close()
        driver.quit()
    return ITEMS


def apply_filters(url, min_price, max_price):
    if min_price.isdigit() and max_price.isdigit():
        filter_data = {
            "88C83F68482F447C9F4E401955196697": {"min": int(min_price), "max": int(max_price)},
            "4CB2C27EAAFC4EB39378C4B7487E6C9E": ["1"]
        }
        json_data = json.dumps(filter_data)
        url_encoded_data = quote_plus(json_data)
        url += '#?filters=' + url_encoded_data
    return url


def get_items(html, items):
    soup = BeautifulSoup(html, 'html.parser')
    item_divs = soup.find_all('div', class_='catalog-item')
    if len(item_divs) == 0:
        return False
    for item in item_divs:
        link = BASEURL + item.find('a', class_='ddl_product_link').get('href')
        item_price = item.find('div', class_='catalog-item-price')
        if item_price:
            item_price_result = item_price.find('span').get_text()
            item_bonus = item.find('div', class_='money-bonus')
            if item_bonus:
                item_bonus_percent = item.find('span', class_='bonus-percent').get_text()
                item_bonus_amount = item.find('span', class_='bonus-amount').get_text()
                item_title = item.find('div', class_='catalog-item__title').get_text()
                item_merchant_name = item.find('div', class_='catalog-item__merchant-info-name')
                if item_merchant_name:
                    item_merchant_name = item_merchant_name.get_text()
                else:
                    item_merchant_name = '-'

                bonus = int(item_bonus_amount.replace(' ', ''))
                price = int(item_price_result[0:-1].replace(' ', ''))
                bonus_percent = int(item_bonus_percent.replace('%', ''))
                items.append({
                    'Наименование': item_title,
                    'Продавец': item_merchant_name,
                    'Цена': price,
                    'Сумма бонуса': bonus,
                    'Процент бонуса': bonus_percent,
                    'Ссылка на товар': link
                })
            else:
                print("Не удалось найти информацию о бонусах")
        else:
            print("Не удалось найти информацию о цене")
    return True

def save_excel(data: list, filename: str):
    if not data:
        print("Нет данных для сохранения.")
        return
    
    try:
        df = pd.DataFrame(data)
        writer = pd.ExcelWriter(f"{filename}.xlsx", engine='xlsxwriter')
        df.to_excel(writer, sheet_name='data', index=False)
        writer.save()
        print(f"Данные успешно сохранены в {filename}.xlsx")
    except Exception as e:
        print(f"Ошибка при сохранении данных в Excel: {e}")


def main():
    target = input('Введите название товара: ')
    min_price = input('Минимальная цена: ')
    min_price = min_price if min_price != '' else '0'
    max_price = input('Максимальная цена: ')
    max_price = max_price if max_price != '' else '9999999'

    target_url = urljoin(BASEURL, f"/catalog/page_num/?q={quote_plus(target)}")
    target_url = apply_filters(target_url, min_price, max_price)

    items = get_pages_html(url=target_url)
    if items:
        save_excel(items, target)
    else:
        print("Нет данных для сохранения.")


    
if __name__ == '__main__':
    main()
