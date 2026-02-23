import os
import sqlite3
from datetime import date
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

# ===== DATABASE =====
conn = sqlite3.connect("cashflow.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS trx(
id INTEGER PRIMARY KEY AUTOINCREMENT,
tipe TEXT,
jumlah REAL,
currency TEXT,
catatan TEXT,
tanggal TEXT
)
""")
conn.commit()


# ===== HELPER =====
def detect_currency(jumlah: float):
    if jumlah >= 10000:
        return "IDR"
    return "THB"


def add_trx(tipe, jumlah, catatan):
    currency = detect_currency(jumlah)
    cur.execute(
        "INSERT INTO trx(tipe,jumlah,currency,catatan,tanggal) VALUES(?,?,?,?,?)",
        (tipe, jumlah, currency, catatan, str(date.today()))
    )
    conn.commit()


# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Cashflow bot siap\n\n"
        "/out jumlah catatan\n"
        "/in jumlah catatan\n"
        "/today"
    )


async def out_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah = float(context.args[0])
        catatan = " ".join(context.args[1:]) or "out"
        add_trx("OUT", jumlah, catatan)

        await update.message.reply_text(f"➖ {jumlah} disimpan ({catatan})")
    except:
        await update.message.reply_text("Format salah\nContoh: /out 20 makan")


async def in_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah = float(context.args[0])
        catatan = " ".join(context.args[1:]) or "in"
        add_trx("IN", jumlah, catatan)

        await update.message.reply_text(f"➕ {jumlah} disimpan ({catatan})")
    except:
        await update.message.reply_text("Format salah\nContoh: /in 500 gaji")


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tgl = str(date.today())

    cur.execute("SELECT tipe,jumlah,currency,catatan FROM trx WHERE tanggal=?", (tgl,))
    rows = cur.fetchall()

    if not rows:
        await update.message.reply_text("Tidak ada transaksi hari ini")
        return

    text = "📊 Hari ini\n\n"

    for r in rows:
        tipe, jumlah, curc, cat = r
        icon = "➕" if tipe == "IN" else "➖"
        text += f"{icon} {cat} — {jumlah} {curc}\n"

    await update.message.reply_text(text)


# ⭐ MAIN FIX (PENTING)
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("out", out_cmd))
    app.add_handler(CommandHandler("in", in_cmd))
    app.add_handler(CommandHandler("today", today))

    print("Cashflow bot jalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
