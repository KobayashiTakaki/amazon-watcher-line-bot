import os
from datetime import datetime, timezone, timedelta
import time
import re
import configparser
import json
import requests

DIRNAME = os.path.dirname(__file__)

class Notifier:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read(os.path.join(DIRNAME, 'config.ini'))
        self.channel_access_token = config['DEFAULT']['CHANNEL_ACCESS_TOKEN']

    def create_broad_cast_message(self, text):
        url = 'https://api.line.me/v2/bot/message/broadcast'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.channel_access_token)
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

    def run(self):
        results_file_path = os.path.join(DIRNAME, 'results.json')
        histories_file_path = os.path.join(DIRNAME, 'histories.json')
        if not os.path.isfile(histories_file_path):
            with open(histories_file_path, mode='w') as f:
                pass
        while True:
            if not os.path.isfile(results_file_path):
                print('results file does not exists.')
                time.sleep(1)
                continue
            results = {}
            histories = {}
            now = datetime.now(timezone(timedelta(hours=9), 'JST'))
            with open(results_file_path, mode='r') as f:
                text = f.read()
                results = json.loads(text) if 0 < len(text) else {}
            with open(histories_file_path, mode='r') as f:
                text = f.read()
                histories = json.loads(text) if 0 < len(text) else {}
            for key in results.keys():
                if key in histories.keys()\
                   and now - timedelta(hours=3) <\
                   datetime.strptime(histories[key]['datetime'], '%Y-%m-%d %H:%M:%S%z'):
                    # 一定時間以内に通知済みだったらスキップ
                    continue
                histories[key] = {
                    'datetime': now.strftime('%Y-%m-%d %H:%M:%S%z')
                }
                with open(histories_file_path, mode='w') as f:
                    f.write(json.dumps(histories))
                    f.flush()
                text = '\n'.join([results[key]['title'], results[key]['url'], '¥' + results[key]['price']])
                self.create_broad_cast_message(text)
            time.sleep(1)

if __name__ == '__main__':
    Notifier().run()
