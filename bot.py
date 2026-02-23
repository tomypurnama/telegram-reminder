import os
import asyncio
import sqlite3
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

# ================= DB =================

conn = sqlite3.connect("data.db", check_same_thread=False)
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
time TEXT,
repeat TEXT
)
""")

conn.commit()

# ================= UTILS =================

def parse_money(args):
    if len(args) < 2:
        raise Exception("format")

    jumlah_raw = args[0].replace(".", "")
    jumlah = float(jumlah_raw)

    currency = args[1].upper()
    if currency not in ["IDR","THB"]:
        raise Exception("currency")

    note = " ".join(args[2:]) if len(args) > 2 else ""

    return jumlah, currency, note

def save_trx(tipe, jumlah, currency, note):
    c.execute(
        "INSERT INTO trx(tipe,jumlah,currency,note,created) VALUES(?,?,?,?,?)",
        (tipe, jumlah, currency, note, datetime.now().isoformat())
    )
    conn.commit()

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ FULL PRO BOT jalan")

# ----- INCOME -----
async def in_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah, currency, note = parse_money(context.args)
        save_trx("in", jumlah, currency, note)
        await update.message.reply_text(f"➕ {jumlah:,.0f} {currency} disimpan")
    except:
        await update.message.reply_text("Format salah\n/in 100000 idr gaji")

# ----- OUT + LIMIT REALTIME -----
async def out_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah, currency, note = parse_money(context.args)
        save_trx("out", jumlah, currency, note)

        today = datetime.now().date().isoformat()
        rows = c.execute("SELECT tipe,jumlah,currency,created FROM trx").fetchall()

        idr_today = 0
        thb_today = 0

        for t,j,curr,created in rows:
            if created.startswith(today) and t == "out":
                if curr == "IDR":
                    idr_today += j
                else:
                    thb_today += j

        LIMIT_IDR = 1_000_000
        LIMIT_THB = 300

        msg = f"➖ {jumlah:,.0f} {currency} disimpan"

        if currency == "IDR" and idr_today > LIMIT_IDR:
            msg += "\n⚠️ Limit IDR harian terlewati"

        if currency == "THB" and thb_today > LIMIT_THB:
            msg += "\n⚠️ Limit THB harian terlewati"

        await update.message.reply_text(msg)

    except:
        await update.message.reply_text("Format salah\n/out 200 thb makan")

# ----- SUMMARY -----
async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = c.execute("SELECT tipe,jumlah,currency FROM trx").fetchall()

    idr = 0
    thb = 0

    for t,j,curr in rows:
        if curr == "IDR":
            idr += j if t=="in" else -j
        else:
            thb += j if t=="in" else -j

    await update.message.reply_text(
        f"📊 Summary\nIDR: {idr:,.0f}\nTHB: {thb:,.0f}"
    )

# ----- REMINDER SEKALI -----
async def ingatkan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        menit = int(context.args[0])
        text = " ".join(context.args[1:]) or "Reminder"

        await update.message.reply_text(f"⏳ {menit} menit: {text}")

        await asyncio.sleep(menit * 60)

        await update.message.reply_text(f"⏰ {text}")
    except:
        await update.message.reply_text("Format salah\n/ingatkan 10 minum air")

# ----- REMINDER HARIAN (DB) -----
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jam = context.args[0]
        text = " ".join(context.args[1:]) or "Reminder"

        c.execute(
            "INSERT INTO reminder(chat_id,text,time,repeat) VALUES(?,?,?,?)",
            (update.effective_chat.id, text, jam, "daily")
        )
        conn.commit()

        await update.message.reply_text(f"🔁 Reminder harian {jam} disimpan")

    except:
        await update.message.reply_text("Format salah\n/daily 07:00 bangun")

# ================= REMINDER LOOP =================

async def reminder_loop(app):
    while True:
        now = datetime.now().strftime("%H:%M")

        rows = c.execute("SELECT id,chat_id,text,time,repeat FROM reminder").fetchall()

        for rid,chat_id,text,t,r in rows:
            if t == now:
                await app.bot.send_message(chat_id=chat_id, text=f"🔔 {text}")

        await asyncio.sleep(60)

# ================= MAIN =================

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("in", in_cmd))
    app.add_handler(CommandHandler("out", out_cmd))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("ingatkan", ingatkan))
    app.add_handler(CommandHandler("daily", daily))

    asyncio.create_task(reminder_loop(app))

    print("FULL PRO BOT jalan...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
