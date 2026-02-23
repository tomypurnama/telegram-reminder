import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot reminder siap 👍\nContoh: /ingatkan 10 minum air")

async def ingatkan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        menit = int(context.args[0])
        pesan = " ".join(context.args[1:]) or "Reminder"

        await update.message.reply_text(f"⏳ Oke, aku ingatkan {menit} menit lagi: {pesan}")

        await asyncio.sleep(menit * 60)

        await update.message.reply_text(f"⏰ Reminder: {pesan}")

    except:
        await update.message.reply_text("Format salah.\nContoh: /ingatkan 10 minum air")

async def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ingatkan", ingatkan))

    print("Bot reminder jalan...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(run_bot())
