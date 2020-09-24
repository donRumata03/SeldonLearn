"""
    This is a class for a bot, which is learning by communicating with people.
    It isn`t telegram- or vk- special!
"""
import os
from collections import defaultdict
from datetime import datetime

from abstract_lib.lang_processor import try_counting, stop_words
from seldon_core import Seldon
from typing import *

from abstract_lib.mylang import from_utf8_json_file, to_utf8_json_file

import config

class Seldon_learn:
    brain :  Seldon
    api : Any  # ( Your messenger api type, it should support .send_message(user_id : int, text : str) and send_keyboard(keys : List[str]) )

    user_states: DefaultDict[int, int] = defaultdict(int)
    user_strings: Dict[int, str] = {}

    user_state_filename: str
    last_saving_datetime: datetime = datetime.now()
    changed_something_during_saving_period = False      # IMPORTANT TO UPDATE IT!!!

    def __init__(self, api, answer_base_filename : str, raw_answer_filename : str, user_state_filename : str):
        self.api = api
        self.api_has_keyboard_support = hasattr(api, "send_keyboard")
        self.api_needs_to_be_informed_about_message_end = hasattr(api, "be_informed_about_answer_ending")

        self.brain = Seldon(answer_base_filename, raw_answer_filename)

        self.user_state_filename = user_state_filename
        self.deserialize()

    def process_saving(self):
        now = datetime.now()
        if self.changed_something_during_saving_period and (now - self.last_saving_datetime).total_seconds() > config.saving_period_seconds:
            print("Saving!")
            self.changed_something_during_saving_period = False
            self.last_saving_datetime = now
            self.serialize()

    def show_main_keyboard(self, user_id : int):
        if self.api_has_keyboard_support:
            self.api.send_keyboard(user_id, ["add", "show"])
        else:
            self.api.send_message(user_id, "_______________________________________________________________"
                                           "\nSuggested options: \t\t\t|" + "|\t\t|".join(["add", "show"]) + "|\n"
                                           "_______________________________________________________________")

    def process_message(self, user_id : int, message : str):

        print(f"Got message \"{message}\" from user with id {user_id}")

        count_try = try_counting(message.lower())
        if count_try is not None:
            self.api.send_message(user_id, count_try)

        elif message.lower() in stop_words:
            self.api.send_message(user_id,
                                  f"Хорошо. В переходите в главное меню. Я так понимаю, так и не получится из Вас вытащить ответ на предыдущий вопрос...")
            self.user_states[user_id] = config.USER_STATE_NOTHING

        elif message == "add":
            if user_id not in self.user_strings:
                self.api.send_message(user_id,
                                      f"Простите, но сначала надо отправить сообщение, а потом уже испольщовать команду \"add\"!")
                return

            self.user_states[user_id] = config.USER_STATE_WAITING_ANSWER
            self.api.send_message(user_id, f"Окей. Как бы Вы ответили на вопрос\"{self.user_strings[user_id]}\"?")


        elif message == "show":
            if user_id not in self.user_strings:
                self.api.send_message(user_id,
                                      f"Простите, но сначала надо отправить сообщение, а потом уже испольщовать команду \"show\"!")
                return

            message_data = list(self.brain.get_all_possible_answers(self.user_strings[user_id]))
            for i in range(len(message_data)):
                message_data[i] = "    " + message_data[i] + ("," if i != len(message_data) else "")
            message_str = '\n'.join(message_data)
            self.api.send_message(user_id,
                                  f"Вот разные варианты ответа на вопрос \"{self.user_strings[user_id]}\": \n[\n{message_str}\n]")


        else:  # Some question or answer
            if self.user_states[user_id] == config.USER_STATE_NOTHING:
                # It`s a question => add string and try to answer
                self.user_strings[user_id] = message

                brain_answer = self.brain.answer(message)

                if brain_answer is not None:
                    # We succeed to get the answer!
                    answer = f"Я бы ответил: \"{brain_answer[0]}\"{'' if brain_answer[1] else '. Но я не уверен!'}\n" + \
                    "Возможно, Вы можете предложить ответ получше? (Или просто добавить другой вариант) " + \
                    "Если да, то пишите \"add\""

                    self.api.send_message(user_id, answer)  # reply_markup = self.adding_keyboard)
                    self.show_main_keyboard(user_id)

                else:
                    self.api.send_message(user_id,
                                          "Упс... Кажется, я не могу ответить на Ваш вопрос... Может быть, Вы знаете ответ? Если нет, то пишите \"Стоп\"")
                    self.user_states[user_id] = config.USER_STATE_WAITING_ANSWER

            elif self.user_states[user_id] == config.USER_STATE_WAITING_ANSWER:
                question = self.user_strings[user_id]
                answer = message

                self.brain.update_answer_base(question, answer)
                self.changed_something_during_saving_period = True

                self.api.send_message(user_id,
                                      f"Отлично, Ваш ответ \"{answer}\" на вопрос \"{question}\" записан в базу данных. Он будет учтён при дальнейшем общении.")
                self.user_states[user_id] = config.USER_STATE_NOTHING

        self.process_saving()
        if self.api_needs_to_be_informed_about_message_end:
            self.api.be_informed_about_answer_ending(user_id)



    def serialize(self):
        self.brain.serialize()

        metadata = {
            "user_states": self.user_states,
            "user_strings": self.user_strings
        }
        to_utf8_json_file(metadata, self.user_state_filename)

    def deserialize(self):
        self.brain.deserialize()

        if not os.path.exists(self.user_state_filename):
            return
        metadata = from_utf8_json_file(self.user_state_filename)

        user_states =   { int(i) : metadata["user_states"][i] for i in metadata["user_states"] }
        user_strings =  { int(i) : metadata["user_strings"][i] for i in metadata["user_strings"] }

        self.user_states = defaultdict(int, user_states)
        self.user_strings = user_strings


