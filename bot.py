import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

reminders = {}
counter = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot reminder siap 👍\n"
        "/ingatkan 10 minum air\n"
        "/ulang 60 berdiri\n"
        "/list"
    )

async def reminder_once(chat_id, reminder_id, delay, pesan, app):
    await asyncio.sleep(delay)
    if reminder_id in reminders:
        await app.bot.send_message(chat_id, f"⏰ {pesan}")
        reminders.pop(reminder_id, None)

async def reminder_repeat(chat_id, reminder_id, delay, pesan, app):
    while reminder_id in reminders:
        await asyncio.sleep(delay)
        await app.bot.send_message(chat_id, f"🔁 {pesan}")

async def ingatkan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global counter
    try:
        menit = int(context.args[0])
        pesan = " ".join(context.args[1:]) or "Reminder"

        reminder_id = counter
        counter += 1

        task = asyncio.create_task(
            reminder_once(update.effective_chat.id, reminder_id, menit * 60, pesan, context.application)
        )

        reminders[reminder_id] = {"task": task, "pesan": pesan, "type": "once"}

        await update.message.reply_text(f"✅ Reminder dibuat ID:{reminder_id}")

    except:
        await update.message.reply_text("Format salah")

async def ulang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global counter
    try:
        menit = int(context.args[0])
        pesan = " ".join(context.args[1:]) or "Repeat"

        reminder_id = counter
        counter += 1

        task = asyncio.create_task(
            reminder_repeat(update.effective_chat.id, reminder_id, menit * 60, pesan, context.application)
        )

        reminders[reminder_id] = {"task": task, "pesan": pesan, "type": "repeat"}

        await update.message.reply_text(f"🔁 Repeat dibuat ID:{reminder_id}")

    except:
        await update.message.reply_text("Format salah")

async def list_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not reminders:
        await update.message.reply_text("Tidak ada reminder aktif")
        return

    teks = "Reminder aktif:\n"
    for rid, data in reminders.items():
        teks += f"ID {rid} — {data['type']} — {data['pesan']}\n"

    await update.message.reply_text(teks)

async def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ingatkan", ingatkan))
    app.add_handler(CommandHandler("ulang", ulang))
    app.add_handler(CommandHandler("list", list_reminder))

    print("Bot reminder jalan...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(run_bot())
