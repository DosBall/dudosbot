import time
import eventlet
import requests
import logging
from time import sleep
import telepot
import config
import telebot
import random
from telebot import types
token = '1747442287:AAEh8JsjfH_5VTKcc61ObPmH2WXJmh36FDY'
vktoken = '3e9c2b3019a8c2de6cdfe2681c75d8817b9ccc5b45465d3e1ca1647e4b7daee9c081e347db2954ceafdde'
URL_VK = 'https://api.vk.com/method/wall.get?domain=du_dos_bot_group&count=10&filter=owner&access_token=3e9c2b3019a8c2de6cdfe2681c75d8817b9ccc5b45465d3e1ca1647e4b7daee9c081e347db2954ceafdde&v=5.68'
FILENAME_VK = 'lastid.txt'
BASE_POST_URL = 'https://vk.com/du_dos_bot_group?w=wall-205952707_'
CHANNEL_NAME = '@Du_Dos_Bot'

bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def welcome(message):
    stiker = open('stiksas.webp', 'rb')
    bot.send_sticker(message.chat.id, stiker)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("🎲 Рандомное число")
    item2 = types.KeyboardButton("😊 Как дела?")

    markup.add(item1, item2)

    bot.send_message(message.chat.id,
                     "Добро пожаловать, {0.first_name}!\nЯ - <b>{1.first_name}</b>, бот созданный чтобы быть подопытным кроликом.".format(
                         message.from_user, bot.get_me()),
                     parse_mode='html', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def lalala(message):
    if message.chat.type == 'private':
        if message.text == '🎲 Рандомное число от 1 до 100':
            bot.send_message(message.chat.id, str(random.randint(0, 100)))
        elif message.text == 'Как дела? 😊':

            markup = types.InlineKeyboardMarkup(row_width=2)
            item1 = types.InlineKeyboardButton("Хорошо", callback_data='good')
            item2 = types.InlineKeyboardButton("Не очень", callback_data='bad')

            markup.add(item1, item2)

            bot.send_message(message.chat.id, 'Отлично, сам как?', reply_markup=markup)
        else:
            bot.send_message(message.chat.id, 'Я не знаю что ответить')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.message:
            if call.data == 'good':
                bot.send_message(call.message.chat.id, 'Супер😊')
            elif call.data == 'bad':
                bot.send_message(call.message.chat.id, 'Бывает 😢')

            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Как дела?",
                                  reply_markup=None)

    except Exception as e:
        print(repr(e))

def get_data():
    timeout = eventlet.Timeout(10)
    try:
        feed = requests.get(URL_VK)
        return feed.json()
    except eventlet.timeout.Timeout:
        logging.warning('Got Timeout while retrieving VK JSON data. Cancelling...')
        return None
    finally:
        timeout.cancel()
def send_new_posts(items, last_id):
    for item in items:
        if item['id'] <= last_id:
            break
        link = '{!s}{!s}'.format(BASE_POST_URL, item['id'])
        bot.send_message(CHANNEL_NAME, link)

        time.sleep(1)
    return


def check_new_posts_vk():
    logging.info('[VK] Started scanning for new posts')
    with open(FILENAME_VK, 'rt') as file:
        last_id = int(file.read())
        if last_id is None:
            logging.error('Could not read from storage. Skipped iteration.')
            return
        logging.info('Last ID (VK) = {!s}'.format(last_id))
    try:
        feed = get_data()
        if feed is not None:
            entries = feed['response'][1:]
            try:
                tmp = entries[0]['is_pinned']
                send_new_posts(entries[1:], last_id)
            except KeyError:
                send_new_posts(entries, last_id)
            with open(FILENAME_VK, 'wt') as file:
                try:
                    tmp = entries[0]['is_pinned']
                    # Если первый пост - закрепленный, то сохраняем ID второго
                    file.write(str(entries[1]['id']))
                    logging.info('New last_id (VK) is {!s}'.format((entries[1]['id'])))
                except KeyError:
                    file.write(str(entries[0]['id']))
                    logging.info('New last_id (VK) is {!s}'.format((entries[0]['id'])))
    except Exception as ex:
        logging.error('Exception of type {!s} in check_new_post(): {!s}'.format(type(ex).__name__, str(ex)))
        pass
    logging.info('[VK] Finished scanning')
    return

if __name__ == '__main__':
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.basicConfig(format='[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s', level=logging.INFO,
                        filename='bot_log.log', datefmt='%d.%m.%Y %H:%M:%S')
    while True:
        check_new_posts_vk()
        logging.info('[App] Script went to sleep.')
        time.sleep(30)

bot.polling(none_stop=True)