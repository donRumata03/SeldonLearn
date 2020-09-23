from lang_processor import get_normal_string
from mylang import *

def convert_to_json(input_name : str = "question.txt", out_name : str = "questions.json"):
    with open(input_name, "r") as j1:
        to_utf8_json_file(json.load(j1), out_name)

def glue_q_ans(question_file : str, answer_file : str, out_file : str):
    res : Dict[str, Set[str]] = {}

    qs = from_utf8_json_file(question_file)
    ans = from_utf8_json_file(answer_file)

    for q, a in zip(qs, ans):
        if q not in res:
            res[q] = {a}
        else:
            res[q].add(a)

    for it in res:
        res[it] = list(res[it])

    to_utf8_json_file(res, out_file)


def normalize_keys(filename : str, function : Callable):
    data = from_utf8_json_file(filename)
    res = {}
    for i in data:
        res[function(i)] = data[i]
    to_utf8_json_file(res, filename)

if __name__ == '__main__':
    # glue_q_ans("questions.json", "answers.json", "initial_answer_base.json")
    normalize_keys("../answer_base.json", get_normal_string)

