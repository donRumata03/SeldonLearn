from typing import *
from collections import defaultdict

from seldon_learn import Seldon_learn
from config import *

from threading import Timer
from abstract_lib.mylang import *

class console_api:
    """
    def send_keyboard(self, user_id : int, keys : List[str]):
        print("_______________________________________________________________"
              "\nSuggested options: \t\t\t|" + "|\t\t|".join(keys) + "|\n"
              "_______________________________________________________________")
    """

    def send_message(self, user_id : int, text : str):
        print(console_color.GREEN, end = "")
        print(text)
        print(console_color.END, end = "")


class collecting_api:
    user_data : Dict[int, List[Union[str, List[str]]] ] = defaultdict(list)

    """
    Client api should have the same interface because it`s a wrapper:
    """
    def __init__(self, client_api : Any, output_with_one_string : bool = False):
        assert hasattr(client_api, "send_message")
        self.has_keyboard_support = hasattr(client_api, "send_keyboard")
        self.output_with_one_string = output_with_one_string
        self.client = client_api

    def send_keyboard(self, user_id : int, keys : List[str]):
        self.user_data[user_id].append(keys)

    def send_message(self, user_id : int, text : str):
        self.user_data[user_id].append(text)

    def be_informed_about_answer_ending(self, user_id : int):
        # Freeing the buffer for the user:

        if not self.output_with_one_string:
            for object_to_send in self.user_data[user_id]:
                if isinstance(object_to_send, list):
                    # Keyboard
                    if self.has_keyboard_support:
                        self.client.send_keyboard(user_id, object_to_send)
                elif isinstance(object_to_send, str):
                    # Message
                    self.client.send_message(user_id, object_to_send)
                else:
                    # Unknown type
                    assert False

        else:
            resultant_string = ""
            for object_to_send in self.user_data[user_id]:
                if isinstance(object_to_send, list):
                    # Keyboard
                    print_red("Warning: can`t send keyboards because can`t convert to strings!")
                elif isinstance(object_to_send, str):
                    # Message
                    resultant_string += object_to_send + "\n"

            self.client.send_message(user_id, resultant_string)


        self.user_data[user_id] = []


seldon = Seldon_learn(collecting_api( console_api(), False ), answer_base_filename, raw_answers_path, bot_filename)


# Mainloop:
def mainloop():
    seldon.process_message(1, input())
    t = Timer(1, mainloop)
    t.start()


if __name__ == '__main__':
    mainloop()

