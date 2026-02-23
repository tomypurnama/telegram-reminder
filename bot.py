import os
import sqlite3
from datetime import date, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

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

BUDGET = {
    ("Food", "THB"): 300,
    ("Transport", "THB"): 150,
}

# ===== SMART =====
def detect_category(text: str):
    t = text.lower()
    if any(x in t for x in ["makan","kopi","food"]): return "Food"
    if any(x in t for x in ["grab","transport","bensin"]): return "Transport"
    if any(x in t for x in ["anak","keluarga"]): return "Family"
    if any(x in t for x in ["gaji","bonus"]): return "Income"
    return "Other"

def parse_input(args):
    jumlah = float(args[0])

    currency = "THB"
    start_note = 1

    if len(args) > 1 and args[1].lower() in ["thb","idr"]:
        currency = args[1].upper()
        start_note = 2

    catatan = " ".join(args[start_note:]) or "trx"
    return jumlah, currency, catatan

def add_trx(tipe, jumlah, currency, catatan):
    kategori = detect_category(catatan)

    cur.execute(
        "INSERT INTO trx(tipe,jumlah,currency,kategori,catatan,tanggal) VALUES(?,?,?,?,?,?)",
        (tipe, jumlah, currency, kategori, catatan, str(date.today()))
    )
    conn.commit()

    return kategori, currency

def check_budget(kategori, currency):
    tgl = str(date.today())

    cur.execute("""
    SELECT SUM(jumlah) FROM trx
    WHERE tanggal=? AND kategori=? AND currency=? AND tipe='OUT'
    """, (tgl, kategori, currency))

    total = cur.fetchone()[0] or 0
    limit = BUDGET.get((kategori, currency))

    if not limit: return None
    if total >= limit: return f"🚨 {kategori} melewati budget {limit} {currency}"
    if total >= limit * 0.8: return f"⚠️ {kategori} mendekati budget {limit} {currency}"
    return None

# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Cashflow FULL (currency manual)\n\n"
        "/out 20 thb makan\n"
        "/out 1000000 idr kirim anak\n"
        "/week /month /summary"
    )

async def out_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah, currency, catatan = parse_input(context.args)

        kategori, currency = add_trx("OUT", jumlah, currency, catatan)

        await update.message.reply_text(f"➖ {jumlah} {currency} disimpan ({catatan})")

        alert = check_budget(kategori, currency)
        if alert:
            await update.message.reply_text(alert)

    except:
        await update.message.reply_text("Format: /out 20 thb makan")

async def in_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah, currency, catatan = parse_input(context.args)

        add_trx("IN", jumlah, currency, catatan)

        await update.message.reply_text(f"➕ {jumlah} {currency} disimpan ({catatan})")

    except:
        await update.message.reply_text("Format: /in 500 thb gaji")

async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = date.today() - timedelta(days=6)

    cur.execute("""
    SELECT currency, tipe, SUM(jumlah)
    FROM trx WHERE tanggal>=?
    GROUP BY currency, tipe
    """, (str(start),))
    rows = cur.fetchall()

    if not rows:
        await update.message.reply_text("Belum ada transaksi minggu ini")
        return

    text = "📆 Minggu ini\n\n"
    for c, t, j in rows:
        icon = "➕" if t == "IN" else "➖"
        text += f"{c} {icon} {j}\n"

    await update.message.reply_text(text)

# ===== MAIN =====
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("out", out_cmd))
    app.add_handler(CommandHandler("in", in_cmd))
    app.add_handler(CommandHandler("week", week))

    print("Cashflow currency manual jalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
