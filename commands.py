import telebot
from dotenv import load_dotenv
import os

from pyexpat.errors import messages

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(token=TELEGRAM_TOKEN)

@bot.message_handler(commands=["start"])
def start (message):
    bot.send_message(message.chat.id, f"Привет {message.from_user.first_name}")

@bot.message_handler(commands=["help"])
def help (message):
    bot.send_message(message.chat.id, "Для того чтобы начать работу с ботом, вам необходио добавить его в чат в качестве администратора")


@bot.message_handler()
def text(message):
    if message.text.lower() == "начнем":
        bot.reply_to(message, "Напишите информацию о чеке в формате: cумма в рублях, имя пользователя совершившего покупу, список должников(через '_'). Данные должны быть записаны в строчку без запятых через пробел")
        bot.register_next_step_handler(message, bill)

def bill(message):
    bill1 = message.text.split()
    bot.reply_to(message, f"получены данные {bill1}")
    sume = bill1[0]
    name = bill1[1]
    spisok = bill1[2].split("_")
    spisok_message = ", ".join(spisok)
    bot.send_message(message.chat.id, f"Чек:\n Общаяя сумма: {sume}\n Имя покупающего: {name}\n Должники: {spisok_message} " )

# нужно привести в порядок сообщения, добавить параметр описание и/или нозвание чека.
# добавить редоктирование списка ботом
# добавить обработку ошибок и исключений


if __name__ == '__main__':
    print('Бот запущен!')
    bot.infinity_polling()