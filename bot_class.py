import requests
import datetime
from pprint import pprint


class BotHandler:

    def __init__(self, token):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)

    def get_updates(self, offset=None, timeout=150, last=False):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params, proxies={"https": '116.203.3.82:1994'})
        result_json = resp.json()['result']
        if last:
            result_json = result_json[-1]
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params, proxies={"https": '116.203.3.82:1994'})
        return resp

    def from_chat_id(self, response):
        return response['message']['forward_from_chat']['id']

    def get_chat_id(self, update):
        chat_id = update['message']['chat']['id']
        return chat_id

