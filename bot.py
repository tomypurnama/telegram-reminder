import os
import asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

# command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot reminder siap 👍\nContoh: /ingatkan 10 minum air")

# command /ingatkan
async def ingatkan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        menit = int(context.args[0])
        pesan = " ".join(context.args[1:]) or "Reminder"

        await update.message.reply_text(f"⏳ Oke, aku ingatkan {menit} menit lagi: {pesan}")

        await asyncio.sleep(menit * 60)

        await update.message.reply_text(f"⏰ Reminder: {pesan}")

    except:
        await update.message.reply_text("Format salah.\nContoh: /ingatkan 10 minum air")

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ingatkan", ingatkan))

    print("Bot reminder jalan...")

    app.run_polling()

if __name__ == "__main__":
    main()
