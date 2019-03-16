import hashlib
import hmac
import time
import urllib

import requests

API_KEY = ''
# обратите внимание, что добавлена 'b' перед строкой
API_SECRET = b''

API_URL = 'bittrex.com'
API_VERSION = 'v1.1'
SECURE = True


# все обращения к API проходят через эту функцию
def call_api(**kwargs):
    http_method = kwargs.get('http_method') if kwargs.get('http_method', '') else 'GET'
    method = kwargs.get('method')

    nonce = str(int(round(time.time())))
    payload = {
        'nonce': nonce
    }

    if kwargs:
        payload.update(kwargs)

    uri = "https://" + API_URL + "/api/" + API_VERSION + method + '?apikey=' + API_KEY + '&nonce=' + nonce
    payload = urllib.parse.urlencode(payload)
    uri += payload


    apisign = hmac.new(API_SECRET,
                       uri.encode(),
                       hashlib.sha512).hexdigest()

    headers = {"Content-type": "application/x-www-form-urlencoded",
               "Key": API_KEY,
               "apisign": apisign}

    res = requests.request(
        method=http_method,
        url=uri,
        params=payload if http_method == 'POST' else [],
        headers=headers,
        verify=SECURE
    ).json()
    return res


def all_markets():
    all_markets_list = []
    all_markets = call_api(method='/public/getmarkets')
    for pair_name in all_markets['result']:
        all_markets_list.append(pair_name['MarketName'])
    return all_markets_list


def buylimit(pair, buy, quantity):
    buylimit_order = call_api(method='/market/buylimit', market=pair, quantity=quantity, rate=buy)
    if buylimit_order['success']:
        text = 'СОЗДАН'
    else:
        text = f"{buylimit_order['message']}\nНЕ СОЗДАН"
    print(buylimit_order)
    return buylimit_order, text


def balance_btc(name_coin):
    coin = name_coin
    balance = call_api(method='/account/getbalance', currency=coin)
    return balance['result']['Available']


def order_info(uuid):
    order_info = call_api(method="/account/getorder", uuid=uuid)
    return order_info
