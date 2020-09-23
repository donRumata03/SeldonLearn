import random

import numpy as np
import pymorphy2
from typing import *

from mylang import split_words, split_lexems, geom_average, little_geom_average, split_if

from itertools import combinations


morph = pymorphy2.MorphAnalyzer()

def lemmatize_words(words : List[str]) -> List[str]:
    return [morph.parse(word)[0].normal_form for word in words]

def fisher_wagner_distance(seq1, seq2):
    size_x = len(seq1) + 1
    size_y = len(seq2) + 1
    matrix = np.zeros((size_x, size_y))
    for x in range(size_x):
        matrix[x, 0] = x
    for y in range(size_y):
        matrix[0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq1[x - 1] == seq2[y - 1]:
                matrix[x, y] = min(
                    matrix[x - 1, y] + 1,
                    matrix[x - 1, y - 1],
                    matrix[x, y - 1] + 1)
            else:
                matrix[x, y] = min(
                    matrix[x - 1, y] + 1,
                    matrix[x - 1, y - 1] + 1,
                    matrix[x, y - 1] + 1)
    return matrix[size_x - 1, size_y - 1]

def brute_normalize(phrase : str):
    return list(filter(lambda x: len(x) >= 2, sorted(lemmatize_words(split_words(phrase)))))

def normalize_phrase(phrase : str) -> List[str]:
    lexems = split_lexems(phrase)
    res = []
    for lex in lexems:
        res.append(" ".join(brute_normalize(lex)))
    return res


def count_char_sum(sentence : List[str]) -> int:
    return sum([sum([ord(c) - ord("А") for c in word]) for word in sentence])


def generate_phrase_lexem_variations(phrase : str) -> List[Tuple[str]]:
    lexems = split_lexems(phrase)

    variations = []
    for l in range(1, len(lexems) + 1):
        for i in combinations(lexems, l):
            variations.append(i)
    variations = variations[::-1]

    res_set = set()

    for i in range(len(variations)):
        this_res = []
        for lexem in variations[i]:
            this_res.append(" ".join(brute_normalize(lexem)))  # sorted(list(variations[i])) # key = count_char_sum)
        this_res.sort(key = count_char_sum)
        res_set.add(tuple(this_res))
        # this_res.sort(key = lambda s: count_char_sum(s) / len(s))
        # res_set.add(tuple(this_res))

    res = list(res_set)
    res.sort(key = lambda s: -len(s) - 0.0001 * sum([len(ss) for ss in s]))

    return res

def generate_phrase_variations(phrase : str) -> List[str]:
    tuples = generate_phrase_lexem_variations(phrase)
    end_res = [" ".join(i) for i in tuples]
    return end_res

def get_updating_keys(lexem_variations : List[Tuple[str]], answer_base):
    res = set()
    # max_lex_size = max([max([len(w.split()) for w in [lex for lex in lexem_variations])])
    max_lex_size = max([max([len(w.split()) for w in lex]) for lex in lexem_variations])

    for variation in lexem_variations:
        if len(variation) > 1:
            res.add(" ".join(variation))
        elif len(variation) == 1:
            lexem = variation[0]
            words = lexem.split()
            if len(words) >= 3:
                res.add(lexem)
            elif max_lex_size <= 2:
                res.add(lexem)
            elif len(words) == 2 and lexem not in answer_base:
                if random.random() >= 0.5:
                    res.add(lexem)

    return res


def make_choice(values : list, fitnesses : List[float]):
    assert values

    russian_roulette_map = []

    def make_res_choice(val):
        r: int = len(russian_roulette_map)
        l: float = -1
        while r != l + 1:
            mid = int((r + l) / 2)
            if val > russian_roulette_map[mid][1]:
                l = mid
            else:
                r = mid
        return r if r < len(russian_roulette_map) else l

    norm_coeff = sum(fitnesses)
    map_pointer = 0

    # print("_________________________________")
    # print("Values: ", values)
    # print("Fits: ", fitnesses)
    # print("_________________________________")


    for index in range(len(values)):
        this_prob = fitnesses[index] / norm_coeff
        russian_roulette_map.append((map_pointer, map_pointer + this_prob))
        map_pointer += this_prob

    return values[make_res_choice(random.random())]


def get_normal_string(phrase : str) -> str:
    return " ".join(sorted(normalize_phrase(phrase), key = count_char_sum))

def is_ariphmetic_equation(string : str) -> bool:
    words = list(filter(bool, split_if(string, lambda x: not str.isalpha(x))))

    allowed_words = {
        "sqrt",
        "sin",
        "cos",

        "max",
        "min",

        "abs",
        "log",
        "ln",
        "exp",

        "pi",
        "e"
    }

    for words in words:
        if words not in allowed_words:
            return False

    """
    for c in list(string):
        if c.isalpha():
            return False
    """

    return True

def try_counting(string : str) -> Optional[float]:
    if not is_ariphmetic_equation(string):
        return None

    try:
        exec(f"from math import*\nres = {string}")
        return locals()["res"]
    except:
        return None


stop_words = \
    {
        "стоп",
        "стой",
        "отмена",
        "отменить",
        "главное меню",
        "назад",
    }


def some_test():
    test_words = ['грустно', 'зависимость', 'хорошему', 'приводит', 'альтернатив']

    print(lemmatize_words(test_words))

    test_phrase = "Привет, Сэлдон! Как ты думаешь, сколько стоят 10 килограмм гречи?"


    print(generate_phrase_variations(test_phrase))

    print(fisher_wagner_distance(
        [1, 3, 4],
        [1, 3, 5]
    ))

    exec("a = 10 * 100 + (100 + 8)")

    print(a)

def test_else():
    test_phrase = "Привет, Сэлдон! Как ты думаешь, сколько стоят 10 килограмм гречи?"
    print(generate_phrase_variations(test_phrase))

    print(little_geom_average(5, 3))

    print(try_counting("rm -rf"))
    print(try_counting("10 + (1 * 7 - 9)"))
    print(try_counting("10 + (1 * 7 - 9"))
    print(try_counting("sqrt(100)"))

    print(count_char_sum(["ё"]))

def fit_choosing_test():
    values = ['приветсвую тебя несовершенный биологический организм', 'я родился!', 'Приве́тствие — жест, слово, словосочетание, письменное послание (и их совмещение) или иной ритуал для вступления в контакт человека (группы людей) с другим человеком (с группой людей).', 'как тебя зовут?', 'как дела?', 'что такое осень?', 'привет, человек', 'привет']
    fits = [29.25, 5.625, 103.5, 8.4375, 5.0625, 9.0, 8.4375, 3.375]

    res = {}

    for i in range(1000):
        c = make_choice(values, fits)
        if c not in res:
            res[c] = 1
        else:
            res[c] += 1

    print(res)


if __name__ == '__main__':

    fit_choosing_test()
    print(make_choice(["Hello!", "HI!"], [-100000000, -1]))

    exit()


    ph1 = "Сэлдон, как ты думаешь, что было раньше, курица или яйцо?"
    ph2 = "Сэлдон, в каком году родился Пушкин?"
    ph3 = "Сэлдон, Привет!"

    rw = generate_phrase_lexem_variations(ph1)
    print(rw)

    prev_dict = {
        "Сэлдон",
        "Привет",
        "Как дела?"
    }

    for i in get_updating_keys(rw, prev_dict):
        print(i)





