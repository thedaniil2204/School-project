import sqlite3
from contextlib import closing

DB_NAME = "check_db.db"


def _connect():
    # check_same_thread=False — безопасно, потому что каждое соединение своё
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def create_db() -> None:
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS checks (
            check_id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id  INTEGER,
            status   TEXT,
            check_name TEXT,
            creator_id INTEGER,
            total_amount REAL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS check_users (
            user_id TEXT,
            check_id INTEGER,
            debt     REAL,
            status   TEXT,
            PRIMARY KEY (user_id, check_id),
            FOREIGN KEY (check_id) REFERENCES checks (check_id)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS check_messages (
            check_id  INTEGER PRIMARY KEY,
            message_id INTEGER,
            FOREIGN KEY (check_id) REFERENCES checks (check_id)
        )""")


# ---------- Работа с чеками ---------- #
def add_check(chat_id: int, check_name: str, creator_id: int,
              total_amount: float) -> int:
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""INSERT INTO checks (chat_id, status, check_name,
                                           creator_id, total_amount)
                       VALUES (?, 'открыт', ?, ?, ?)""",
                    (chat_id, check_name, creator_id, total_amount))
        return cur.lastrowid


def close_check_if_paid(check_id: int) -> None:
    """Если все пользователи оплатили — ставим чек 'закрыт'."""
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""SELECT COUNT(*) FROM check_users
                       WHERE check_id = ? AND status = 'должен'""",
                    (check_id,))
        (cnt_not_paid,) = cur.fetchone()
        if cnt_not_paid == 0:
            cur.execute("""UPDATE checks SET status = 'закрыт'
                           WHERE check_id = ?""", (check_id,))


def get_check_status(check_id: int) -> str | None:
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT status FROM checks WHERE check_id = ?", (check_id,))
        row = cur.fetchone()
        return row[0] if row else None


# ---------- Пользователи и долги ---------- #
def add_users_to_check(check_id: int, users_debts: dict[str, float]) -> None:
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.executemany("""
            INSERT INTO check_users (user_id, check_id, debt, status)
            VALUES (?, ?, ?, 'должен')""",
                        [(u, check_id, d) for u, d in users_debts.items()])


def update_user_status(check_id: int, user_id: str, new_status: str) -> None:
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""UPDATE check_users
                       SET status = ?
                       WHERE check_id = ? AND user_id = ?""",
                    (new_status, check_id, user_id))


def get_user_record(user_id: str) -> dict | None:
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""SELECT check_id, debt, status
                       FROM check_users
                       WHERE user_id = ? AND status = 'должен'
                       ORDER BY check_id DESC LIMIT 1""",
                    (user_id,))
        row = cur.fetchone()
        if row:
            return {"check_id": row[0], "debt": row[1], "status": row[2]}
        return None


def list_users_for_check(check_id: int) -> list[tuple[str, float, str]]:
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""SELECT user_id, debt, status
                       FROM check_users
                       WHERE check_id = ?""", (check_id,))
        return cur.fetchall()


# ---------- Сообщения ---------- #
def save_check_message_id(check_id: int, message_id: int) -> None:
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""INSERT OR REPLACE INTO check_messages (check_id, message_id)
                       VALUES (?, ?)""", (check_id, message_id))


def get_check_message_id(check_id: int) -> int | None:
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""SELECT message_id FROM check_messages
                       WHERE check_id = ?""", (check_id,))
        row = cur.fetchone()
        return row[0] if row else None


# ---------- Вспомогательное ---------- #
def build_check_text(check_id: int, buyer_name: str,
                     total_amount: float) -> str:
    """Собирает актуальный текст сообщения о чеке."""
    parts = [
        f"Чек #{check_id}",
        f"Общая сумма: {total_amount}",
        f"Покупатель: {buyer_name}",
        "Должники:"
    ]
    for user_id, debt, status in list_users_for_check(check_id):
        suffix = "✅" if status == "оплатил" else ""
        parts.append(f"– {user_id}: {debt} {suffix}")
    return "\n".join(parts)



# def clear_test_data():
#     conn = sqlite3.connect('check_db.sqlite')
#     cursor = conn.cursor()
#
#     # Удаляем все записи из всех таблиц
#     cursor.execute('DELETE FROM check_users')
#     cursor.execute('DELETE FROM check_messages')
#     cursor.execute('DELETE FROM checks')
#
#     conn.commit()
#     conn.close()

# Вызови эту функцию для очистки данных
# clear_test_data()


create_db()



