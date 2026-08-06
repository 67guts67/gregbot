import discord
from discord.ext import commands
from discord import app_commands

from bot import bot

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    fun = app_commands.Group(
        name="fun",
        description="...",
    )

    @fun.command(name="meowl", description="Post Meowl GIF.")
    async def meowl(self, interaction: discord.Interaction):
        await interaction.response.send_message("https://klipy.com/gifs/meowl-cat-5")

        try:
            await interaction.channel.send("Yes, this is real!")
        except Exception as e:
            print(e)

    @fun.command(name="rquote", description="Get a random quote from the #quotes channel.")
    async def rquote(self, interaction: discord.Interaction):
        if not bot.quote_cache.loaded:
            await interaction.response.send_message(f"No quotes cached.")
            return

        message = bot.quote_cache.random()

        content = message.content

        if message.attachments:
            if content:
                content += "\n"
            content += "\n".join(
                attachment.url for attachment in message.attachments
            )

        if not content:
            await interaction.response.send_message("Selected message has no content.")
            return

        content += f"\n\n-# Original: {message.jump_url}"

        await interaction.response.send_message(
            content[:2000]
        )

    @fun.command(name="real", description="Respond with 'Yes, this is real.'")
    async def real(self, interaction: discord.Interaction):
        await interaction.response.send_message("Me when I lie:", ephemeral=True, delete_after=0)
        await interaction.channel.send("Yes, this is real.")

    @fun.command(name="fake", description="Respond with 'Yes, this is real.'")
    async def fake(self, interaction: discord.Interaction):
        await interaction.response.send_message("Me when I lie:", ephemeral=True, delete_after=0)
        await interaction.channel.send("Yes, this is fake.")

async def setup(bot):
    await bot.add_cog(Fun(bot))