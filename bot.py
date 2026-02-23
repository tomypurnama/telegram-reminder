import os
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

# ===== DATABASE =====
conn = sqlite3.connect("cashflow.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS transaksi (
id INTEGER PRIMARY KEY AUTOINCREMENT,
tipe TEXT,
jumlah REAL,
currency TEXT,
kategori TEXT,
tanggal TEXT
)
""")
conn.commit()

# ===== COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Cashflow bot siap 👍\n"
        "/keluar 80 thb makan\n"
        "/masuk 1000000 idr gaji\n"
        "/saldo\n"
        "/hari"
    )

async def keluar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah = float(context.args[0])
        currency = context.args[1].lower()
        kategori = " ".join(context.args[2:]) or "lainnya"

        cursor.execute(
            "INSERT INTO transaksi (tipe,jumlah,currency,kategori,tanggal) VALUES (?,?,?,?,?)",
            ("keluar", jumlah, currency, kategori, datetime.now().isoformat())
        )
        conn.commit()

        await update.message.reply_text("✅ Pengeluaran dicatat")

    except:
        await update.message.reply_text("Format: /keluar 80 thb makan")

async def masuk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah = float(context.args[0])
        currency = context.args[1].lower()
        kategori = " ".join(context.args[2:]) or "lainnya"

        cursor.execute(
            "INSERT INTO transaksi (tipe,jumlah,currency,kategori,tanggal) VALUES (?,?,?,?,?)",
            ("masuk", jumlah, currency, kategori, datetime.now().isoformat())
        )
        conn.commit()

        await update.message.reply_text("✅ Pemasukan dicatat")

    except:
        await update.message.reply_text("Format: /masuk 1000000 idr gaji")

async def saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = cursor.execute("""
    SELECT currency,
    SUM(CASE WHEN tipe='masuk' THEN jumlah ELSE 0 END) -
    SUM(CASE WHEN tipe='keluar' THEN jumlah ELSE 0 END)
    FROM transaksi
    GROUP BY currency
    """).fetchall()

    if not rows:
        await update.message.reply_text("Belum ada data")
        return

    teks = "Saldo:\n"
    for currency, total in rows:
        teks += f"{currency.upper()}: {total:,.0f}\n"

    await update.message.reply_text(teks)

async def hari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().date().isoformat()

    rows = cursor.execute("""
    SELECT tipe,jumlah,currency,kategori
    FROM transaksi
    WHERE substr(tanggal,1,10)=?
    """, (today,)).fetchall()

    if not rows:
        await update.message.reply_text("Tidak ada transaksi hari ini")
        return

    teks = "Hari ini:\n"
    for tipe, jumlah, currency, kategori in rows:
        teks += f"{tipe} {jumlah} {currency} — {kategori}\n"

    await update.message.reply_text(teks)

# ===== RUN BOT =====
async def run():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("keluar", keluar))
    app.add_handler(CommandHandler("masuk", masuk))
    app.add_handler(CommandHandler("saldo", saldo))
    app.add_handler(CommandHandler("hari", hari))

    print("Cashflow bot jalan...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

import asyncio
loop = asyncio.get_event_loop()
loop.create_task(run())
loop.run_forever()
