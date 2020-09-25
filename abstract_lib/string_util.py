from typing import *

def make_stringy_keyboard(options : List[str]):
    return ("_______________________________________________________________"
            "\nSuggested options: \t\t\t|" + "|\t\t|".join(options) + "|\n"
            "_______________________________________________________________")

