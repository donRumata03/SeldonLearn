from abstract_lib.lang_processor import *
from abstract_lib.mylang import *

import config

class Seldon:
    """
    Methods for the user:

    1) __init__(answer_base_filename, raw_answers_filename)
    2) answer(question)
    3) update_answer_base(question, answer)
    4) deserialize()    <- Loads the contents of answer base and raw answer files to memory. Automatically called on init.
    5) serialize()      <- Saves current state of answer base and raw_answers to the corresponding files, recommended to be called once in 20 seconds as it`s performed in the telegram bot

    For further information go to the definitions of the methods below

    """

    answer_base: Dict[str, Set[str]] = {}
    raw_answers: Dict[str, Set[str]] = {}

    answer_filename: str
    raw_answer_filename: str


    def __init__(self, _answer_base_filename : str, _raw_answer_filename : str):
        self.answer_filename = _answer_base_filename
        self.raw_answer_filename = _raw_answer_filename

        self.deserialize()

    ################ Private methods: ################
    def are_fw_similar(self, parsed_question1 : str, parsed_question2 : str) -> bool:
        parsed_words1 = split_words(parsed_question1)
        parsed_words2 = split_words(parsed_question2)

        l1 = len(parsed_words1)
        l2 = len(parsed_words2)
        edge = little_geom_average(l1, l2) / 2.2

        # print("FW edge =", edge)

        return fisher_wagner_distance(parsed_words1, parsed_words2) <= edge

    def get_related_questions(self, parsed_question : str, search_similarities : bool = True) -> List[str]:
        """
        :param parsed_question: the actual question, must be parsed!!!

        :param search_similarities: if this parameter is set to True, than ALL the keys in the dictionary will be compared to the question => O(n)
                                    otherwise this would work during O(1) but EXACT key match is required
        """
        if parsed_question in self.answer_base:
            return [parsed_question]

        if not search_similarities:
            return []


        # Otherwise check all the keys:
        res = []

        for existing_question in self.answer_base:
            if self.are_fw_similar(existing_question, parsed_question):
                res.append(existing_question)

        return res

    # Answering:
    def choose_best_phrase(self, answers : List[str], answer_sources : Dict[str, str], parsed_question : str) -> str:
        if not answers:
            print_red("Empty list of answers given => can`t choose the best!")
            assert answers

        question_popularity = {}

        for answer in answer_sources:
            question = answer_sources[answer]

            if question not in question_popularity:
                question_popularity[question] = 1
            else:
                question_popularity[question] += 1

        print("Question popularity:", question_popularity)

        # use Russian roulette to choose the best idea:
        # So, generate fitnesses:
        fitnesses = []
        for this_answer in answers:
            source = answer_sources[this_answer]
            # print("This answer: \"", this_answer, "\" Source: \"", source, "\"")

            source_len = len(source)
            ans_len = len(this_answer)
            popularity = question_popularity[source] ** 2

            this_fit = source_len ** 2 * ans_len / popularity

            # fw_dist_edge = little_geom_average(this_answer, parsed_question)

            if self.are_fw_similar(parsed_question, source):
                print(f"Found similarity: {parsed_question} and {source}")
                this_fit *= 3

            fitnesses.append(this_fit)

        # TODO: add Fischer wagner distance to fitnesses?

        selected_answer = make_choice(answers, fitnesses)

        return selected_answer


    def get_all_simple_answers_with_sources(self, raw_question : str, search_similarities : bool = True) -> Optional[Tuple[List[str], Dict[str, str]]]:
        normal_question = get_normal_string(raw_question)

        keys = self.get_related_questions(normal_question, search_similarities)

        answers = list()
        answer_sources = {}

        for key in keys:
            for ans in self.answer_base[key]:
                answers.append(ans)
                answer_sources[ans] = key

        for key in keys:
            self.answer_base[key] = set(answers)  # Copy all the answers to each related question

        if not answers:
            return [], {}

        return answers, answer_sources


    def get_simple_answer(self, raw_question : str, search_similarities : bool = True) -> Optional[str]:
        answers, answer_sources = self.get_all_simple_answers_with_sources(raw_question, search_similarities)

        parsed_question = get_normal_string(raw_question)

        if not answers:
            return None

        print("Answers:", answers)
        print("Answer sources:", answer_sources)

        best_phrase = self.choose_best_phrase(answers, answer_sources, parsed_question)
        chosen_question = answer_sources[best_phrase]

        return self.auto_format(parsed_question, chosen_question, best_phrase)

    def is_strict_answer(self, question : str, answer_source : str):
        # print("Strictness determination!")

        q_words = split_words(question)
        source_words = split_words(answer_source)

        q_len = len(q_words)
        source_len = len(source_words)

        return 1.5 >= (q_len * len(question)) / (source_len * len(answer_source)) or source_len >= 5

    def format_answer(self, answer : str, interrogate : bool = False, exclamate : bool = False) -> str:
        # print("Formatting!")

        if not answer:
            return answer

        answer = answer[0].capitalize() + answer[1:]

        if interrogate:
            if not answer[-1].isalnum():
                answer = answer[:-1] + "?"
            else:
                answer += "?"

        if exclamate:
            if not answer[-1].isalnum():
                answer = answer[:-1] + "!"
            else:
                answer += "!"

        return answer

    def format_compound_answer(self, full_question : str, re_question : str, answer : str) -> str:
        splitted = set(filter(bool, (split_words(re_question))))
        if random.random() < 0.5:
            print("Unifying words from real question AND our question!")
            question_words = set(filter(bool, split_words(full_question)))

            splitted = splitted.intersection(question_words)

        re_question = ", ".join(splitted)

        return self.format_answer(re_question, True) + " " + self.format_answer(answer, False, True)
        # TODO: add commas (between re_question words, because it`s the mind stream (sorted words))??) (DONE?)

    def auto_format(self, question : str, answering_question : str, chosen_answer : str) -> str:
        if not self.is_strict_answer(question, answering_question):  # It might be not ideal answer, so, add the chosen question
            answer = self.format_compound_answer(question, answering_question, chosen_answer)
        else:
            answer = self.format_answer(chosen_answer)

        return answer

    def get_all_variation_answers(self, raw_question : str) -> List[str]:
        variations = sorted(list(filter(bool, generate_phrase_variations(raw_question))), key = lambda var: -len(var))

        longest_variation = variations[0]
        longest_variation_length = len(longest_variation.split())  # max([len(variation) for variation in variations])

        print(f"__________________________________________\nThere are {len(variations)} variations of the phrase {raw_question}; longest: {longest_variation_length}!")

        all_raw_answers = []
        answer_sources = {}
        real_answer_sources = {}

        for variation in variations:
            this_answers, this_sources = list(
                self.get_all_simple_answers_with_sources(variation, len(variations) <= 30))
            for ans in this_answers:
                real_answer_sources[ans] = variation
                answer_sources[ans] = this_sources[ans]

            all_raw_answers.extend(this_answers)


        res = []
        for possible_answer in all_raw_answers:
            chosen_question = real_answer_sources[possible_answer]
            res.append(self.auto_format(longest_variation, chosen_question, possible_answer))

        return res


    def get_variation_answer(self, raw_question : str) -> Optional[str]:
        variations = sorted(list(filter(bool, generate_phrase_variations(raw_question))), key = lambda var: -len(var))

        longest_variation = variations[0]
        longest_variation_length = len(longest_variation.split())  # max([len(variation) for variation in variations])

        print(f"__________________________________________\nThere are {len(variations)} variations of the phrase {raw_question}; longest: {longest_variation_length}!")

        if not variations:
            return None

        all_answers = []
        answer_sources = {}
        real_answer_sources = {}


        for variation in variations:
            this_answers, this_sources = list(self.get_all_simple_answers_with_sources(variation, len(variations) <= 30))
            for ans in this_answers:
                real_answer_sources[ans] = variation
                answer_sources[ans] = this_sources[ans]

            all_answers.extend(this_answers)

        if not all_answers:
            return None

        chosen_answer = self.choose_best_phrase(all_answers, answer_sources, longest_variation)
        chosen_question = real_answer_sources[chosen_answer]

        return self.auto_format(longest_variation, chosen_question, chosen_answer)


    # Updating answer base:
    def update_one_pair(self, raw_question : str, answer : str):
        # Updates this particular key:
        if raw_question in self.answer_base:
            self.answer_base[raw_question].add(answer)
        else:
            self.answer_base[raw_question] = {answer}

    def update_question_related_keys(self, raw_question : str, answer : str):
        # Updates this and related questions` answers
        normalized_question = get_normal_string(raw_question)
        related_questions = self.get_related_questions(normalized_question)

        if normalized_question not in related_questions:
            related_questions.append(normalized_question)

        for rel_question in related_questions:
            self.update_one_pair(rel_question, answer)

        # TODO: make recursion?..


    ################ Public methods: ################
    def answer(self, raw_question : str) -> Optional[Tuple[str, bool]]:
        """
        :returns: None if there is no answers available, otherwise: answer and the degree of confidence: boolean (True if sure, False if not sure)
        """
        lower_question = raw_question.lower()

        print(f"Trying to answer question \"{lower_question}\" simply...")

        simple_try = self.get_simple_answer(lower_question)
        if simple_try is not None:
            print("Answered simply!")
            return simple_try, True

        print("Failed to answer simply! Trying out variations...")

        variation_try = self.get_variation_answer(lower_question)

        if variation_try is not None:
            print("Answering through variations!")
            return variation_try, False

        print("Failed to answer anyhow :(")
        return None

    def update_answer_base(self, raw_question : str, answer : str):
        lex_variations = generate_phrase_lexem_variations(raw_question)
        upd_keys = get_updating_keys(lex_variations, self.answer_base)
        for key in upd_keys:
            self.update_question_related_keys(key, answer)
            print("Updating keys similar to: ", key)

    def get_all_possible_answers(self, raw_question : str) -> List[str]:
        # Check both simple and variations: both anyway, even if simple answer(s) exist(s)

        simple_answers, simple_answer_sources = self.get_all_simple_answers_with_sources(raw_question)
        variation_answers = self.get_all_variation_answers(raw_question)

        return simple_answers + variation_answers


    def deserialize(self):
        self.answer_base = from_utf8_json_file(self.answer_filename)
        for k in self.answer_base:
            self.answer_base[k] = set(self.answer_base[k])

        self.raw_answers = from_utf8_json_file(self.raw_answer_filename)
        for k in self.raw_answers:
            self.raw_answers[k] = set(self.raw_answers[k])

    def serialize(self):
        res = {}
        for k in self.answer_base:
            res[k] = list(self.answer_base[k])
        to_utf8_json_file(res, self.answer_filename)

        raw_ans = {}
        for k in self.raw_answers:
            raw_ans[k] = list(self.raw_answers[k])
        to_utf8_json_file(raw_ans, self.raw_answer_filename)





# Tests:
if __name__ == '__main__':
    seldon = Seldon(config.answer_base_filename, config.raw_answers_path)

    err_list = [
        "Привет, Сэлдон!",
        "Привет, Сэлдон, как ты думаешь, что делать с этим?..",
        "Что такое карандаш?.............",
        "Привет, Сэлдон, сколько лет тебе? А сколько штатов в США? А есть у тебя гитара?",
        "Привет, Сэлдон, сколько лет тебе? А сколько таки штатов в США? А есть ли у тебя гитара?",
    ]

    print(seldon.answer(err_list[2]))
    print(seldon.get_all_possible_answers(err_list[1]))

    print(seldon.are_fw_similar("осень такой что", "карандаш такой что"))

    # print(seldon.answer())


