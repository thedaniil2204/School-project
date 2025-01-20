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
    if message.text.lower() == "начнем рассчет":
        bot.reply_to(message, "Напишите информацию о чеке в формате: cумма в рублях, имя пользователя совершившего покупу, способ разделения долга. Данные должны быть записаны в строчку без запятых через пробел")


# Обработчик текстовых сообщений в процессе



bot.polling(non_stop= True)