from typing import Any, List, Dict

from seldon_learn import Seldon_learn
from config import *

import telebot

api = telebot.TeleBot(default_key, threaded = False)

class emulated_telegram_api:
    m_api : telebot.TeleBot

    cached_keyboards : Dict[tuple, Any] = {}

    def __init__(self, _api : telebot.TeleBot):
        self.m_api = _api

    def send_message(self, user_id, message):
        self.m_api.send_message(user_id, message)

    def send_keyboard(self, user_id : int, keys : List[str]):
        if tuple(keys) not in self.cached_keyboards:
            this_kb = telebot.types.ReplyKeyboardMarkup(True, True)
            this_kb.row("add", "show")

            self.cached_keyboards[tuple(keys)] = this_kb


        self.m_api.send_message(user_id, "", reply_markup = self.cached_keyboards[tuple(keys)])


seldon = Seldon_learn(emulated_telegram_api(api), answer_base_filename, raw_answers_path, bot_filename)

@api.message_handler(content_types = ['text'])
def process_message(message):
    seldon.process_message(message.chat.id, message.text)


@api.message_handler(commands = ['start'])
def send_initial_message(message):
    seldon.api.send_message(message.chat.id, 'Hi, I`m the new, better Seldon')

while True:
    try:
        api.polling(none_stop = True)
    except:
        pass
