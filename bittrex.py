import requests
import time
import urllib
import hmac, hashlib
from pprint import pprint

API_KEY = 'd912feebbf3e49d78fd81481427ba95d'
# обратите внимание, что добавлена 'b' перед строкой
API_SECRET = b'4f6eb42d10c145b7b43f54f3250674a0'


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
    uri += urllib.parse.urlencode(payload)
    payload = urllib.parse.urlencode(payload)

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
    buylimit_order = call_api(method='/market/buylimit', market=pair, quantity=quantity,rate=buy)
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

def del_closed_order(buy_order_list):
    closed_order_list = []

    for closed_order in order_closed_or_canceled(buy_order_list):
        if closed_order in order_buy_list:
            order_buy_list.remove(closed_order)
            closed_order_list.append(closed_order)

    return buy_order_list, closed_order_list

            # bot.send_message(bot.get_chat_id(update),
                             # f"Отменен/закрыт ордер {closed_order_info['result']['Exchange']}\nпо цене: "
                             # f"{closed_order_info['result']['Limit']:.8f} \nколичество: "
                             # f"{closed_order_info['result']['Quantity']}\n")


def order_closed_or_canceled(order_list):
    closed_list = []

    for order in order_list:

        if order_info(order)['result']['ImmediateOrCancel']:
            closed_list.append(order['uuid'])

        if order_info(order)['result']['Closed']:
            closed_list.append(order)

    return closed_list
