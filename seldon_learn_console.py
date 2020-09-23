from typing import *

from seldon_learn import Seldon_learn
from config import *

from vk_api import *

from threading import Timer


class console_api:
    def send_keyboard(self, user_id : int, keys : List[str]):
        print("_______________________________________________________________"
              "\nSuggested options: \t\t\t|" + "|\t\t|".join(keys) + "|\n"
              "_______________________________________________________________")

    def send_message(self, user_id : int, text : str):
        print(text)

seldon = Seldon_learn(console_api(), answer_base_filename, raw_answers_path, bot_filename)

# Mainloop:
def mainloop():
    seldon.process_message(1, input())
    t = Timer(1, mainloop)
    t.start()


if __name__ == '__main__':
    mainloop()

