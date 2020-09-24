import telebot
import json
import numpy as np
import random
from abstract_lib.lang_processor import fisher_wagner_distance

key = "1120691185:AAE5yegpxZ6FCTNHywjJ0Kwk46Cx33H_q58"

bot = telebot.TeleBot(key)
keyboard1 = telebot.types.ReplyKeyboardMarkup(True, True)
keyboard1.row('add')




q_buf = ""
idnum = []
flag = []


@bot.message_handler(commands = ['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Hi, i am better seldon')


@bot.message_handler(content_types = ['text'])
def send_text(message):
    global flag
    global q_buf
    global idnum
    idn = -1
    for t in range(0, np.size(idnum)):
        if message.chat.id == idnum[t]:
            idn = t
    if idn == -1:
        idnum.append(message.chat.id)
        flag.append(0)
        idn = np.size(flag) - 1
    print(idnum)
    print(message.text.lower())
    a1 = message.text.lower()
    q = []
    a = []
    min1 = 10000
    minv = 0
    q_now = []
    a_now = []
    with open('question.txt', 'r') as fr:
        q = json.load(fr)
    with open('answers.txt', 'r') as fr:
        a = json.load(fr)
    if flag[idn] == 3 and (message.text.lower() == "ADD" or message.text.lower() == "add") and not (q_buf == ""):
        bot.send_message(message.chat.id, ('And how will you answer?'))
        flag[idn] = 1

    elif message.text.lower() == "show" or message.text.lower() == "SHOW":
        for h in range(0, np.size(q)):
            bot.send_message(message.chat.id, q[h])
            bot.send_message(message.chat.id, a[h])

    elif (flag[idn] == 0 or flag[idn] == 3) and not (message.text.lower() == "ADD" or message.text.lower() == "add"):
        for k in range(0, np.size(q)):
            if fisher_wagner_distance(a1, q[k]) < 2:
                a_now.append(a[k])
                q_now.append(q[k])
        if (np.size(a_now) > 0):
            bot.send_message(message.chat.id, (a_now[int(random.uniform(0, np.size(a_now)) - 0.0001)]), reply_markup = keyboard1)
            q_buf = message.text.lower()
            flag[idn] = 3
        else:
            bot.send_message(message.chat.id, "Not found")
            bot.send_message(message.chat.id, "Write answer")
            flag[idn] = 1
            q_buf = message.text.lower()
    elif flag[idn] == 1:
        q.append(q_buf)
        a.append(message.text.lower())
        with open('question.txt', 'w') as fw:
            json.dump(q, fw)
        with open('answers.txt', 'w') as fw:
            json.dump(a, fw)
            flag[idn] = 0
        bot.send_message(message.chat.id, "Answer added")


bot.polling()
