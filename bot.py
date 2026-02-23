import os
import sqlite3
from datetime import date, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

EXCHANGE_RATE = 800

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

# ===== UTIL =====
def clean_number(text: str):
    return float(text.replace(".", "").replace(",", ""))

def detect_category(text: str):
    t = text.lower()
    if "makan" in t or "kopi" in t: return "Food"
    if "grab" in t or "transport" in t: return "Transport"
    if "anak" in t or "keluarga" in t: return "Family"
    if "gaji" in t or "bonus" in t: return "Income"
    return "Other"

def parse_input(args):
    jumlah = clean_number(args[0])

    currency = "THB"
    start_note = 1

    if len(args) > 1 and args[1].lower() in ["thb","idr"]:
        currency = args[1].upper()
        start_note = 2

    catatan = " ".join(args[start_note:]) or "trx"
    return jumlah, currency, catatan

def to_idr(jumlah, currency):
    return jumlah if currency == "IDR" else jumlah * EXCHANGE_RATE

def add_trx(tipe, jumlah, currency, catatan):
    kategori = detect_category(catatan)

    cur.execute(
        "INSERT INTO trx(tipe,jumlah,currency,kategori,catatan,tanggal) VALUES(?,?,?,?,?,?)",
        (tipe, jumlah, currency, kategori, catatan, str(date.today()))
    )
    conn.commit()

# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Cashflow PRO siap\n"
        "/out 20 thb makan\n"
        "/in 1.000.000 idr gaji\n"
        "/summary /week /month"
    )

async def out_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah, currency, catatan = parse_input(context.args)
        add_trx("OUT", jumlah, currency, catatan)
        await update.message.reply_text(f"➖ {jumlah} {currency} disimpan ({catatan})")
    except:
        await update.message.reply_text("Format: /out 20 thb makan")

async def in_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah, currency, catatan = parse_input(context.args)
        add_trx("IN", jumlah, currency, catatan)
        await update.message.reply_text(f"➕ {jumlah} {currency} disimpan ({catatan})")
    except:
        await update.message.reply_text("Format: /in 500 thb gaji")

# ===== FIX TOTAL =====
def calc_total(rows):
    total = 0
    for tipe, jumlah, curc in rows:
        idr = to_idr(jumlah, curc)

        if tipe == "OUT":
            total -= idr
        else:
            total += idr

    return total

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tgl = str(date.today())

    cur.execute("SELECT tipe,jumlah,currency FROM trx WHERE tanggal=?", (tgl,))
    rows = cur.fetchall()

    total = calc_total(rows)

    await update.message.reply_text(
        f"📊 Summary hari ini\n\nTotal (IDR eq): {int(total):,}"
    )

async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = date.today() - timedelta(days=6)

    cur.execute("SELECT tipe,jumlah,currency FROM trx WHERE tanggal>=?", (str(start),))
    rows = cur.fetchall()

    total = calc_total(rows)

    await update.message.reply_text(
        f"📆 Minggu ini (IDR eq): {int(total):,}"
    )

async def month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bulan = date.today().strftime("%Y-%m")

    cur.execute("SELECT tipe,jumlah,currency FROM trx WHERE substr(tanggal,1,7)=?", (bulan,))
    rows = cur.fetchall()

    total = calc_total(rows)

    await update.message.reply_text(
        f"📅 Bulan ini (IDR eq): {int(total):,}"
    )

# ===== MAIN =====
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("out", out_cmd))
    app.add_handler(CommandHandler("in", in_cmd))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("week", week))
    app.add_handler(CommandHandler("month", month))

    print("Cashflow PRO FIX jalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
