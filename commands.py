import telebot
from dotenv import load_dotenv
import os
import sqlite3
from data_b import create_db, add_check, add_users_to_check, update_check_status, get_check_status, get_check_message, update_check_message, get_users_for_check

# Загружаем токен из .env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(token=TELEGRAM_TOKEN)

# Создание базы данных, если она еще не создана
create_db()

# Обработчик команды /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, f"Привет {message.from_user.first_name}")

# Обработчик команды /help
@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(
        message.chat.id,
        "Для того чтобы начать работу с ботом, вам необходимо добавить его в чат в качестве администратора."
    )

# Обработчик команды /create_check
@bot.message_handler(commands=["create_check"])
def create_check_handler(message):
    bot.reply_to(message, "Введите сумму чека, имя покупателя и список должников через пробел.")
    bot.register_next_step_handler(message, create_check)

# Обработчик для создания чека
def create_check(message):
    bill_data = message.text.split()

    try:
        total_amount = float(bill_data[0])  # Сумма чека
    except ValueError:
        bot.reply_to(message, "Сумма должна быть числом.")
        return

    creator_name = bill_data[1]  # Имя покупателя
    users = bill_data[2:]  # Список должников

    # Создаем чек в БД
    check_id = add_check(message.chat.id, "открыт", "Чек на покупки", message.from_user.id, total_amount)

    # Добавляем пользователей в таблицу check_users и их долги
    users_debts = {user: round(total_amount / len(users), 2) for user in users}
    add_users_to_check(check_id, users_debts)

    # Формируем сообщение о чеке
    spisok_message = []
    for user, debt in users_debts.items():
        spisok_message.append(f"{user} должен - {debt}")

    spisok_message = "\n".join(spisok_message)
    sent_message = bot.send_message(
        message.chat.id,
        f"Чек:\n"
        f"Общая сумма: {total_amount}\n"
        f"Имя покупающего: {creator_name}\n"
        f"Должники:\n{spisok_message}"
    )

    # Запоминаем ID сообщения чека для дальнейших обновлений
    update_check_message(check_id, sent_message.message_id)

    bot.pin_chat_message(chat_id=message.chat.id, message_id=sent_message.message_id)

# Обработчик для команд типа "оплатил"
@bot.message_handler(func=lambda message: "оплатил" in message.text.lower())
def handle_payment(message):
    username = message.text.split()[0]  # Получаем username из сообщения

    # Получаем список пользователей чека из базы данных
    users_for_check = get_users_for_check(username)  # Функция, которая получает всех пользователей для чека

    if users_for_check:
        # Проверяем статус чека в базе данных
        check_id = users_for_check[0]['check_id']  # Извлекаем ID чека из списка пользователей
        check_status = get_check_status(check_id)

        if check_status == "закрыт":
            bot.reply_to(message, "Чек уже закрыт.")
            return

        # Обновляем статус пользователя как оплатившего
        update_check_status(check_id, "оплатил")

        # Получаем обновленную информацию о чеке
        updated_message = get_check_message(check_id)

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=check_id,
            text=updated_message.strip()
        )
        bot.reply_to(message, f"Статус пользователя {username} обновлен.")
    else:
        bot.reply_to(message, "Этот пользователь не найден в списке должников.")

# Запуск бота
if __name__ == '__main__':
    print('Бот запущен!')
    bot.infinity_polling()








