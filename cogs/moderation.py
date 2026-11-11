import discord
from datetime import timedelta
from discord.ext import commands
from discord import app_commands
import config as cfg

from services.database import database_operation

class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    moderation = app_commands.Group(
        name="moderation",
        description="..."
    )

    @moderation.command(name="purge", description="Delete messages by amount or message link.")
    @app_commands.checks.has_permissions(manage_messages=True)
    @app_commands.checks.bot_has_permissions(manage_messages=True)
    @app_commands.describe(arg="The amount of messages to delete | The message link till which all messages will be deleted")
    async def purge(self, interaction: discord.Interaction, arg: str):
        try:
            MAX_PURGE = cfg.MAX_PURGE
            MESSAGE_LINK_RE = cfg.MESSAGE_LINK_RE
            await interaction.response.defer(ephemeral=True)

            if arg.isdigit():
                amount = int(arg)

                if amount < 1:
                    await interaction.followup.send("Amount must be at least 1.", ephemeral=True)
                    return

                if amount > MAX_PURGE:
                    await interaction.followup.send(
                        f"You can delete at most {MAX_PURGE} messages at once.",
                        ephemeral=True
                    )
                    return

                deleted = await interaction.channel.purge(limit=amount + 1)

                await interaction.followup.send(
                    f"Deleted **{len(deleted) - 1}** messages.",
                    ephemeral=True
                )
                return

            match = MESSAGE_LINK_RE.match(arg)
            if not match:
                await interaction.followup.send(
                    "Usage:\n"
                    "`^purge <amount>`\n"
                    "`^purge <message link>`",
                    ephemeral=True
                )
                return

            channel_id = int(match.group(1))
            message_id = int(match.group(2))

            if channel_id != interaction.channel.id:
                await interaction.followup.send(
                    "The linked message must be in this channel.",
                    ephemeral=True
                )
                return

            try:
                target = await interaction.channel.fetch_message(message_id)
            except discord.NotFound:
                await interaction.followup.send(
                    "Couldn't find that message.",
                    ephemeral=True
                )
                return

            # Count messages that would be deleted
            messages = [
                m async for m in interaction.channel.history(
                    after=target,
                    oldest_first=False,
                    limit=MAX_PURGE + 1
                )
            ]

            if len(messages) > MAX_PURGE:
                await interaction.followup.send(
                    f"Refusing to delete more than {MAX_PURGE} messages.\n"
                    "Use a newer message link.",
                    ephemeral=True
                )
                return

            deleted = await interaction.channel.purge(after=target)

            await interaction.followup.send(
                f"🗑 Deleted **{len(deleted)}** messages.",
                ephemeral=True
            )
        except Exception as e:
            interaction.response.send_message(f"Failed to purge messages.", ephemeral=True)
            print(e)

    @purge.error
    async def purge_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "You cant run this command, noob",
                ephemeral=True
            )
        elif isinstance(error, app_commands.BotMissingPermissions):
            await interaction.response.send_message(
                "I need the **Manage Messages** permission.",
                ephemeral=True
            )

    @moderation.command(name="ban", description="Ban Gregor and yourself.")
    @database_operation(write=True)
    async def ban(self, interaction: discord.Interaction):
        GREGOR_ID = cfg.GREGOR_ID
        try:
            member = interaction.guild.get_member(GREGOR_ID)
            if member is None:
                member = await interaction.guild.fetch_member(GREGOR_ID)

            await member.ban()
            await interaction.response.send_message(f"<@575710766787985435> banned.")

            self.bot.database.update_user_int(GREGOR_ID, 1, "bans_received")
            self.bot.database.update_user_int(interaction.user.id, 1, "bans_issued")

            await interaction.user.ban()
            await interaction.followup.send(f"<@{interaction.user.id}> banned.")

            self.bot.database.update_user_int(interaction.user.id, 1, "bans_received")

        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to ban this user.")
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Failed (HTTP {e.status}).")

    @moderation.command(name="timeout", description="Timeout Gregor and yourself for 60 seconds.")
    @database_operation(write=True)
    async def timeout(self, interaction: discord.Interaction):
        GREGOR_ID = cfg.GREGOR_ID
        try:
            self.bot.database.db.pull()

            member = interaction.guild.get_member(GREGOR_ID)
            if member is None:
                member = await interaction.guild.fetch_member(GREGOR_ID)
            duration = timedelta(minutes=1)

            await member.timeout(duration)
            await interaction.response.send_message(f"<@575710766787985435> timed out for 60 seconds.")

            self.bot.database.update_user_int(GREGOR_ID, 60, "on_timeout")

            await interaction.user.timeout(duration)
            await interaction.followup.send(f"<@{interaction.user.id}> timed out for 60 seconds.")

            self.bot.database.update_user_int(interaction.user.id, 60, "on_timeout")

            self.bot.database.db.commit()
            self.bot.database.db.push()

        except discord.Forbidden:
            await interaction.followup.send("I don't have permission to timeout this user.")
        except discord.HTTPException as e:
            await interaction.response.send_message(f"Failed (HTTP {e.status}).")

    @moderation.command(name="warn", description="Issue another warning to Gregor.")
    @database_operation(write=True)
    async def warn(self, interaction: discord.Interaction):
        try:
            user = interaction.user.id
            warns = self.bot.database.update_user_int(575710766787985435, 1, "warnings_received")
            _ = self.bot.database.update_user_int(user, 1, "warnings_issued")

            await interaction.response.send_message(f'<@575710766787985435> has been warned. This is warning **{warns}**!')
        except Exception as e:
            print(e)
            await interaction.response.send_message(f'Error occurred, upsi pupsi', ephemeral=True)

    @moderation.command(name="selftimeout", description="Timeout yourself for a specified number of minutes (1-10080).")
    @app_commands.describe(minutes="Number of minutes (1-10080) to timeout yourself")
    async def selftimeout(self, interaction: discord.Interaction, minutes: app_commands.Range[int, 1, 10080]):
        try:
            await interaction.user.timeout(timedelta(minutes=minutes))
            await interaction.response.send_message(f"{interaction.user} timed out for {minutes} minute{"s" if minutes > 1 else ""}.")

        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to timeout this user.")

        except discord.HTTPException as e:
            await interaction.response.send_message(f"Failed (HTTP {e.status}).")

async def setup(bot):
    await bot.add_cog(Moderation(bot))