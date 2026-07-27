import asyncio

from config import QUOTE_CHANNEL_ID, TYPE_TO_GET_BANNED_ID
import discord
from discord.ext import commands


class Messages(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_message(self, message):

        await self.cache_quotes(message)
        await self.react_riener(message)
        await self.delete_in_watched_channel(message)


    async def cache_quotes(self, message):

        if message.channel.id != QUOTE_CHANNEL_ID:
            return

        self.bot.quote_cache.add(message)

    async def react_riener(self, message):

        if message.author.bot:
            return

        riener = 1292816924383776880

        if (
            "riener" in message.content.lower()
            or "<:riener:1292816924383776880>" in message.content
        ):
            emoji = self.bot.get_emoji(riener)

            if emoji:
                await message.add_reaction(emoji)

    async def delete_in_watched_channel(self, message):
        if message.channel.id == TYPE_TO_GET_BANNED_ID and message.author != self.bot.user:
            try:
                await message.delete(delay=5)
            except (discord.Forbidden, discord.HTTPException,  discord.NotFound) as e:
                print(e,flush=True)

async def setup(bot):
    await bot.add_cog(Messages(bot))