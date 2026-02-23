import os
import asyncio
import sqlite3
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")
DB = "data.db"
KURS_THB_IDR = 450

# ================= DB =================

conn = sqlite3.connect(DB, check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS trx(
id INTEGER PRIMARY KEY AUTOINCREMENT,
tipe TEXT,
jumlah REAL,
currency TEXT,
note TEXT,
created TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS reminder(
id INTEGER PRIMARY KEY AUTOINCREMENT,
chat_id TEXT,
text TEXT,
waktu TEXT,
repeat TEXT
)
""")

conn.commit()

# ================= UTILS =================

def clean_number(text: str):
    text = text.replace(".", "").replace(",", "")
    return float(text)

def parse_money(args):
    jumlah = clean_number(args[0])

    currency = "THB"
    start_note = 1

    if len(args) > 1 and args[1].lower() in ["idr","thb"]:
        currency = args[1].upper()
        start_note = 2

    note = " ".join(args[start_note:]) or "trx"
    return jumlah, currency, note

def save_trx(tipe, jumlah, currency, note):
    c.execute(
        "INSERT INTO trx(tipe,jumlah,currency,note,created) VALUES(?,?,?,?,?)",
        (tipe, jumlah, currency, note, datetime.now().isoformat())
    )
    conn.commit()

# ================= CASHFLOW =================

async def in_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah, currency, note = parse_money(context.args)
        save_trx("in", jumlah, currency, note)
        await update.message.reply_text(f"➕ {jumlah:,.0f} {currency} disimpan")
    except:
        await update.message.reply_text("Format salah\n/in 10000 thb gaji")

async def out_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah, currency, note = parse_money(context.args)
        save_trx("out", jumlah, currency, note)
        await update.message.reply_text(f"➖ {jumlah:,.0f} {currency} disimpan")
    except:
        await update.message.reply_text("Format salah\n/out 200 thb makan")

# ================= SUMMARY =================

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = c.execute("SELECT tipe,jumlah,currency FROM trx").fetchall()

    idr = 0
    thb = 0

    for t,j,curr in rows:
        val = j if t == "in" else -j
        if curr == "IDR":
            idr += val
        else:
            thb += val

    eq = idr + thb * KURS_THB_IDR

    await update.message.reply_text(
        f"📊 Summary\n\n"
        f"IDR: {idr:,.0f}\n"
        f"THB: {thb:,.0f}\n"
        f"EQ IDR: {eq:,.0f}"
    )

# ================= INSIGHT =================

async def insight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = c.execute("SELECT tipe,jumlah,currency FROM trx WHERE tipe='out'").fetchall()

    total_idr = sum(j for t,j,c in rows if c=="IDR")
    total_thb = sum(j for t,j,c in rows if c=="THB")

    text = "🧠 Insight\n\n"

    if total_idr > 5_000_000:
        text += "⚠️ Pengeluaran IDR besar\n"

    if total_thb > 10_000:
        text += "⚠️ Pengeluaran THB besar\n"

    if text == "🧠 Insight\n\n":
        text += "Aman 👍"

    await update.message.reply_text(text)

# ================= REMINDER =================

async def ingatkan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        menit = int(context.args[0])
        text = " ".join(context.args[1:]) or "Reminder"

        waktu = datetime.now() + timedelta(minutes=menit)

        c.execute(
            "INSERT INTO reminder(chat_id,text,waktu,repeat) VALUES(?,?,?,?)",
            (str(update.effective_chat.id), text, waktu.isoformat(), "once")
        )
        conn.commit()

        await update.message.reply_text("✅ Reminder disimpan")
    except:
        await update.message.reply_text("Format salah\n/ingatkan 10 minum")

async def ingatkan_harian(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jam = context.args[0]
        text = " ".join(context.args[1:]) or "Reminder"

        c.execute(
            "INSERT INTO reminder(chat_id,text,waktu,repeat) VALUES(?,?,?,?)",
            (str(update.effective_chat.id), text, jam, "daily")
        )
        conn.commit()

        await update.message.reply_text("✅ Reminder harian disimpan")
    except:
        await update.message.reply_text("Format salah\n/ingatkan_harian 09:00 minum")

async def reminder_loop(app: Application):
    while True:
        now = datetime.now()

        rows = c.execute("SELECT id,chat_id,text,waktu,repeat FROM reminder").fetchall()

        for rid, chat_id, text, waktu, rep in rows:

            if rep == "once":
                dt = datetime.fromisoformat(waktu)
                if now >= dt:
                    await app.bot.send_message(chat_id, f"⏰ {text}")
                    c.execute("DELETE FROM reminder WHERE id=?", (rid,))
                    conn.commit()

            if rep == "daily":
                if now.strftime("%H:%M") == waktu:
                    await app.bot.send_message(chat_id, f"🔁 {text}")

        await asyncio.sleep(30)

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bot Finance Pro siap 👍\n\n"
        "/in jumlah\n"
        "/out jumlah\n"
        "/summary\n"
        "/insight\n"
        "/ingatkan\n"
        "/ingatkan_harian"
    )

# ================= MAIN (RAILWAY SAFE) =================

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("in", in_cmd))
    app.add_handler(CommandHandler("out", out_cmd))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("insight", insight))
    app.add_handler(CommandHandler("ingatkan", ingatkan))
    app.add_handler(CommandHandler("ingatkan_harian", ingatkan_harian))

    asyncio.create_task(reminder_loop(app))

    print("FULL PRO BOT jalan...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
