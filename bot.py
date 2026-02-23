import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot reminder stabil 👍")

async def ingatkan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        menit = int(context.args[0])
        pesan = " ".join(context.args[1:]) or "Reminder"

        await update.message.reply_text(f"⏳ {menit} menit: {pesan}")

        await asyncio.sleep(menit * 60)

        await update.message.reply_text(f"⏰ {pesan}")

    except:
        await update.message.reply_text("Format salah\nContoh: /ingatkan 10 minum air")

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ingatkan", ingatkan))

    print("Bot stabil jalan...")

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
