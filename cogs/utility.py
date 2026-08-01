from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands
from config import ALLOWED_ROLE_IDS, TYPE_TO_GET_BANNED_ID

from bot import bot

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    utility = app_commands.Group(
        name="utility",
        description="..."
    )

    @utility.command(name="echo", description="Send a message to the current or a specified text channel.")
    @app_commands.describe(string="The text to echo")
    @app_commands.describe(target="The target channel to echo message [optional - default: Channel in which command was invoked]")
    async def echo(
            self,
            interaction: discord.Interaction,
            string: str,
            target: Optional[discord.TextChannel]
    ):
        if target:
            if target.id == TYPE_TO_GET_BANNED_ID:
                await interaction.response.send_message("Nice try")
                return

            perms = target.permissions_for(interaction.user)
            if not (perms.view_channel and perms.send_messages):
                await interaction.response.send_message("You don't have permission to send there.")
                return

        else:
            target = interaction.channel

        safe = string[:2000]
        allowed_mentions = discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
        try:
            message = await target.send(safe, allowed_mentions=allowed_mentions)
            await interaction.response.send_message(f"Message send in {message.jump_url}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to send there.")
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Error sending message (HTTP {e.status})")

    @utility.command(name="ping", description="Display the bot's current latency.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(bot.latency * 1000)
        await interaction.response.send_message(f"Pong! {latency}ms")

    @utility.command(name="pingroles", description="Ping one of the allowed self-assignable roles.")
    @app_commands.choices(role = [
        app_commands.Choice(name="zeichenspiele",     value="1438155180171595786"),
        app_commands.Choice(name="minecraft",         value="1444330125347782717"),
        app_commands.Choice(name="league",            value="1444330248031178822"),
        app_commands.Choice(name="friendslop",        value="1444330309200908551"),
        app_commands.Choice(name="mario kart",        value="1444330436858744946"),
        app_commands.Choice(name="repo",              value="1503123095760666644"),
        app_commands.Choice(name="test",              value="1521817122131673088"),
        app_commands.Choice(name="unemploymentsquad", value="1499383073320472586"),
    ])
    @app_commands.describe(msg="The message to send to the specified role")
    @app_commands.describe(role="The role to ping")
    async def pingroles(self, interaction: discord.Interaction, role: app_commands.Choice[str], msg: str):
        pingedRole = interaction.guild.get_role(int(role.value))

        author = interaction.user

        try:
            embed = discord.Embed(
                description=f"{author.mention} pinged {pingedRole.mention}",
                color=discord.Color.blurple()
            )
            embed.add_field(name="msg:", value=msg if msg else "*(no message provided)*", inline=False)

            await interaction.response.send_message(f"{pingedRole.name} pinged", ephemeral=True)

            await interaction.channel.send(
                content=pingedRole.mention,
                embed=embed,
                allowed_mentions=discord.AllowedMentions(
                    users=[author],
                    roles=[pingedRole]
                )
            )

        except Exception:
            await interaction.response.send_message(f"Error pinging the specified role!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Utility(bot))