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
kategori TEXT,
catatan TEXT,
tanggal TEXT
)
""")
conn.commit()


# ===== SMART CATEGORY =====
def detect_category(text: str):
    t = text.lower()

    if any(x in t for x in ["makan", "kopi", "food"]):
        return "Food"
    if any(x in t for x in ["grab", "transport", "bensin"]):
        return "Transport"
    if any(x in t for x in ["anak", "keluarga"]):
        return "Family"
    if any(x in t for x in ["gaji", "bonus"]):
        return "Income"

    return "Other"


def detect_currency(jumlah: float):
    if jumlah >= 10000:
        return "IDR"
    return "THB"


def add_trx(tipe, jumlah, catatan):
    currency = detect_currency(jumlah)
    kategori = detect_category(catatan)

    cur.execute(
        "INSERT INTO trx(tipe,jumlah,currency,kategori,catatan,tanggal) VALUES(?,?,?,?,?,?)",
        (tipe, jumlah, currency, kategori, catatan, str(date.today()))
    )
    conn.commit()


# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Cashflow bot v3 siap\n\n"
        "/out jumlah catatan\n"
        "/in jumlah catatan\n"
        "/today\n"
        "/summary\n"
        "/month"
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


async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tgl = str(date.today())

    cur.execute("""
    SELECT currency, tipe, SUM(jumlah)
    FROM trx
    WHERE tanggal=?
    GROUP BY currency, tipe
    """, (tgl,))
    rows = cur.fetchall()

    text = "📊 Summary hari ini\n\n"

    for c, t, j in rows:
        icon = "➕" if t == "IN" else "➖"
        text += f"{c} {icon} {j}\n"

    cur.execute("""
    SELECT kategori, SUM(jumlah), currency
    FROM trx
    WHERE tanggal=? AND tipe='OUT'
    GROUP BY kategori, currency
    """, (tgl,))
    krows = cur.fetchall()

    if krows:
        text += "\nKategori:\n"
        for k, j, c in krows:
            text += f"{k}: {j} {c}\n"

    await update.message.reply_text(text)


async def month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bulan = date.today().strftime("%Y-%m")

    cur.execute("""
    SELECT currency, tipe, SUM(jumlah)
    FROM trx
    WHERE substr(tanggal,1,7)=?
    GROUP BY currency, tipe
    """, (bulan,))
    rows = cur.fetchall()

    if not rows:
        await update.message.reply_text("Belum ada transaksi bulan ini")
        return

    text = "📅 Bulan ini\n\n"

    for c, t, j in rows:
        icon = "➕" if t == "IN" else "➖"
        text += f"{c} {icon} {j}\n"

    cur.execute("""
    SELECT kategori, SUM(jumlah), currency
    FROM trx
    WHERE substr(tanggal,1,7)=? AND tipe='OUT'
    GROUP BY kategori, currency
    """, (bulan,))
    krows = cur.fetchall()

    if krows:
        text += "\nKategori:\n"
        for k, j, c in krows:
            text += f"{k}: {j} {c}\n"

    await update.message.reply_text(text)


# ===== MAIN =====
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("out", out_cmd))
    app.add_handler(CommandHandler("in", in_cmd))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("month", month))

    print("Cashflow bot v3 jalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
