import telebot
from dotenv import load_dotenv
import os
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = telebot.TeleBot(token=TELEGRAM_TOKEN)

@bot.message_handler(commands=["start"])
def start (message):
    bot.send_message(message.chat.id, f"Привет {message.from_user.first_name}")

@bot.message_handler(commands=["help"])
def help (message):
    bot.send_message(message.chat.id, "Для того чтобы начать работу с ботом, вам необходио добавить его в чат в качестве администратора")


bot.polling(non_stop= True)