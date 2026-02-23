import os
import re
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from db import *
from reminder import add_reminder
from cashflow import add_tx, get_summary

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot Life aktif 🚀")

async def ingatkan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    m = re.match(r"(\d+)\s+(.*)", text)
    if not m:
        await update.message.reply_text("Format: /ingatkan 10 minum air")
        return

    sec = int(m.group(1))
    msg = m.group(2)

    add_reminder(update.effective_user.id, msg, sec)
    await update.message.reply_text("Reminder disimpan ✅")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.lower()
    m = re.match(r"(in|out)\s+([\d\.]+)\s+(idr|thb)\s*(.*)", txt)
    if not m:
        return

    ttype = m.group(1)
    amount = float(m.group(2).replace(".", ""))
    cur = m.group(3).upper()
    note = m.group(4)

    add_tx(update.effective_user.id, ttype, amount, cur, note)
    await update.message.reply_text("Disimpan ✅")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_summary(update.effective_user.id)

    msg = "📊 Summary\n\n"
    for c, v in data:
        msg += f"{c}: {int(v):,}\n"

    await update.message.reply_text(msg)

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ingatkan", ingatkan))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(MessageHandler(filters.TEXT, text_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
