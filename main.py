import sqlite3
import time
from datetime import datetime
from typing import List, Any, Union
import bittrex
import bot_class
from boto.s3.connection import S3Connection
from os import environ


TOKEN = environ['TOKEN']


orders_db = sqlite3.connect("orders.db")  # orders(uid, status, date_open, date_closed)
messages_db = sqlite3.connect("messages.db")  # messages(id, text, date)
cursor_orders = orders_db.cursor()
cursor_messages = messages_db.cursor()


# cursor_orders.execute("""DELETE FROM orders""")
# orders_db.commit()


# cursor_messages.execute("""CREATE TABLE messages
# (id_msg,text_msg,date_msg)
# """)

def signals_from_fostage(bot, update):
    if bot.from_chat_id(update) == -1001149814828:  # id_chat Forstage team
        msg_text = update['message']['text'].split()
        if 'Покупка' in msg_text[1][1:]:
            pair = msg_text[0].strip('🏎').split('/')
            pair = pair[1] + '-' + pair[0]

            buy = float(msg_text[2][:-1])
            sell = list(map(float, (msg_text[4][:-1], msg_text[6][:-1], msg_text[8][:-1])))
            bot.send_message(bot.get_chat_id(update),
                             '{} купить по {:.8f},\nЦели: {:.8f}, {:.8f}, {:.8f}'.format(pair, buy, *sell))

            if pair in bittrex.all_markets():  # если пара есть на бирже Bittrex
                bot.send_message(bot.get_chat_id(update), 'УРА! Эта пара есть на Биттрекс!')
                buy_order_bittrex_forstage(buy, pair, bot, update)


        else:
            print('Не содержит сигнала')
            bot.send_message(bot.get_chat_id(update), 'Не содержит сигнала')
    else:
        bot.send_message(bot.get_chat_id(update), 'Сообщение не из чата Forsage Team')


# Открытие ордера на Bittrex
def buy_order_bittrex_forstage(buy, pair, bot, update):
    buy = buy / 2  # для отладки цена ордера уменьшина в 2 раза, чтобы ордер не сработал
    # quantity = float(bittrex.balance_btc(
    #     'BTC')) * 0.04 / buy  # 0.04 - ордер на 4% от доступного депозита BTC
    quantity = 0.0005 / buy  # ордер на сумму 0.0005 BTC
    buy_order, text_buy = bittrex.buylimit(pair, buy, quantity)
    print(buy_order)

    # если ордер создан успешно, вносим в базу ордеров
    if buy_order['success']:
        info_order = bittrex.order_info(buy_order['result']['uuid'])
        value_msg: List[Any, Any, Any, Any] = [info_order['result']['OrderUuid'], \
                                               info_order['result']['Exchange'], \
                                               info_order['result']['Opened'], \
                                               info_order['result']['ImmediateOrCancel']]

        cursor_orders.execute(
            """INSERT INTO orders
               VALUES (?,?,?,?)""",
            value_msg
        )
        orders_db.commit()
        bot.send_message(bot.get_chat_id(update),
                         f'{text_buy} ордер на покупку {pair.split("-")[1]} '
                         f'\nпо цене: {buy:.8f}\nколичество: {quantity:.8f} '
                         f'\n{value_msg[0]}')
    else:
        bot.send_message(bot.get_chat_id(update), f"Ордер не создан по причине:\n{buy_order['message']}")

    # отправленеи сообщение в чат о результатах создания ордера


def new_msg(bot_telegram):
    # id последнего письма из базы данных
    cursor_messages.execute("SELECT id_msg FROM messages ORDER BY date_msg DESC LIMIT 1")
    last_id_msg = cursor_messages.fetchone()

    # получение обновлений из чата
    update = bot_telegram.get_updates(offset=last_id_msg, last=True)
    update.update({'Not empty': True})

    if update['update_id'] != last_id_msg[0]:
        # добавление данных нового письма в базу
        value_msg: List[Union[datetime, Any]] = [update['update_id'], update['message']['text'],
                                                 datetime.fromtimestamp(update['message']['date'])]
        cursor_messages.execute(
            """INSERT INTO messages
               VALUES (?,?,?)""",
            value_msg
        )
        messages_db.commit()
    else:
        update = {'message': {'chat': {'id': update['message']['chat']['id']}}, 'Not empty': False}

    return update


def check_order_close(bot, update):
    cursor_orders.execute("SELECT * FROM orders")

    while True:
        uid_order = cursor_orders.fetchone()
        if uid_order:
            uid_order = uid_order[0]

        if uid_order == None:
            break
        order_info = bittrex.order_info(str(uid_order))
        if order_info['result']['Closed']:
            cursor_orders.execute('DELETE FROM orders where uid = ?', (uid_order,))
            orders_db.commit()
            orders_db.execute("VACUUM")
            text_msg = (f"Ордер:\n{order_info['result']['Exchange']}\n"
                        f"на по цене {order_info['result']['Limit']:.8f} BTC\n"
                        f"uid: {uid_order}\nзакрыт в {order_info['result']['Closed']}"
                        f"Оставшееся количество:{order_info['result']['QuantityRemaining']}")
            bot.send_message(bot.get_chat_id(update), text_msg)


# Свой класс исключений
class ScriptError(Exception):
    pass


if __name__ == '__main__':
    while True:
        # экземпляр класса
        bot = bot_class.BotHandler(TOKEN)

        # получаем новое сообщение
        last_msg = new_msg(bot)

        # проверяем последнее письмо на данные из чата Forsage Team
        if last_msg['Not empty']:
            signals_from_fostage(bot, last_msg)

        # проверяем выполнение ордеров
        check_order_close(bot, last_msg)

        print('Новый цикл')
        time.sleep(1)
