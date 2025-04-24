import sqlite3
from contextlib import closing

DB_NAME = "check_db.db"


def _connect():
    # для потоков PyTelegramBotAPI
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def create_db() -> None:
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS checks (
            check_id     INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id      INTEGER,
            status       TEXT,
            buyer_name   TEXT,
            creator_id   INTEGER,
            total_amount REAL,
            is_final     INTEGER DEFAULT 0
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS check_users (
            user_id  TEXT,
            check_id INTEGER,
            debt     REAL,
            status   TEXT,
            PRIMARY KEY (user_id, check_id),
            FOREIGN KEY (check_id) REFERENCES checks (check_id)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS check_messages (
            check_id   INTEGER PRIMARY KEY,
            message_id INTEGER,
            FOREIGN KEY (check_id) REFERENCES checks (check_id)
        )""")
        # если база была создана раньше, пытаемся добавить новые столбцы молча
        try:
            cur.execute("ALTER TABLE checks ADD COLUMN is_final INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass


# ---------- чек ---------- #
def add_check(chat_id: int, buyer_name: str, creator_id: int,
              total_amount: float, is_final: int = 0) -> int:
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""
        INSERT INTO checks (chat_id, status, buyer_name, creator_id,
                            total_amount, is_final)
        VALUES (?, 'открыт', ?, ?, ?, ?)""",
                    (chat_id, buyer_name, creator_id, total_amount, is_final))
        return cur.lastrowid


def close_check_if_paid(check_id: int) -> bool:
    """True, если именно сейчас чек закрылся."""
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""SELECT COUNT(*) FROM check_users
                       WHERE check_id = ? AND status = 'должен'""", (check_id,))
        (left_to_pay,) = cur.fetchone()
        if left_to_pay == 0:
            cur.execute("""UPDATE checks SET status = 'закрыт'
                           WHERE check_id = ?""", (check_id,))
            return True
        return False


def get_check_status(check_id: int) -> str | None:
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT status FROM checks WHERE check_id = ?", (check_id,))
        r = cur.fetchone()
        return r[0] if r else None


def is_final(check_id: int) -> bool:
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("SELECT is_final FROM checks WHERE check_id = ?", (check_id,))
        r = cur.fetchone()
        return bool(r and r[0])


def get_last_open_check_id(chat_id: int) -> int | None:
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""SELECT check_id FROM checks
                       WHERE chat_id = ? AND status != 'закрыт'
                       ORDER BY check_id DESC LIMIT 1""", (chat_id,))
        r = cur.fetchone()
        return r[0] if r else None


def close_all_checks(chat_id: int) -> None:
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""UPDATE checks SET status = 'закрыт'
                       WHERE chat_id = ?""", (chat_id,))


# ---------- пользователи ---------- #
def add_users_to_check(check_id: int, users_debts: dict[str, float]) -> None:
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.executemany("""
        INSERT INTO check_users (user_id, check_id, debt, status)
        VALUES (?, ?, ?, 'должен')""",
                        [(u, check_id, d) for u, d in users_debts.items()])


def update_user_status(check_id: int, user_id: str, new_status: str) -> None:
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""UPDATE check_users SET status = ?
                       WHERE check_id = ? AND user_id = ?""",
                    (new_status, check_id, user_id))


def get_user_record(check_id: int, user_id: str) -> dict | None:
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""SELECT debt, status FROM check_users
                       WHERE check_id = ? AND user_id = ?""",
                    (check_id, user_id))
        r = cur.fetchone()
        if r:
            return {"debt": r[0], "status": r[1]}
        return None


def list_users_for_check(check_id: int) -> list[tuple[str, float, str]]:
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""SELECT user_id, debt, status
                       FROM check_users WHERE check_id = ?""", (check_id,))
        return cur.fetchall()


# ---------- сообщения ---------- #
def save_check_message_id(check_id: int, message_id: int) -> None:
    with closing(_connect()) as conn, conn, closing(conn.cursor()) as cur:
        cur.execute("""INSERT OR REPLACE INTO check_messages
                       (check_id, message_id) VALUES (?, ?)""",
                    (check_id, message_id))


def get_check_message_id(check_id: int) -> int | None:
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""SELECT message_id FROM check_messages
                       WHERE check_id = ?""", (check_id,))
        r = cur.fetchone()
        return r[0] if r else None


# ---------- агрегаты ---------- #
def aggregate_debts(chat_id: int) -> dict[str, float]:
    """Суммы долгов по всем ОТКРЫТЫМ и НЕ финальным чекам чата."""
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""
        SELECT cu.user_id, SUM(cu.debt)
        FROM check_users cu
        JOIN checks c ON c.check_id = cu.check_id
        WHERE c.chat_id = ?
          AND c.status != 'закрыт'
          AND c.is_final = 0
        GROUP BY cu.user_id
        """, (chat_id,))
        return {user: total for user, total in cur.fetchall()}


# ---------- вывод ---------- #
def build_check_text(check_id: int) -> str:
    with closing(_connect()) as conn, closing(conn.cursor()) as cur:
        cur.execute("""SELECT buyer_name, total_amount, status
                       FROM checks WHERE check_id = ?""", (check_id,))
        buyer_name, total_amount, status = cur.fetchone()

    rows = ["✅ ЗАКРЫТ ✅" if status == "закрыт" else "",
            f"Чек #{check_id}",
            f"Общая сумма: {total_amount}",
            f"Покупатель: {buyer_name}",
            "Должники:"]
    for user_id, debt, st in list_users_for_check(check_id):
        suffix = "✅" if st == "оплатил" else ""
        rows.append(f"– {user_id}: {debt} {suffix}")
    return "\n".join([r for r in rows if r])

create_db()

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






