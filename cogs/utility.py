from typing import Optional

import discord
from discord.ext import commands
from config import ALLOWED_ROLE_IDS, TYPE_TO_GET_BANNED_ID


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Ping one of the allowed self-assignable roles.")
    async def pingroles(self, ctx, role_name: str = None, *, msg: str = None):
        if role_name is None:
            await ctx.send("Please specify a role.")
            return

        try:
            role = await commands.RoleConverter().convert(ctx, role_name)
        except commands.RoleNotFound:
            role = discord.utils.find(
                lambda r: r.name.lower() == role_name.lower(),
                ctx.guild.roles
            )

        if role is None:
            await ctx.send("That role could not be found.")
            return

        if role.id not in ALLOWED_ROLE_IDS:
            await ctx.send("That role cannot be pinged.")
            return

        embed = discord.Embed(
            description=f"{ctx.author.mention} pinged {role.mention}",
            color=discord.Color.blurple()
        )
        embed.add_field(name="msg:", value=msg if msg else "*(no message provided)*", inline=False)

        await ctx.send(
            content=role.mention, 
            embed=embed,
            allowed_mentions=discord.AllowedMentions(
                users=[ctx.author],
                roles=[role]
            )
        )

    @commands.command(help="List all roles that can be pinged with ^pingroles.")
    async def validroles(self, ctx):
        await ctx.send('''
1438155180171595786,  # zeichenspiele
1444330125347782717,  # minecraft
1444330248031178822,  # league
1444330309200908551,  # friendslop
1444330436858744946,  # mario kart
1503123095760666644,  # repo
1521817122131673088,  # test
1499383073320472586   # unemploymentsquad
''')

    @commands.command(help="Display the bot's current Discord status.")
    async def status(self, ctx):
        await ctx.send(self.bot.status)

    @commands.command(help="Display the bot's current latency.")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! {latency}ms")

    @commands.command(help="Send a message to the current or a specified text channel.")
    async def echo(self, ctx, channel: Optional[discord.TextChannel] = None, *, string: str):
        target = channel or ctx.channel

        if target.id == TYPE_TO_GET_BANNED_ID:
            await ctx.send("Nice try")
            return

        perms = target.permissions_for(ctx.author)
        if not (perms.view_channel and perms.send_messages):
            await ctx.send("You don't have permission to send there.")
            return

        safe = string[:2000]
        allowed_mentions = discord.AllowedMentions(
            users=True,
            roles=False,
            everyone=False
        )
        try:
            await target.send(safe, allowed_mentions=allowed_mentions)
        except discord.Forbidden:
            await ctx.send("I don't have permission to send there.")
        except discord.HTTPException as e:
            await ctx.send(f"Error sending message (HTTP {e.status})")

    @echo.error
    async def echo_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Usage: `^echo [channel] <message>`")
        else:
            raise error


async def setup(bot):
    await bot.add_cog(Utility(bot))