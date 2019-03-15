import time
from pprint import pprint

import bittrex
import bot_class
import requests


TOKEN = '739770367:AAFlprJWibNhoZ6Yw-8N4RW-0zsbUeXkGD0'
# имя файла для update_id
log_msg = 'msg_log.txt'  # файл для хранения последнего id сообщения
log_open_buy_order = 'buy_order_log.txt'  # файл для хранения открытых ордеров на покупку

# Свой класс исключений
class ScriptError(Exception):
    pass


# загрузка последнего update_id из файла
def load_last_msg(filename):
    with open(filename) as f:
        last_msg = int(f.readlines()[-1].rstrip())
    return last_msg


# загрузка данных из файла
def load_text(filename):
    text = []
    with open(filename) as f:
        for line in f.readlines():
            text.append(line.rstrip())
    return text


# сохранение новых данных в файл
def save_text(filename, type, *args):
    with open(filename, type) as f:
        f.write(str(*args) + '\n')


# Выставление ордеров по репосту сообщения из чата Forstage team
def signals_from_fostage(update):
    try:

        if bot.from_chat_id(update) == -1001149814828:  # id_chat Forstage team
            msg_text = update['message']['text'].split()
            if 'Покупка' in msg_text[1][1:]:
                pair = msg_text[0].strip('🏎').split('/')
                pair = pair[1] + '-' + pair[0]

                buy_text = msg_text[2][:-1]
                sell_1_text = msg_text[4][:-1]
                sell_2_text = msg_text[6][:-1]
                sell_3_text = msg_text[8][:-1]
                bot.send_message(bot.get_chat_id(update),
                                 f'{pair} купить по {buy_text}, цели: {sell_1_text}, {sell_2_text}, {sell_3_text}')

                buy = float(buy_text)
                sell_1 = float(sell_1_text)
                sell_2 = float(sell_2_text)
                sell_3 = float(sell_3_text)

                if pair in bittrex.all_markets():  # если пара есть на бирже Bittrex
                    bot.send_message(bot.get_chat_id(update), 'УРА! Эта пара есть на Биттрекс!')

                    buy = buy / 2  # для отладки цена ордера уменьшина в 2 раза, чтобы ордер не сработал
                    # quantity = float(bittrex.balance_btc(
                    #     'BTC')) * 0.04 / buy  # 0.04 - ордер на 4% от доступного депозита BTC
                    quantity = 0.0005 / buy  # ордер на сумму 0.0005 BTC
                    buy_order, text_buy = bittrex.buylimit(pair, buy, quantity)

                    if buy_order['success']:
                        print(buy_order['result']['uuid'])
                        save_text(log_open_buy_order, 'a', buy_order['result']['uuid'])  # сохраняем в файл
                    bot.send_message(bot.get_chat_id(update),
                                     f'{text_buy} ордер на покупку {pair.split("-")[1]} '
                                     f'\nпо цене: {buy:.8f}\nколичество: {quantity:.8f} ')

            else:
                # print('Не содержит сигнала')
                bot.send_message(bot.get_chat_id(update), 'Не содержит сигнала')
        else:
            bot.send_message(bot.get_chat_id(update), 'Сообщение не из чата Forsage Team')
    except KeyError:
        print('Сообщение не из чата Forsage Team')


if __name__ == '__main__':



    # экземпляр класса
    bot = bot_class.BotHandler(TOKEN)


    # основной цикл
    while True:

        # try:
        # последнее обновление, offset=<id last message>, last=True - последнее сообщение
        update = bot.get_updates(offset=load_last_msg(log_msg), last=True)
        buy_order_list = load_text(log_open_buy_order)  # список открытых ордеров
        print(buy_order_list)
        # проверка исполения/отмены ордера на покупку

        buy_order_list, closed_order_list = bittrex.del_closed_order(buy_order_list)
        print(buy_order_list, closed_order_list)
        save_text(log_open_buy_order, 'w', *buy_order_list)

        if update['update_id'] == load_last_msg(log_msg):
            pass
        else:
            print('Новое сообщение. Добавляем в базу.')
            save_text(log_msg, update['update_id'])
            signals_from_fostage(update)

        print('Новый цикл')
        time.sleep(1)
        # except Exception as e:
        #     print(e)
