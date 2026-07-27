import discord
from datetime import timedelta
from discord.ext import commands
import config as cfg

class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Delete messages by amount or message link.")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, arg: str):
        MAX_PURGE = cfg.MAX_PURGE
        MESSAGE_LINK_RE = cfg.MESSAGE_LINK_RE

        if arg.isdigit():
            amount = int(arg)

            if amount < 1:
                return await ctx.send("Amount must be at least 1.", delete_after=5)

            if amount > MAX_PURGE:
                return await ctx.send(
                    f"You can delete at most {MAX_PURGE} messages at once.",
                    delete_after=5
                )

            deleted = await ctx.channel.purge(limit=amount + 1)

            confirm = await ctx.send(
                f"Deleted **{len(deleted) - 1}** messages.",
                delete_after=5
            )
            return

        match = MESSAGE_LINK_RE.match(arg)
        if not match:
            return await ctx.send(
                "Usage:\n"
                "`^purge <amount>`\n"
                "`^purge <message link>`",
                delete_after=8
            )

        channel_id = int(match.group(1))
        message_id = int(match.group(2))

        if channel_id != ctx.channel.id:
            return await ctx.send(
                "The linked message must be in this channel.",
                delete_after=5
            )

        try:
            target = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            return await ctx.send(
                "Couldn't find that message.",
                delete_after=5
            )

        # Count messages that would be deleted
        messages = [
            m async for m in ctx.channel.history(
                after=target,
                oldest_first=False,
                limit=MAX_PURGE + 1
            )
        ]

        if len(messages) > MAX_PURGE:
            return await ctx.send(
                f"Refusing to delete more than {MAX_PURGE} messages.\n"
                "Use a newer message link.",
                delete_after=8
            )

        deleted = await ctx.channel.purge(after=target)

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send(
            f"🗑 Deleted **{len(deleted)}** messages.",
            delete_after=5
        )

    @purge.error
    async def purge_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(
                "You cant run this command, noob",
                delete_after=5
            )
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(
                "I need the **Manage Messages** permission.",
                delete_after=5
            )
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                "Usage:\n"
                "`^purge <amount>`\n"
                "`^purge <message link>`",
                delete_after=8
            )

    @commands.command(help="Ban Gregor and yourself.")
    async def ban(self, ctx):
        GREGOR_ID = cfg.GREGOR_ID
        try:
            member = ctx.guild.get_member(GREGOR_ID)
            if member is None:
                member = await ctx.guild.fetch_member(GREGOR_ID)

            await member.ban()
            await ctx.send(f"<@575710766787985435> banned.")

            await ctx.author.ban()
            await ctx.send(f"<@{ctx.author.id}> banned.")

        except discord.Forbidden:
            await ctx.send("I don't have permission to ban this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed (HTTP {e.status}).")

    @commands.command(help="Timeout Gregor and yourself for 60 seconds.")
    async def timeout(self, ctx):
        GREGOR_ID = cfg.GREGOR_ID
        try:
            member = ctx.guild.get_member(GREGOR_ID)
            if member is None:
                member = await ctx.guild.fetch_member(GREGOR_ID)
            duration = timedelta(minutes=1)

            await member.timeout(duration)
            await ctx.send(f"<@575710766787985435> timed out for 60 seconds.")

            await ctx.author.timeout(duration)
            await ctx.send(f"<@{ctx.author.id}> timed out for 60 seconds.")

        except discord.Forbidden:
            await ctx.send("I don't have permission to timeout this user.")
        except discord.HTTPException as e:
            await ctx.send(f"Failed (HTTP {e.status}).")

    @commands.command(help="Issue another warning to Gregor.")
    async def warn(self, ctx):
        cfg.GREGOR_WARNS += 1
        await ctx.send(f'<@575710766787985435> has been warned. This is warning **{cfg.GREGOR_WARNS}**!')

    @commands.command(help="Timeout yourself for a specified number of minutes (1-10080).")
    async def selftimeout(self, ctx, minutes: int = None):
        try:
            if minutes is None:
                await ctx.send(f"Enter an amount of minutes between 1 and 10080.")
                return

            if minutes > 10080:
                minutes = 10080

            if minutes < 1:
                minutes = 1

            await ctx.author.timeout(timedelta(minutes=minutes))
            await ctx.send(f"{ctx.author} timed out for {minutes} minutes.")

        except discord.Forbidden:
            await ctx.send("I don't have permission to timeout this user.")

        except discord.HTTPException as e:
            await ctx.send(f"Failed (HTTP {e.status}).")

    @selftimeout.error
    async def selftimeout_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Please enter a valid number of minutes in base 10.")


async def setup(bot):
    await bot.add_cog(Moderation(bot))