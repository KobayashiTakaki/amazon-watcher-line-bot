import os
from datetime import datetime, timezone, timedelta
import re
import configparser
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def firefox_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('disable-infobars')
    options.add_argument('--disable-extensions')
    return webdriver.Firefox(firefox_options=options)

def create_broad_cast_message(text):
    dirname = os.path.dirname(__file__)
    config = configparser.ConfigParser()
    config.read(os.path.join(dirname, 'config.ini'))
    channel_access_token = config['DEFAULT']['CHANNEL_ACCESS_TOKEN']
    url = 'https://api.line.me/v2/bot/message/broadcast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {}'.format(channel_access_token)
    }
    data = {
        'messages': [
            {
                'type': 'text',
                'text': text
            }
        ]
    }
    requests.post(url, data=json.dumps(data), headers=headers)

def fetch_amazon_data(url, driver):
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'productTitle'))
    )
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'addToCart'))
    )
    soup = BeautifulSoup(driver.page_source, "html.parser")
    title = soup.find(id='productTitle').text.strip()
    price_text = soup.select('#price #priceblock_ourprice_row #priceblock_ourprice')[0].text
    price = int(re.sub(r'[^0-9]', '', price_text))
    return { 'title': title, 'price': price, 'url': url }

def fetch_rakuten_data(url, driver):
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'searchresultitem'))
    )
    soup = BeautifulSoup(driver.page_source, "html.parser")
    link_elem = soup.select_one('.searchresultitems .searchresultitem .title h2 a')
    title = link_elem.text
    url = link_elem.get('href')
    price_text = soup.select_one('.searchresultitems .searchresultitem .price span').text
    price = int(re.sub(r'[^0-9]', '', price_text))
    return { 'title': title, 'price': price, 'url': url }

def fetch_item_data():
    dirname = os.path.dirname(__file__)
    f = open(os.path.join(dirname, 'targets.json'))
    targets = json.loads(f.read())['targets']
    f.close()
    histories_file_path = os.path.join(dirname, 'histories.json')
    if not os.path.isfile(histories_file_path):
        with open(histories_file_path, mode='w') as f:
            pass
    f = open(histories_file_path)
    text = f.read()
    histories = json.loads(text)['histories'] if 0 < len(text) else {}
    f.close()

    driver = firefox_driver()
    results = []
    new_histories = {'histories': {}}
    now = datetime.now(timezone.utc)

    for target in targets:
        if target['url'] in histories.keys()\
           and now - timedelta(hours=3) <\
               datetime.strptime(histories[target['url']], '%Y-%m-%d %H:%M:%S%z'):
                new_histories['histories'][target['url']] = histories[target['url']]
                continue
        if 'amazon.co.jp' in target['url']:
            data = fetch_amazon_data(target['url'], driver)
        if 'rakuten.co.jp' in target['url']:
            data = fetch_rakuten_data(target['url'], driver)
        if data['price'] < target['limit']:
            results.append({
                'title': data['title'],
                'url': data['url'],
                'price': str(data['price'])
            })
            new_histories['histories'][target['url']] = now.strftime('%Y-%m-%d %H:%M:%S%z')
    with open(histories_file_path, mode='w') as f:
        f.write(json.dumps(new_histories))
    driver.close()
    return results

if __name__ == '__main__':
    results = fetch_item_data()
    for result in results:
        text = '\n'.join([result['title'], result['url'], '¥' + result['price']])
        create_broad_cast_message(text)
