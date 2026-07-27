import aiohttp
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

from services.quote_cache import QuoteCache
from services.tiss_cache import tiss_cache

load_dotenv("secrets.env")

class GregBot(commands.Bot):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.quote_cache = QuoteCache()
        self.http_session: aiohttp.ClientSession | None = None
        self.add_check(self.only_me())

    def only_me(self):
        authors = [627465945522241555, 575710766787985435]
        async def predicate(ctx):
            return ctx.author.id in authors
        return predicate

    async def setup_hook(self):
        self.http_session = aiohttp.ClientSession(
            headers={"User-Agent": "GregBot/1.0"}
        )
        extensions = [
            "cogs.ai",
            "cogs.fun",
            "cogs.info",
            "cogs.moderation",
            "cogs.tiss",
            "cogs.utility",
            "listeners.messages",
            "listeners.events",
        ]

        tiss_cache.start_sweeper()

        for extension in extensions:
            await self.load_extension(extension)


intents = discord.Intents.default()
intents.message_content = True
intents.members = True


bot = GregBot(
    command_prefix="'",
    intents=intents
)
bot.token = os.getenv("TOKEN2")