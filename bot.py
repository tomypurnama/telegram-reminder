async def out_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        jumlah, currency, note = parse_money(context.args)

        save_trx("out", jumlah, currency, note)

        # ===== LIMIT REALTIME =====
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
