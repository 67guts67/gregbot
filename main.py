import asyncio
from bot import bot
from services.keep_alive import start


async def main():
    start()

    async with bot:
        await bot.start(bot.token)


asyncio.run(main())