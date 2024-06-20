import random
import telebot
import psycopg2
from telebot import types
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

user = 'postgres'
password = 'postgres'

state_storage = StateMemoryStorage()
token = '*******************'
bot = telebot.TeleBot(token, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []

class Command:
  ADD_WORD = 'Добавить слово'
  DELETE_WORD = 'Удалить слово'
  NEXT = 'Следующее слово'

class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()

@bot.message_handler(commands=['cards', 'start'])
def create_cards(message):
    cid = message.chat.id
    # Заполняем таблицу пользователей уникальными id
    with psycopg2.connect(database="EnglishTranslate", user=user, password=password, host="localhost") as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT id_user FROM User_info;""")
            list_id = cur.fetchall()
            list = []
            for i in list_id:
                list.append(i[0])
            # После первого запуска словарь будет состоять из 50 слов
            if cid not in list:
                cur.execute("""INSERT INTO User_info(id_user, set_of_words) VALUES(%s, %s);""", (cid, 50))
            with conn.cursor() as cur:
                cur.execute("""SELECT set_of_words FROM User_info WHERE id_user=%s;""", (cid,))
                set_of_words = cur.fetchall()[0][0]
        bot.send_message(cid, f"Привет! Я помогу тебе выучить английские слова. Твой словарь будет состоять из {set_of_words} слов. Введи /go в чат")
    conn.close()

# Реализуем функцию перевода и добавления кнопок
@bot.message_handler(commands=['go'])
def words(message):
    cid = message.chat.id
    with psycopg2.connect(database="EnglishTranslate", user=user, password=password, host="localhost") as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT russian_word, english_word FROM English_words_translate;""")
            list_words = cur.fetchall()
            cur.execute("""SELECT set_of_words FROM User_info WHERE id_user=%s;""", (cid, ))
            set_of_words = cur.fetchall()[0][0]
            set_word = random.randint(1, set_of_words)
            target_word = list_words[set_word][0]
            translate_word = list_words[set_word][1]
            cur.execute("""SELECT en_1, en_2, en_3 FROM Other_words;""")
            list_id = cur.fetchall()
            en_1 = str(list_id[set_word][0])
            en_2 = str(list_id[set_word][1])
            en_3 = str(list_id[set_word][2])
            cur.execute("""SELECT english_word FROM English_words_translate WHERE id=%s;""", (en_1,))
            english_1 = cur.fetchall()[0][0]
            cur.execute("""SELECT english_word FROM English_words_translate WHERE id=%s;""", (en_2,))
            english_2 = cur.fetchall()[0][0]
            cur.execute("""SELECT english_word FROM English_words_translate WHERE id=%s;""", (en_3,))
            english_3 = cur.fetchall()[0][0]

        markup = types.ReplyKeyboardMarkup(row_width=2)
        types.KeyboardButton(translate_word)
        buttons.append(translate_word)
        types.KeyboardButton(english_1)
        buttons.append(english_1)
        types.KeyboardButton(english_2)
        buttons.append(english_2)
        types.KeyboardButton(english_3)
        buttons.append(english_3)
        random.shuffle(buttons)

        next_btn = types.KeyboardButton(Command.NEXT)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)

        buttons.extend([next_btn, add_word_btn, delete_word_btn])

        # Реализуем выбор перевода
        markup.add(*buttons)
        greeting = f"Выбери перевод слова:\n🇷🇺 {target_word}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['translate_word'] = translate_word
        data['target_word'] = target_word
        data['english_1'] = english_1
        data['english_2'] = english_2
        data['english_3'] = english_3
    buttons.remove(translate_word)
    buttons.remove(english_1)
    buttons.remove(english_2)
    buttons.remove(english_3)
    buttons.remove(next_btn)
    buttons.remove(add_word_btn)
    buttons.remove(delete_word_btn)

    conn.close()

# Реализуем функцию перехода к следующему слову
@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_word(message):
    words(message)

# Реализуем функцию добавления нового слова
@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    cid = message.chat.id
    with psycopg2.connect(database="EnglishTranslate", user=user, password=password, host="localhost") as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT set_of_words FROM User_info WHERE id_user=%s;""", (cid, ))
            set_of_words = cur.fetchall()[0][0]
            if set_of_words <= 1000:
                set_of_words += 1
                cur.execute("""UPDATE User_info SET set_of_words=%s WHERE id_user=%s;""", (set_of_words, cid))
                conn.commit()
                bot.send_message(message.chat.id, f"Ваш словарь состоит из {set_of_words} слов")
            else:
                bot.send_message(message.chat.id, "У Вас максимальное количество слов")
    conn.close()

# Реализуем функцию удаления слов
@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    cid = message.chat.id
    with psycopg2.connect(database="EnglishTranslate", user=user, password=password, host="localhost") as conn:
        with conn.cursor() as cur:
            cur.execute("""SELECT set_of_words FROM User_info WHERE id_user=%s;""", (cid,))
            set_of_words = cur.fetchall()[0][0]
            if set_of_words > 1:
                set_of_words -= 1
                cur.execute("""UPDATE User_info SET set_of_words=%s WHERE id_user=%s;""", (set_of_words, cid))
                conn.commit()
                bot.send_message(message.chat.id, f"Ваш словарь состоит из {set_of_words} слов")
            else:
                bot.send_message(message.chat.id, "У Вас минимальное количество слов")
    conn.close()

# Реализуем функцию проверки ответа и выбора следующего слова, нового слова и удаления слова
@bot.message_handler(func=lambda message:True, content_types=["text"])
def message_reply(message):
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        translate_word = data['translate_word']
    if message.text == translate_word:
        bot.send_message(message.chat.id, "Правильно!")
        next_word(message)
    elif message.text == Command.NEXT:
        next_word(message)
    elif message.text == Command.ADD_WORD:
        add_word(message)
    elif message.text == Command.DELETE_WORD:
        delete_word(message)
    else:
        bot.send_message(message.chat.id, "Неправильно!")

bot.infinity_polling(skip_pending=True)