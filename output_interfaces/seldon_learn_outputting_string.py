from typing import *
from collections import defaultdict

from seldon_learn import Seldon_learn
from config import *

from threading import Timer
from abstract_lib.mylang import *

from output_interfaces.seldon_learn_string_collecting import collecting_api, get_stringy_answer

class console_api:

    def send_keyboard(self, user_id : int, keys : List[str], text : str):
        print(text, "\n")
        print("_______________________________________________________________"
              "\nSuggested options: \t\t\t|" + "|\t\t|".join(keys) + "|\n"
              "_______________________________________________________________")


    def send_message(self, user_id : int, text : str):
        # print(console_color.GREEN, end = "")
        # print(text)
        # print(console_color.END, end = "")
        pass



seldon = Seldon_learn(collecting_api( console_api(), False ), answer_base_filename, raw_answers_path, bot_filename)



# Mainloop:
def mainloop():
    # seldon.process_message(1, input())
    print_good_info(get_stringy_answer(seldon, input()))


    t = Timer(1, mainloop)
    t.start()


if __name__ == '__main__':
    mainloop()

