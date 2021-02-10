from typing import *
from collections import defaultdict

from seldon_learn import Seldon_learn
from config import *

from threading import Timer
from abstract_lib.mylang import *



class collecting_api:
    user_data : Dict[int, List[Union[str, List[str]]] ] = defaultdict(list)

    """
    Client api should have the same interface because it`s a wrapper:
    """
    def __init__(self, client_api : Any, output_with_one_string : bool = False):
        assert hasattr(client_api, "send_message")
        self.has_keyboard_support = hasattr(client_api, "send_keyboard")
        self.output_with_one_message = output_with_one_string
        self.client = client_api

    def send_keyboard(self, user_id : int, keys : List[str]):
        self.user_data[user_id].append(keys)

    def send_message(self, user_id : int, text : str):
        self.user_data[user_id].append(text)

    def flush_buffer(self, user_id : int):
        # Freeing the buffer for the user:

        if not self.output_with_one_message:
            # Simply send all messages in sequence:
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

            self.user_data[user_id] = []

        else:  # If it`s required to send only on message:
            resultant_string = ""
            the_keyboard = None

            if self.has_keyboard_support:
                message = self.get_keyboard_with_string_from_buffer(user_id)
                self.client.send_keyboard(user_id, message[1], message[0])
            else:
                resultant_string = self.get_string_from_buffer(user_id)
                self.client.send_message(user_id, resultant_string)




    def get_string_from_buffer(self, user_id) -> str:
        resultant_string = ""

        for object_to_send in self.user_data[user_id]:
            if isinstance(object_to_send, list):
                # Keyboard
                print_red("Warning: can`t send keyboards because can`t convert to strings?")

            elif isinstance(object_to_send, str):
                # Message
                resultant_string += object_to_send + "\n"

        self.user_data[user_id] = []

        return resultant_string.strip()


    def get_keyboard_with_string_from_buffer(self, user_id : int) -> Tuple[str, Optional[List[str]]]:
        resultant_string = ""
        the_keyboard = None

        for object_to_send in self.user_data[user_id]:
            if isinstance(object_to_send, list):
                if the_keyboard is None:
                    the_keyboard = object_to_send
                else:
                    print_red("WARNING: The stream has multiple keyboards! Only the last one is saved!")

            elif isinstance(object_to_send, str):
                # Message
                resultant_string += object_to_send + "\n"

        self.user_data[user_id] = []

        return resultant_string.strip(), the_keyboard


def get_stringy_answer(learning_seldon: Seldon_learn, message: str) -> str:
    assert isinstance(learning_seldon.api, collecting_api)
    learning_seldon.process_message(user_id = 1, message = message)
    return learning_seldon.api.get_string_from_buffer(user_id = 1)
