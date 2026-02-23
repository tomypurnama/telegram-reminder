async def main():
    app = Application.builder().token(TOKEN).build()

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("in", in_cmd))
    app.add_handler(CommandHandler("out", out_cmd))
    app.add_handler(CommandHandler("summary", summary))
    app.add_handler(CommandHandler("insight", insight))
    app.add_handler(CommandHandler("ingatkan", ingatkan))
    app.add_handler(CommandHandler("ingatkan_harian", ingatkan_harian))

    # background reminder loop
    asyncio.create_task(reminder_loop(app))

    print("FULL PRO BOT jalan...")

    # railway safe start
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # keep alive
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
