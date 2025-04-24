import sqlite3


# Создание базы данных и таблиц (если они не существуют)
def create_db():
    conn = sqlite3.connect('checks_db.sqlite')
    cursor = conn.cursor()

    # Создаем таблицу с чековыми записями
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS checks (
        check_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        status TEXT NOT NULL
    )''')

    # Создаем таблицу с деталями чеков
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS check_details (
        check_id INTEGER,
        check_name TEXT NOT NULL,
        creator_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        FOREIGN KEY (check_id) REFERENCES checks (check_id)
    )''')

    # Создаем таблицу с пользователями в чековых записях
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS check_users (
        check_id INTEGER,
        user_id INTEGER NOT NULL,
        debt REAL NOT NULL,
        FOREIGN KEY (check_id) REFERENCES checks (check_id)
    )''')

    # Создаем таблицу с сообщениями (если она нужна для получения ID сообщений чека)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS check_messages (
        check_id INTEGER,
        message_id INTEGER NOT NULL,
        FOREIGN KEY (check_id) REFERENCES checks (check_id)
    )''')

    conn.commit()
    conn.close()


# Функции для работы с базой данных

# 1. Добавление нового чека
def add_check(chat_id, status, check_name, creator_id, total_amount):
    conn = sqlite3.connect('checks_db.sqlite')
    cursor = conn.cursor()

    # Добавляем чек в таблицу 'checks'
    cursor.execute('''INSERT INTO checks (chat_id, status) 
                      VALUES (?, ?)''', (chat_id, status))

    # Получаем последний добавленный check_id
    check_id = cursor.lastrowid

    # Добавляем детали чека в таблицу 'check_details'
    cursor.execute('''INSERT INTO check_details (check_id, check_name, creator_id, total_amount) 
                      VALUES (?, ?, ?, ?)''',
                   (check_id, check_name, creator_id, total_amount))

    conn.commit()
    conn.close()

    return check_id


# 2. Добавление пользователей в чек
def add_users_to_check(check_id, users_debts):
    conn = sqlite3.connect('checks_db.sqlite')
    cursor = conn.cursor()

    # Добавляем пользователей в чек
    for user_id, debt in users_debts.items():
        cursor.execute('''INSERT INTO check_users (check_id, user_id, debt) 
                          VALUES (?, ?, ?)''', (check_id, user_id, debt))

    conn.commit()
    conn.close()


# 3. Обновление статуса чека
def update_check_status(check_id, new_status):
    conn = sqlite3.connect('checks_db.sqlite')
    cursor = conn.cursor()

    # Обновляем статус чека
    cursor.execute('''UPDATE checks 
                      SET status = ? 
                      WHERE check_id = ?''', (new_status, check_id))

    conn.commit()
    conn.close()


# 4. Обновление ID сообщения для чека (если нужно)
def update_check_message(check_id, message_id):
    conn = sqlite3.connect('checks_db.sqlite')
    cursor = conn.cursor()

    # Добавляем или обновляем запись о сообщении для чека
    cursor.execute('''INSERT OR REPLACE INTO check_messages (check_id, message_id)
                      VALUES (?, ?)''', (check_id, message_id))

    conn.commit()
    conn.close()


# 5. Получение статуса чека
def get_check_status(check_id):
    conn = sqlite3.connect('checks_db.sqlite')
    cursor = conn.cursor()

    # Получаем статус чека
    cursor.execute('''SELECT status 
                      FROM checks 
                      WHERE check_id = ?''', (check_id,))
    status = cursor.fetchone()

    conn.close()

    if status:
        return status[0]
    else:
        return None


# 6. Получение информации о сообщении чека
def get_check_message(check_id):
    conn = sqlite3.connect('checks_db.sqlite')
    cursor = conn.cursor()

    # Получаем ID сообщения для чека
    cursor.execute('''SELECT message_id 
                      FROM check_messages 
                      WHERE check_id = ?''', (check_id,))
    message_id = cursor.fetchone()

    conn.close()

    if message_id:
        return message_id[0]
    else:
        return None


# 7. Получение информации о текущем чеке
def get_check_info(check_id):
    conn = sqlite3.connect('checks_db.sqlite')
    cursor = conn.cursor()

    # Получаем основные данные о чеке
    cursor.execute('''SELECT check_name, creator_id, total_amount 
                      FROM check_details 
                      WHERE check_id = ?''', (check_id,))
    check_info = cursor.fetchone()

    # Получаем пользователей и их долги
    cursor.execute('''SELECT user_id, debt 
                      FROM check_users 
                      WHERE check_id = ?''', (check_id,))
    users_info = cursor.fetchall()

    conn.close()

    # Формируем результат
    if check_info:
        check_name, creator_id, total_amount = check_info
        users_debts = {user_id: debt for user_id, debt in users_info}
        return {
            "check_name": check_name,
            "creator_id": creator_id,
            "total_amount": total_amount,
            "users_debts": users_debts
        }
    else:
        return None


