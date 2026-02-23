import os
import asyncio
import schedule
from telegram import Bot

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

async def bangun_async():
    await bot.send_message(chat_id=CHAT_ID, text="⏰ Bangun tidur bosku!")

def bangun():
    asyncio.run(bangun_async())

schedule.every().day.at("05:30").do(bangun)

print("Bot jalan...")

while True:
    schedule.run_pending()
    import time
time.sleep(1)


