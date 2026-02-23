import os
import asyncio
import sqlite3
from datetime import datetime
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
    jumlah = float(args[0].replace(".",""))
    currency = args[1].upper()
    note = " ".join(args[2:]) if len(args)>2 else ""
    return jumlah, currency, note

def save_trx(tipe,jumlah,currency,note):
    c.execute(
        "INSERT INTO trx(tipe,jumlah,currency,note,created) VALUES(?,?,?,?,?)",
        (tipe,jumlah,currency,note,datetime.now().isoformat())
    )
    conn.commit()

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ FULL PRO BOT jalan")

async def in_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah,currency,note = parse_money(context.args)
        save_trx("in",jumlah,currency,note)
        await update.message.reply_text(f"➕ {jumlah:,.0f} {currency}")
    except:
        await update.message.reply_text("Format: /in 100000 idr")

async def out_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah,currency,note = parse_money(context.args)
        save_trx("out",jumlah,currency,note)
        await update.message.reply_text(f"➖ {jumlah:,.0f} {currency}")
    except:
        await update.message.reply_text("Format: /out 50 thb")

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = c.execute("SELECT tipe,jumlah,currency FROM trx").fetchall()

    idr=0
    thb=0

    for t,j,curr in rows:
        if curr=="IDR":
            idr += j if t=="in" else -j
        else:
            thb += j if t=="in" else -j

    await update.message.reply_text(f"📊 Summary\nIDR: {idr:,.0f}\nTHB: {thb:,.0f}")

async def ingatkan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        menit=int(context.args[0])
        text=" ".join(context.args[1:]) or "Reminder"

        await update.message.reply_text(f"⏳ {menit} menit")

        await asyncio.sleep(menit*60)

        await update.message.reply_text(f"⏰ {text}")
    except:
        await update.message.reply_text("Format /ingatkan 10 minum")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jam=context.args[0]
        text=" ".join(context.args[1:]) or "Reminder"

        c.execute(
            "INSERT INTO reminder(chat_id,text,time,repeat) VALUES(?,?,?,?)",
            (update.effective_chat.id,text,jam,"daily")
        )
        conn.commit()

        await update.message.reply_text("✅ Daily disimpan")
    except:
        await update.message.reply_text("Format /daily 07:00 bangun")

# ================= REMINDER LOOP =================
async def reminder_loop(app):
    while True:
        now=datetime.now().strftime("%H:%M")
        rows=c.execute("SELECT chat_id,text,time FROM reminder").fetchall()

        for chat_id,text,t in rows:
            if t==now:
                await app.bot.send_message(chat_id=chat_id,text=f"🔔 {text}")

        await asyncio.sleep(60)

# ================= MAIN =================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("in", in_cmd))
    app.add_handler(CommandHandler("out", out_cmd))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("ingatkan", ingatkan))
    app.add_handler(CommandHandler("daily", daily))

    app.job_queue.run_repeating(lambda ctx: asyncio.create_task(reminder_loop(app)), interval=60, first=5)

    print("BOT STABLE jalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
