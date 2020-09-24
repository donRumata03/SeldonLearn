import os
import pathlib

default_key = "1120691185:AAE5yegpxZ6FCTNHywjJ0Kwk46Cx33H_q58"

test_key = "1236607694:AAFfCstUzctVY0CnAA3pNNNHwPoC97VeuJs"  # For test bot :)

saving_period_seconds = 20

root_path = pathlib.Path(__file__).parent.absolute()  # "D:/Projects/Seldon/"

print("Root path: ", root_path)

answer_base_filename = os.path.join(root_path, "data/answer_base.json")
bot_filename = os.path.join(root_path, "data/bot_user_states.json")
raw_answers_path = os.path.join(root_path, "data/raw_answers.json")

USER_STATE_NOTHING = 0
USER_STATE_WAITING_ANSWER = 1

