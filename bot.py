import os
import asyncio
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

conn = sqlite3.connect("reminders.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS reminders (
id INTEGER PRIMARY KEY AUTOINCREMENT,
chat_id INTEGER,
delay INTEGER,
pesan TEXT,
repeat INTEGER
)
""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Reminder DB bot siap 👍")

async def schedule_from_db(app):
    rows = cursor.execute("SELECT * FROM reminders").fetchall()

    for rid, chat_id, delay, pesan, repeat in rows:
        asyncio.create_task(reminder_task(rid, chat_id, delay, pesan, repeat, app))

async def reminder_task(rid, chat_id, delay, pesan, repeat, app):
    await asyncio.sleep(delay)

    await app.bot.send_message(chat_id, f"⏰ {pesan}")

    if repeat:
        asyncio.create_task(reminder_task(rid, chat_id, delay, pesan, repeat, app))
    else:
        cursor.execute("DELETE FROM reminders WHERE id=?", (rid,))
        conn.commit()

async def ingatkan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        menit = int(context.args[0])
        pesan = " ".join(context.args[1:]) or "Reminder"

        cursor.execute(
            "INSERT INTO reminders (chat_id, delay, pesan, repeat) VALUES (?, ?, ?, 0)",
            (update.effective_chat.id, menit * 60, pesan)
        )
        conn.commit()

        await update.message.reply_text("✅ Reminder disimpan (DB)")

    except:
        await update.message.reply_text("Format salah")

async def ulang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        menit = int(context.args[0])
        pesan = " ".join(context.args[1:]) or "Repeat"

        cursor.execute(
            "INSERT INTO reminders (chat_id, delay, pesan, repeat) VALUES (?, ?, ?, 1)",
            (update.effective_chat.id, menit * 60, pesan)
        )
        conn.commit()

        await update.message.reply_text("🔁 Repeat disimpan (DB)")

    except:
        await update.message.reply_text("Format salah")

async def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ingatkan", ingatkan))
    app.add_handler(CommandHandler("ulang", ulang))

    print("Bot DB reminder jalan...")

    await app.initialize()
    await app.start()

    await schedule_from_db(app)

    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(run_bot())
