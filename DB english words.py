import psycopg2
from random import randint

user="postgres"
password="postgres"

# Создаём таблицы в базе данных
def create_db(conn):
    with conn.cursor() as cur:
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS English_words_translate(
                        id SERIAL PRIMARY KEY,
                        russian_word VARCHAR NOT NULL,
                        english_word VARCHAR NOT NULL
                        );
                    """)
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS Other_words(    
                        id INTEGER REFERENCES English_words_translate(id),
                        en_1 VARCHAR NOT NULL,
                        en_2 VARCHAR NOT NULL,
                        en_3 VARCHAR NOT NULL
                        );
                    """)
        cur.execute("""
                    CREATE TABLE IF NOT EXISTS User_info(    
                        id_user INTEGER PRIMARY KEY UNIQUE,
                        set_of_words INTEGER NOT NULL
                        );
                    """)

        conn.commit()

# Заполняем таблицы данными
def add_word(conn):
    with open('words.txt', 'r', encoding='utf-8') as f:
        for line in f:
            english_word = line.strip().split(' ')[0]
            russian_word = line.strip().split('— ')[-1]
            with conn.cursor() as cur:
                cur.execute("""INSERT INTO English_words_translate(russian_word, english_word) VALUES(%s, %s);""",
                           (russian_word, english_word))
                conn.commit()

# Заполняем таблицу слов с неправильным переводом
def add_other_word(conn):
    id = 1
    for i in range(1000):
        en_1 = randint(1, 1000)
        en_2 = randint(1, 1000)
        en_3 = randint(1, 1000)

        with conn.cursor() as cur:
            cur.execute("""INSERT INTO Other_words(id, en_1, en_2, en_3) VALUES(%s, %s, %s, %s);""",
                       (id, en_1, en_2, en_3))
            conn.commit()
        id += 1
# При необходимости удаляем таблицы
def delete_db(conn):
    with conn.cursor() as cur:
        cur.execute("""DROP TABLE Other_words;""")
        cur.execute("""DROP TABLE User_info;""")
        cur.execute("""DROP TABLE English_words_translate;""")
        conn.commit()

if __name__ == "__main__":
    with psycopg2.connect(database="EnglishTranslate", user=user, password=password, host="localhost") as conn:
        # delete_db(conn)
        create_db(conn)
        add_word(conn)
        add_other_word(conn)
    conn.close()
