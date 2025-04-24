import sqlite3

# Функция для создания базы данных и таблиц
def create_db():
    conn = sqlite3.connect('check_db.db')  # Имя базы данных
    cursor = conn.cursor()

    # Создание таблицы для чеков
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS checks (
        check_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        status TEXT,
        check_name TEXT,
        creator_id INTEGER,
        total_amount REAL
    )''')

    # Создание таблицы для пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS check_users (
        user_id TEXT,
        check_id INTEGER,
        debt REAL,
        status TEXT,
        PRIMARY KEY (user_id, check_id),
        FOREIGN KEY (check_id) REFERENCES checks (check_id)
    )''')

    # Создание таблицы для сообщений чеков
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS check_messages (
        check_id INTEGER PRIMARY KEY,
        message_id INTEGER,
        FOREIGN KEY (check_id) REFERENCES checks (check_id)
    )''')

    conn.commit()
    conn.close()

# Функция для добавления чека в базу данных
def add_check(chat_id, status, check_name, creator_id, total_amount):
    conn = sqlite3.connect('check_db.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO checks (chat_id, status, check_name, creator_id, total_amount)
    VALUES (?, ?, ?, ?, ?)''', (chat_id, status, check_name, creator_id, total_amount))
    conn.commit()
    check_id = cursor.lastrowid
    conn.close()
    return check_id

# Функция для добавления пользователей в чек
def add_users_to_check(check_id, users_debts):
    conn = sqlite3.connect('check_db.db')
    cursor = conn.cursor()
    for user_id, debt in users_debts.items():
        cursor.execute('''
        INSERT INTO check_users (user_id, check_id, debt, status)
        VALUES (?, ?, ?, ?)''', (user_id, check_id, debt, "должен"))
    conn.commit()
    conn.close()

# Функция для обновления статуса чека
def update_check_status(check_id, status):
    conn = sqlite3.connect('check_db.db')
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE checks
    SET status = ?
    WHERE check_id = ?''', (status, check_id))
    conn.commit()
    conn.close()

# Функция для получения статуса чека
def get_check_status(check_id):
    conn = sqlite3.connect('check_db.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT status FROM checks
    WHERE check_id = ?''', (check_id,))
    status = cursor.fetchone()
    conn.close()
    return status[0] if status else None

# Функция для получения сообщения чека
def get_check_message(check_id):
    conn = sqlite3.connect('check_db.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT message_id FROM check_messages
    WHERE check_id = ?''', (check_id,))
    message_id = cursor.fetchone()
    conn.close()
    return f"Чек #{check_id} с ID сообщения: {message_id[0]}" if message_id else "Сообщение не найдено."

# Функция для обновления ID сообщения чека
def update_check_message(check_id, message_id):
    conn = sqlite3.connect('check_db.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT OR REPLACE INTO check_messages (check_id, message_id)
    VALUES (?, ?)''', (check_id, message_id))
    conn.commit()
    conn.close()

# Функция для получения пользователей по чеку
def get_users_for_check(username):
    conn = sqlite3.connect('check_db.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT check_id, user_id, debt
    FROM check_users
    WHERE user_id = ?''', (username,))
    users = cursor.fetchall()
    conn.close()
    return [{'check_id': user[0], 'user_id': user[1], 'debt': user[2]} for user in users]



# def clear_test_data():
#     conn = sqlite3.connect('checks_db.sqlite')
#     cursor = conn.cursor()
#
#     # Удаляем все записи из всех таблиц
#     cursor.execute('DELETE FROM check_users')
#     cursor.execute('DELETE FROM check_details')
#     cursor.execute('DELETE FROM check_messages')
#     cursor.execute('DELETE FROM checks')
#
#     conn.commit()
#     conn.close()
#
# # Вызови эту функцию для очистки данных
# clear_test_data()


create_db()



