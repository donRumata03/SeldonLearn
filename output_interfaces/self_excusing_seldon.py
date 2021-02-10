from seldon_core import *


def answer_with_excuses(target_seldon: Seldon, question: str):
	brain_response = target_seldon.answer(question)

	if brain_response is not None:
		return brain_response[0]

	# TODO: Try to think out some excuses:

	simple_excuses = [
		"Даже не знаю, что тут сказать…",
		"Это печально…",
		"Ничего не понял, но очень интересно!",
		"Мы работаем над этим",
		"Так исторически сложилось"
	]

	return random.choice(simple_excuses)

