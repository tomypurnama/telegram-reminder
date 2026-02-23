from telegram import Bot
import schedule
import time
import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

def bangun():
    bot.send_message(chat_id=CHAT_ID, text="⏰ Bangun tidur bosku!")

schedule.every().day.at("08:00").do(bangun)

while True:
    schedule.run_pending()
    time.sleep(1)