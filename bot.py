import os
import sqlite3
from datetime import date, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

# ===== CONFIG =====
EXCHANGE_RATE = 800  # 1 THB = 800 IDR (bisa ubah manual)

BUDGET = {
    ("Food", "THB"): 300,
    ("Transport", "THB"): 150,
}

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

# ===== UTIL =====
def clean_number(text: str):
    return float(text.replace(".", "").replace(",", ""))

def detect_category(text: str):
    t = text.lower()
    if any(x in t for x in ["makan","kopi","food"]): return "Food"
    if any(x in t for x in ["grab","transport","bensin"]): return "Transport"
    if any(x in t for x in ["anak","keluarga"]): return "Family"
    if any(x in t for x in ["gaji","bonus"]): return "Income"
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
    return kategori

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

def insight_period(start_date):
    cur.execute("""
    SELECT kategori, SUM(jumlah), currency
    FROM trx
    WHERE tanggal>=? AND tipe='OUT'
    GROUP BY kategori, currency
    ORDER BY SUM(jumlah) DESC
    LIMIT 1
    """, (str(start_date),))
    row = cur.fetchone()

    if row:
        return f"💡 Pengeluaran terbesar: {row[0]} ({row[1]} {row[2]})"
    return None

# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Cashflow PRO siap\n\n"
        "/out 20 thb makan\n"
        "/out 1.000.000 idr kirim anak\n"
        "/summary /week /month"
    )

async def out_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah, currency, catatan = parse_input(context.args)
        kategori = add_trx("OUT", jumlah, currency, catatan)

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

async def summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tgl = str(date.today())

    cur.execute("""
    SELECT tipe,jumlah,currency FROM trx WHERE tanggal=?
    """, (tgl,))
    rows = cur.fetchall()

    total_idr = 0
    text = "📊 Summary hari ini\n\n"

    for tipe, jumlah, curc in rows:
        total_idr += to_idr(jumlah if tipe=="OUT" else -jumlah, curc)

    text += f"Total (IDR equivalent): {int(total_idr)}\n"

    insight = insight_period(tgl)
    if insight:
        text += "\n" + insight

    await update.message.reply_text(text)

async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = date.today() - timedelta(days=6)

    cur.execute("SELECT tipe,jumlah,currency FROM trx WHERE tanggal>=?", (str(start),))
    rows = cur.fetchall()

    total = 0
    for tipe, jumlah, curc in rows:
        total += to_idr(jumlah if tipe=="OUT" else -jumlah, curc)

    text = f"📆 Minggu ini (IDR eq): {int(total)}\n"
    insight = insight_period(start)
    if insight:
        text += insight

    await update.message.reply_text(text)

async def month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bulan = date.today().strftime("%Y-%m")

    cur.execute("SELECT tipe,jumlah,currency FROM trx WHERE substr(tanggal,1,7)=?", (bulan,))
    rows = cur.fetchall()

    total = 0
    for tipe, jumlah, curc in rows:
        total += to_idr(jumlah if tipe=="OUT" else -jumlah, curc)

    text = f"📅 Bulan ini (IDR eq): {int(total)}\n"

    insight = insight_period(bulan + "-01")
    if insight:
        text += insight

    await update.message.reply_text(text)

# ===== MAIN =====
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("out", out_cmd))
    app.add_handler(CommandHandler("in", in_cmd))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("week", week))
    app.add_handler(CommandHandler("month", month))

    print("Cashflow PRO jalan...")
    app.run_polling()

if __name__ == "__main__":
    main()
