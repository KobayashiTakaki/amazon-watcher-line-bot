import os
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

def fetch_item_data():
    dirname = os.path.dirname(__file__)
    f = open('{}targets.json'.format(dirname))
    targets = json.loads(f.read())['targets']
    f.close()
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('disable-infobars')
    options.add_argument('--disable-extensions')
    driver = webdriver.Firefox(firefox_options=options)
    results = []
    for target in targets:
        driver.get(target['url'])
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.ID, 'productTitle'))
        )
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.ID, 'addToCart'))
        )
        soup = BeautifulSoup(driver.page_source, "html.parser")
        title = soup.find(id='productTitle').text.strip()
        price_text = soup.select('#addToCart span[class*=price]')[0].text
        price = int(re.sub(r'[^0-9]', '', price_text))
        if price < target['limit']:
            results.append({
                'title': title,
                'url': target['url'],
                'price': str(price)
            })
    driver.close()
    return results

if __name__ == '__main__':
    results = fetch_item_data()
    for result in results:
        text = '\n'.join([result['title'], result['url'], '¥' + result['price']])
        create_broad_cast_message(text)
