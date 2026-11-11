import aiohttp
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

from services.quote_cache import QuoteCache
from services.tiss_cache import tiss_cache

from services.database import Database

load_dotenv("secrets.env")

class GregBot(commands.Bot):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.quote_cache = QuoteCache()
        self.http_session: aiohttp.ClientSession | None = None
        self.database = Database()

        # Sets pattern for Synopsis Message
        self.usage = lambda x: f"Usage: {self.command_prefix}{x}"

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
    intents=intents,
    help_command=None, # already uses slash command, instead of removing this line, please uncomment the prefix_help function in info.py
)
bot.token = os.getenv("TOKEN")