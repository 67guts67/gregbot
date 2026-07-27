import discord
from discord.ext import commands

from config import QUOTE_CHANNEL_ID


class Events(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):

        print(f"Logged in as {self.bot.user}", flush=True)

        #cache the quotes
        if not self.bot.quote_cache.loaded:

            channel = self.bot.get_channel(QUOTE_CHANNEL_ID)

            if channel is None:
                channel = await self.bot.fetch_channel(QUOTE_CHANNEL_ID)

            try:
                async for message in channel.history(limit=None):
                    self.bot.quote_cache.add(message)

                self.bot.quote_cache.loaded = True

            except Exception as e:
                print(f"Failed loading quotes: {e}", flush=True)

            print(
                f"Loaded {len(self.bot.quote_cache)} quotes",
                flush=True
            )



async def setup(bot):
    await bot.add_cog(Events(bot))