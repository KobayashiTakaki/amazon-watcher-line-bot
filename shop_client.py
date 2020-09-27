import os
from datetime import datetime, timezone, timedelta
import time
import re
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

DIRNAME = os.path.dirname(__file__)

class ShopClient:
    def __init__(self):
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('disable-infobars')
        options.add_argument('--disable-extensions')
        self.driver = webdriver.Firefox(options=options)

        f = open(os.path.join(DIRNAME, 'targets.json'))
        self.targets = json.loads(f.read())['targets']
        f.close()

    def fetch_amazon_data(self, url):
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'productTitle'))
        )
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, 'priceblock_ourprice'))
        )
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        title = soup.find(id='productTitle').text.strip()
        price_text = soup.select('#price #priceblock_ourprice_row #priceblock_ourprice')[0].text
        price = int(re.sub(r'[^0-9]', '', price_text))
        return { 'title': title, 'price': price, 'url': url }

    def fetch_rakuten_data(self, url):
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'searchresultitem'))
        )
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        link_elem = soup.select_one('.searchresultitems .searchresultitem .title h2 a')
        title = link_elem.text
        url = link_elem.get('href')
        price_text = soup.select_one('.searchresultitems .searchresultitem .price span').text
        price = int(re.sub(r'[^0-9]', '', price_text))
        return { 'title': title, 'price': price, 'url': url }

    def run(self):
        results_file_path = os.path.join(DIRNAME, 'results.json')
        if not os.path.isfile(results_file_path):
            with open(results_file_path, mode='w') as f:
                pass
        while True:
            results = {}
            with open(results_file_path, mode='r') as f:
                text = f.read()
                results = json.loads(text) if 0 < len(text) else {}
            now = datetime.now(timezone(timedelta(hours=9), 'JST'))
            for target in self.targets:
                if target['id'] in results.keys()\
                   and now - timedelta(hours=3) <\
                   datetime.strptime(results[target['id']]['datetime'], '%Y-%m-%d %H:%M:%S%z'):
                    # 一定時間以内に保存済みだったらスキップ
                    continue
                try:
                    if 'amazon.co.jp' in target['url']:
                        data = self.fetch_amazon_data(target['url'])
                    if 'rakuten.co.jp' in target['url']:
                        data = self.fetch_rakuten_data(target['url'])
                except TimeoutException:
                    print('waiting for page loading timeout.')
                    continue

                if data['price'] < target['limit']:
                    results[target['id']] = {
                        'url': data['url'],
                        'datetime': now.strftime('%Y-%m-%d %H:%M:%S%z'),
                        'title': data['title'],
                        'price': str(data['price'])
                    }
                    with open(results_file_path, mode='w') as f:
                        f.write(json.dumps(results))
                        f.flush()
                elif target['id'] in results.keys():
                    del results[target['id']]
                    with open(results_file_path, mode='w') as f:
                        f.write(json.dumps(results))
                        f.flush()
            time.sleep(1)

if __name__ == '__main__':
    ShopClient().run()
