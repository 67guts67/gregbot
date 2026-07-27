import discord
from discord.ext import commands


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Get a random quote from the #quotes channel.")
    async def rquote(self, ctx):
        if not self.bot.quote_cache.loaded:
            await ctx.send("No quotes cached.")
            return
        message = self.bot.quote_cache.random()

        content = message.content

        if message.attachments:
            if content:
                content += "\n"
            content += "\n".join(
                attachment.url for attachment in message.attachments
            )

        if not content:
            await ctx.send("Selected message has no content.")
            return

        content += f"\n\n-# Original: {message.jump_url}"

        await ctx.send(
            content[:2000],
            allowed_mentions=discord.AllowedMentions.none()
        )

    @commands.command(help="Post Meowl GIF.")
    async def meowl(self, ctx):
        await ctx.send('https://klipy.com/gifs/meowl-cat-5')
        await ctx.send('Yes, this is real.')

    @commands.command(help="Respond with 'Yes, this is fake.'")
    async def fake(self, ctx):
        await ctx.message.delete(delay=1)
        await ctx.send('Yes, this is fake.')

    @commands.command(help="Respond with 'Yes, this is real.'")
    async def real(self, ctx):
        await ctx.message.delete(delay=1)
        await ctx.send('Yes, this is real.')


async def setup(bot):
    await bot.add_cog(Fun(bot))