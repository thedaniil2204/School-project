import sqlite3


# Функция для подключения к базе данных и создания таблиц
def create_db():
    # Подключаемся к базе данных (если файл базы не существует, он будет создан)
    conn = sqlite3.connect('checks_db.sqlite')
    cursor = conn.cursor()

    # Создание таблицы чеков
    cursor.execute('''CREATE TABLE IF NOT EXISTS checks (
                        check_id INTEGER PRIMARY KEY,
                        chat_id INTEGER,
                        status TEXT
                    )''')

    # Создание таблицы с деталями чека
    cursor.execute('''CREATE TABLE IF NOT EXISTS check_details (
                        check_id INTEGER,
                        check_name TEXT,
                        creator_id INTEGER,
                        total_amount REAL,
                        FOREIGN KEY (check_id) REFERENCES checks (check_id)
                    )''')

    # Создание таблицы пользователей в чеке
    cursor.execute('''CREATE TABLE IF NOT EXISTS check_users (
                        check_id INTEGER,
                        user_id INTEGER,
                        debt REAL,
                        FOREIGN KEY (check_id) REFERENCES checks (check_id)
                    )''')

    # Подтверждаем изменения и закрываем соединение
    conn.commit()
    conn.close()

# Вызываем функцию для создания базы данных
create_db()