import telebot
from dotenv import load_dotenv
import os
from telebot.types import Message

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(token=TELEGRAM_TOKEN)

# Словарь для хранения данных о чеках
check_data = {
    "message_id": None,
    "debtors": {}
}

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, f"Привет {message.from_user.first_name}")

@bot.message_handler(commands=["help"])
def help(message):
    bot.send_message(
        message.chat.id,
        "Для того чтобы начать работу с ботом, вам необходимо добавить его в чат в качестве администратора."
    )

user_list = []

@bot.message_handler(commands=['add_users'])
def add_users_handler(message: Message):
    global user_list
    user_list = message.text.split()[1:]
    if user_list:
        response = "Добавлены следующие пользователи:\n" + "\n".join(user_list)
        bot.reply_to(message, response)
    else:
        bot.reply_to(message, "Вы не указали участников.")

@bot.message_handler()
def text(message):
    if message.text.lower() == "начнем":
        bot.reply_to(
            message,
            "Напишите информацию о чеке в формате:\n"
            "сумма в рублях, имя пользователя, совершившего покупку.\n"
            "Данные должны быть записаны в строчку без запятых через пробел."
        )
        bot.register_next_step_handler(message, bill)
    elif "оплатил" in message.text.lower():
        handle_payment(message)

sume = ""

def bill(message):
    global check_data
    global sume
    bill_data = message.text.split()
    try:
        sume = int(bill_data[0])
    except ValueError:
        bot.reply_to(message, "сумма должна быть записана числом")

    name = bill_data[1]
    spisok_message = []
    check_data["debtors"] = {}

    for user in user_list:
        debt = round(int(sume) / len(user_list), 2)
        spisok_message.append(f"{user} должен - {debt}")
        check_data["debtors"][user] = f"должен - {debt}"

    spisok_message = "\n".join(spisok_message)
    sent_message = bot.send_message(
        message.chat.id,
        f"Чек:\n"
        f"Общая сумма: {sume}\n"
        f"Имя покупающего: {name}\n"
        f"Должники:\n{spisok_message}"
    )
    check_data["message_id"] = sent_message.message_id
    bot.pin_chat_message(chat_id=message.chat.id, message_id=sent_message.message_id)

def handle_payment(message):
    global check_data
    username = message.text.split()[0]  # Получаем username из сообщения
    if username in check_data["debtors"]:
        check_data["debtors"][username] = "оплатил"
        updated_message = f"Чек:\nОбшая сумма: {sume}\nДолжники:\n"
        for user, status in check_data["debtors"].items():
            updated_message += f"{user} {status}\n"
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=check_data["message_id"],
            text=updated_message.strip()
        )
    else:
        bot.reply_to(message, "Этот пользователь не найден в списке должников.")

# Запуск бота
if __name__ == '__main__':
    print('Бот запущен!')
    bot.infinity_polling()