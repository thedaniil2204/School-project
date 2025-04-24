import os
import re
import time
import logging
from dotenv import load_dotenv
import telebot
import requests

import data_b as db


# ---------- init ---------- #
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
db.create_db()

logging.basicConfig(level=logging.INFO)


# ---------- small helpers ---------- #
PAY_CMD_RE = re.compile(r"\bоплатил\b", re.I)


def parse_payment_command(text: str) -> tuple[int | None, str | None]:
    """
    Возвращает (check_id, username)
      * 'оплатил 3 ivan'  &rarr; (3, 'ivan')
      * 'оплатил ivan'    &rarr; (None, 'ivan')
    """
    tokens = text.strip().split()
    if len(tokens) < 2:
        return None, None
    if tokens[1].lstrip("#").isdigit():
        if len(tokens) < 3:
            return None, None
        return int(tokens[1].lstrip("#")), tokens[2]
    return None, tokens[1]


def safe_edit_message(chat_id: int, message_id: int, text: str) -> None:
    try:
        bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
    except requests.exceptions.RequestException as e:
        logging.error(f"edit_message_text failed: {e}")
        time.sleep(3)
        try:
            bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
        except Exception as e2:
            logging.error(f"retry failed: {e2}")


# ---------- /start  /help ---------- #
@bot.message_handler(commands=["start"])
def cmd_start(m):
    bot.reply_to(m, f"Привет, {m.from_user.first_name}! 👋")


@bot.message_handler(commands=["help"])
def cmd_help(m):
    bot.reply_to(
        m,
        "➊ Добавь бота в групповой чат как администратора.\n"
        "➋ /create_check — создать чек.\n"
        "➌ Оплата: &laquo;оплатил №_чека ник &raquo;  или  &laquo;оплатил ник &raquo; (для последнего чека).\n"
        "➍ &laquo;посчитай все&raquo; — итоговый счёт."
    )


# ---------- /create_check ---------- #
@bot.message_handler(commands=["create_check"])
def cmd_create_check(m):
    bot.reply_to(
        m,
        "Введите: сумма имя_покупателя должник1 должник2 ..."
    )
    bot.register_next_step_handler(m, _create_step)


def _create_step(m):
    parts = m.text.split()
    if len(parts) < 3:
        bot.reply_to(m, "Нужно минимум 3 слова: сумма, покупатель, должники.")
        return
    try:
        total = float(parts[0])
    except ValueError:
        bot.reply_to(m, "Сумма должна быть числом.")
        return

    buyer = parts[1]
    debtors = parts[2:]
    per_person = round(total / len(debtors), 2)
    debts = {u: per_person for u in debtors}

    check_id = db.add_check(m.chat.id, buyer, m.from_user.id, total)
    db.add_users_to_check(check_id, debts)

    text = db.build_check_text(check_id)
    sent = bot.send_message(m.chat.id, text)
    db.save_check_message_id(check_id, sent.message_id)
    bot.pin_chat_message(m.chat.id, sent.message_id)


# ---------- &laquo;посчитай все&raquo; ---------- #
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("посчитай все"))
def calc_all(m):
    totals = db.aggregate_debts(m.chat.id)
    if not totals:
        bot.reply_to(m, "Нет открытых чеков для подсчёта.")
        return

    total_sum = sum(totals.values())
    check_id = db.add_check(m.chat.id, "Сводный", m.from_user.id, total_sum, is_final=1)
    db.add_users_to_check(check_id, totals)

    text = db.build_check_text(check_id)
    sent = bot.send_message(m.chat.id, text)
    db.save_check_message_id(check_id, sent.message_id)
    bot.pin_chat_message(m.chat.id, sent.message_id)

    bot.send_message(
        m.chat.id,
        "Серия чеков завершена. После оплаты сводного счёта начните новую /create_check."
    )


# ---------- оплата ---------- #
@bot.message_handler(func=lambda m: m.text and PAY_CMD_RE.search(m.text))
def handle_payment(m):
    check_id, user = parse_payment_command(m.text)
    if not user:
        bot.reply_to(m, "Формат: &laquo;оплатил №_чека ник &raquo; или &laquo;оплатил ник &raquo;.")
        return

    # определить чек
    if check_id is None:
        check_id = db.get_last_open_check_id(m.chat.id)
        if check_id is None:
            bot.reply_to(m, "Нет открытых чеков в этом чате.")
            return

    # проверить, что пользователь есть в чеке
    rec = db.get_user_record(check_id, user)
    if not rec:
        bot.reply_to(m, f"{user} не найден в чеке #{check_id} или уже оплатил.")
        return

    # обновляем
    db.update_user_status(check_id, user, "оплатил")
    just_closed = db.close_check_if_paid(check_id)

    # редакция сообщения
    msg_id = db.get_check_message_id(check_id)
    if msg_id:
        safe_edit_message(m.chat.id, msg_id, db.build_check_text(check_id))

    # если чек закрылся — открепляем
    if just_closed and msg_id:
        try:
            bot.unpin_chat_message(m.chat.id, msg_id)
        except Exception:
            pass

    # финальный чек &rarr; закрыть ВСЁ
    if just_closed and db.is_final(check_id):
        db.close_all_checks(m.chat.id)
        bot.send_message(m.chat.id, "Все счета закрыты! 🎉")

    bot.reply_to(m, f"{user} отмечен как оплативший.")


# ---------- run ---------- #
if __name__ == "__main__":
    print("Бот запущен 🚀")
    bot.infinity_polling()









