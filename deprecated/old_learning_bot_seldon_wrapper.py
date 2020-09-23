import telebot
from lang_processor import *
from mylang import *

from collections import defaultdict
from datetime import datetime



from config import *


class Seldon_learn:
    answer_base: Dict[str, Set[str]] = {}
    raw_answers: Dict[str, Set[str]] = {}
    user_states: DefaultDict[str, int] = defaultdict(int)
    user_strings: Dict[str, str] = {}

    answer_filename: str
    user_state_filename: str

    last_saving_datetime: datetime = datetime.now()

    def __init__(self, _api, answer_filename: str, user_state_filename: str, raw_answers_filename : str):
        self.api = _api
        self.adding_keyboard = telebot.types.ReplyKeyboardMarkup(True, True)
        self.adding_keyboard.row("add", "show")
        self.user_state_filename = user_state_filename
        self.answer_filename = answer_filename
        self.raw_answer_filename = raw_answers_filename
        self.deserialize()


    def deserialize(self):
        self.answer_base = from_utf8_json_file(self.answer_filename)
        for k in self.answer_base:
            self.answer_base[k] = set(self.answer_base[k])

        self.raw_answers = from_utf8_json_file(self.raw_answer_filename)
        for k in self.raw_answers:
            self.raw_answers[k] = set(self.raw_answers[k])

        if not os.path.exists(self.user_state_filename):
            return
        metadata = from_utf8_json_file(self.user_state_filename)
        self.user_states = defaultdict(int, metadata["user_states"])
        self.user_strings = metadata["user_strings"]


    def serialize(self):
        res = {}
        for k in self.answer_base:
            res[k] = list(self.answer_base[k])
        to_utf8_json_file(res, self.answer_filename)

        raw_ans = {}
        for k in self.raw_answers:
            raw_ans[k] = list(self.raw_answers[k])
        to_utf8_json_file(raw_ans, self.raw_answer_filename)


        metadata = {
            "user_states": self.user_states,
            "user_strings": self.user_strings
        }
        to_utf8_json_file(metadata, self.user_state_filename)

    def get_answer_keys(self, parsed_question: str, search_similarities : bool = True) -> List[str]:
        if not search_similarities:
            if parsed_question in self.answer_base:
                return [parsed_question]
            else:
                return []

        res = []

        if parsed_question in self.answer_base:
            return [parsed_question]

        for existing_question in self.answer_base:
            l1 = len(split_words(parsed_question))
            l2 = len(split_words(existing_question))
            edge = little_geom_average(l1, l2) / 2

            # print(parsed_question, existing_question, l1, l2, edge)

            if fisher_wagner_distance(split_words(existing_question), split_words(parsed_question)) <= edge:
                res.append(existing_question)

        return res

    """
                this_value = len(self.answer_base[existing_question])
                if best_value < this_value:
                    best_key = existing_question
                    best_value = this_value

                elif best_value == this_value:
                    if random.random() < 0.5:
                        best_key = existing_question

        if best_key is not None:
            return best_key
        return None
        """

    def get_answers(self, question: str, search_similarities : bool = True) -> Set[str]:
        """
        parsed_q = get_normal_string(question)  # "".join(normalize_phrase(question))
        for existing_question in self.answer_base:
            if fisher_wagner_distance(existing_question, parsed_q) <= 1:
                self.answer_base[parsed_q] = self.answer_base[existing_question]  # Copy data to an additional question
                # TODO: bind them
                return self.answer_base[existing_question]
        return None
        """
        normal = get_normal_string(question)

        keys = self.get_answer_keys(normal, search_similarities)

        answers = set()

        for key in keys:
            for ans in self.answer_base[key]:
                answers.add(ans)

        for key in keys:
            self.answer_base[key] = answers  # Copy data to an additional question

        return answers

    def get_variation_answer(self, question : str):
        variations = list(filter(bool, generate_phrase_variations(question)))
        print("Variations:", len(variations))



        if not variations:
            return None


        all_answers = []
        answer_sources = {}

        question_popularity = {}

        for variation in variations:
            this_answers = list(self.get_answers(variation, len(variations) <= 30))
            for ans in this_answers:
                answer_sources[ans] = variation
            question_popularity[variation] = len(this_answers)
            all_answers.extend(this_answers)

        print("Possible answer sources:", answer_sources)
        print("Question popularity: ", question_popularity)
        print("All answers: ", all_answers)

        selected_answer = make_choice(all_answers, [len(answer_sources[the_ans]) ** 2 * math.sqrt(len(the_ans)) / question_popularity[answer_sources[the_ans]] ** 2 for the_ans in all_answers])
        if selected_answer is None:
            return None
        ans_source = answer_sources[selected_answer]
        ans_source_len = len(ans_source)
        q_len = len(question)
        if ans_source_len < q_len / 2.5 and len(ans_source.split()) <= 3:
            if ans_source[-1] != "?":
                ans_source = ans_source + "?"
            if str.islower(selected_answer[0]):
                selected_answer = str.capitalize(selected_answer[0]) + selected_answer[1:]
            if str.isalpha(selected_answer[-1]):
                selected_answer = selected_answer + "!"
            selected_answer = "\"" + ans_source + "\" " + selected_answer
        return selected_answer

    def get_random_answer(self, question: str) -> str:
        return random.choice(self.get_answers(question))

    def raw_update_answer_base(self, question : str, answer : str):
        if question in self.answer_base:
            self.answer_base[question].add(answer)
        else:
            self.answer_base[question] = {answer}

    def update_one_answer(self, raw_question: str, answer: str, to_normalize : bool = True):
        normalized_question = get_normal_string(raw_question) if to_normalize else raw_question
        related_questions = self.get_answer_keys(normalized_question)

        related_questions.append(normalized_question)

        self.raw_update_answer_base(normalized_question, answer)
        for rel_question in related_questions:
            self.raw_update_answer_base(rel_question, answer)

    def update_answer_base(self, raw_question: str, answer: str):
        lex_variations = generate_phrase_lexem_variations(raw_question)
        upd_keys = get_updating_keys(lex_variations, self.answer_base)
        for key in upd_keys:
            self.update_one_answer(key, answer, False)
            print("Updating keys similar to: ", key)

    def process_message(self, message):
        text = message.text.lower()
        raw_text = message.text
        user_id = message.chat.id
        str_user_id = str(user_id)
        print(f"Got message \"{text}\" from user with id {str_user_id}")

        count_try = try_counting(text)
        if count_try is not None:
            self.api.send_message(user_id, count_try)

        elif text in stop_words:
            self.api.send_message(user_id, f"Хорошо. В переходите в главное меню. Я так понимаю, так и не получится из Вас вытащить ответ на этот вопрос...")
            self.user_states[str_user_id] = USER_STATE_NOTHING

        elif text == "add":
            if str_user_id not in self.user_strings:
                self.api.send_message(user_id,
                                      f"Простите, но сначала надо отправить сообщение, а потом уже испольщовать эту команду!")
                return

            self.user_states[str_user_id] = USER_STATE_WAITING_ANSWER
            self.api.send_message(user_id, f"Окей. Как бы Вы ответили на вопрос\"{self.user_strings[str_user_id]}\"?")


        elif text == "show":
            if str_user_id not in self.user_strings:
                self.api.send_message(user_id, f"Простите, но сначала надо отправить сообщение, а потом уже испольщовать эту команду!")
                return
            message_data = list(self.get_answers(self.user_strings[str_user_id]))
            for i in range(len(message_data)):
                message_data[i] = "    " + message_data[i] + ("," if i != len(message_data) else "")
            message_str = '\n'.join(message_data)
            self.api.send_message(user_id, f"Вот разные варианты ответа на вопрос \"{self.user_strings[str_user_id]}\": \n[\n{message_str}\n]")


        else:  # Some question or answer
            if self.user_states[str_user_id] == USER_STATE_NOTHING:
                got_answers = list(self.get_answers(question = text))
                self.user_strings[str_user_id] = text

                if got_answers:
                    self.api.send_message(user_id, f"Я бы ответил: \"{random.choice(got_answers)}\"\n"
                                                   "Возможно, Вы можете предложить ответ получше? (Или просто добавить другой вариант)"
                                                   "Если да, то пишите \"add\"", reply_markup = self.adding_keyboard)

                else:
                    # Try other phrase variations:
                    variant_answer = self.get_variation_answer(text)

                    if variant_answer is not None:
                        self.api.send_message(user_id, f"Я бы ответил: \"{variant_answer}\", но я не уверен...\n"
                                                        "Возможно, Вы можете предложить ответ получше? (Или просто добавить другой вариант)\n"
                                                        "Если да, то пишите \"add\"", reply_markup = self.adding_keyboard)

                    else:
                        self.api.send_message(user_id,
                                              f"Упс... Кажется, я не могу ответить на Ваш вопрос... Может быть Вы знаете ответ?")
                        self.user_states[str_user_id] = USER_STATE_WAITING_ANSWER

            elif self.user_states[str_user_id] == USER_STATE_WAITING_ANSWER:
                question = self.user_strings[str_user_id]
                answer = raw_text
                self.update_answer_base(question, answer)
                self.api.send_message(user_id,
                                      f"Отлично, Ваш ответ \"{raw_text}\" на вопрос \"{question}\" записан в базу данных. Он будет учтён при дальнейшем общении.")
                self.user_states[str_user_id] = USER_STATE_NOTHING

        now = datetime.now()
        if (now - self.last_saving_datetime).total_seconds() >= saving_period_seconds:
            self.serialize()
            self.last_saving_datetime = now


api = telebot.TeleBot(default_key, threaded = False)

seldon = Seldon_learn(api, answer_base_filename, bot_filename, raw_answers_path)

print(seldon.get_variation_answer("я пожилой человек?\\"))
print(seldon.get_variation_answer("привет, сэлдон, сколько лет тебе? А сколько штатов в США? А есть у тебя гитара?"))

@api.message_handler(content_types = ['text'])
def process_message(message):
    seldon.process_message(message)


@api.message_handler(commands = ['start'])
def send_initial_message(message):
    seldon.api.send_message(message.chat.id, 'Hi, I`m the new, better Seldon')

api.polling(none_stop = True)

