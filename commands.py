import os
import re
import logging
import time
from dotenv import load_dotenv
import telebot
import requests

import data_b as db  # наш модуль для работы с БД

# ---------- Инициализация ---------- #
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

db.create_db()  # гарантируем, что база данных существует

# Настроим логирование
logging.basicConfig(level=logging.ERROR)

# ---------- /start и /help ---------- #
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    bot.reply_to(msg, f"Привет, {msg.from_user.first_name}! 👋")


@bot.message_handler(commands=["help"])
def cmd_help(msg):
    bot.reply_to(
        msg,
        "➊ Добавь бота в групповой чат как администратора.\n"
        "➋ Используй /create_check, чтобы поделить чек.\n"
        "➌ Пиши &laquo;оплатил твой_ник &raquo;, когда перевёл деньги."
    )

# ---------- /create_check ---------- #
@bot.message_handler(commands=["create_check"])
def cmd_create_check(msg):
    bot.reply_to(
        msg,
        "Введите: сумма имя_покупателя должник1 должник2 ..."
    )
    bot.register_next_step_handler(msg, _create_check_step)


def _create_check_step(msg):
    parts = msg.text.split()
    if len(parts) < 3:
        bot.reply_to(msg, "Нужно минимум 3 слова: сумма, покупатель, должники.")
        return

    try:
        total = float(parts[0])
    except ValueError:
        bot.reply_to(msg, "Сумма должна быть числом.")
        return

    buyer = parts[1]
    debtors = parts[2:]
    if not debtors:
        bot.reply_to(msg, "Укажите хотя бы одного должника.")
        return

    per_person = round(total / len(debtors), 2)
    users_debts = {u: per_person for u in debtors}

    check_id = db.add_check(msg.chat.id, "Чек на покупки", msg.from_user.id, total)
    db.add_users_to_check(check_id, users_debts)

    text = db.build_check_text(check_id, buyer, total)
    sent = bot.send_message(msg.chat.id, text)
    db.save_check_message_id(check_id, sent.message_id)
    bot.pin_chat_message(msg.chat.id, sent.message_id)


# ---------- Оплата ---------- #
@bot.message_handler(
    func=lambda m: bool(re.search(r"\bоплатил\b", m.text, flags=re.IGNORECASE))
)
def handle_payment(msg):
    tokens = msg.text.strip().split()
    if len(tokens) < 2:
        bot.reply_to(msg, "Формат: &laquo;оплатил ник &raquo;.")
        return

    user_name = tokens[1]
    record = db.get_user_record(user_name)
    if not record:
        bot.reply_to(msg, "Должник не найден или уже всё оплатил.")
        return

    check_id = record["check_id"]

    # Обновляем пользователя
    db.update_user_status(check_id, user_name, "оплатил")
    db.close_check_if_paid(check_id)

    # Получаем данные для обновления сообщения
    buyer_name = ""  # Можно использовать поле из базы, если нужно
    total_amount = record["debt"] * len(db.list_users_for_check(check_id))
    new_text = db.build_check_text(check_id, buyer_name, total_amount)
    message_id = db.get_check_message_id(check_id)

    if message_id:
        safe_edit_message(msg.chat.id, message_id, new_text)

    bot.reply_to(msg, f"Отлично! {user_name} отмечен как оплативший.")


# ---------- Безопасное редактирование сообщений ---------- #
def safe_edit_message(chat_id, message_id, new_text):
    try:
        bot.edit_message_text(new_text, chat_id=chat_id, message_id=message_id)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to edit message {message_id} in chat {chat_id}: {e}")
        # Можно добавить повторную попытку через несколько секунд
        time.sleep(5)
        try:
            bot.edit_message_text(new_text, chat_id=chat_id, message_id=message_id)
        except requests.exceptions.RequestException as retry_error:
            logging.error(f"Retry failed for message {message_id} in chat {chat_id}: {retry_error}")


# ---------- Запуск ---------- #
if __name__ == "__main__":
    print("Бот запущен 🚀")
    bot.infinity_polling()









