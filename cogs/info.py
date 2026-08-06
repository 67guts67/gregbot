import discord
from discord.ext import commands
from discord import app_commands

from bot import bot

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    info = app_commands.Group(
        name="info",
        description="..."
    )

    def help_message(self):
        description = []
        commandList = [commandGroup for commandGroup in self.bot.tree.get_commands() if
                       isinstance(commandGroup, app_commands.Group)]
        embed = discord.Embed(title="Commands", color=discord.Color.blurple())
        for iteration, group in enumerate(commandList):
            name = f"Slash command category: {group.name}"
            value = f"{
                "\n\n".join([

                    f" - {command.name}"

                    f"\n> Description: {command.description}"

                    f"{f"\n> Argument(s):\n{"\n".join([

                        f"> - `{parameter.name}`: {parameter.description}" for parameter in command.parameters

                    ])}" if len(command.parameters) > 0 else ""}"

                    for command in group.commands])}\n\n{'-' * 85}\n"

            embed.add_field(
                name=f"Slash command category: {group.name}",
                value=value,
                inline=False
            )

            description.append(f"{name}\n{value}")

        if self.bot.commands:
            name = f"Non slash commands (can be invoked using the `{self.bot.command_prefix}` prefix)"
            value = f"{"\n\n".join([
                    
                    f" - {command.name}"
                    f"\n> Description: {command.help}"
                    f"\n> Usage: {command.usage}"
                    
                    for command in self.bot.commands])}"
            embed.add_field(
                name=name,
                value=value,
                inline=False
            )

        embed.description = "\n\n\n".join(description)
        return embed

    '''
    @commands.command(name="help", help="Shows this message")
    async def prefix_help(self, ctx: commands.Context):
        await ctx.send(embed=self.help_message())
    '''

    @app_commands.command(name="help", description="Show commands")
    async def slash_help(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self.help_message())

    @info.command(name="whoami", description="Show information about GregBot.")
    async def whoami(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Username: **{bot.user.name}#{bot.user.discriminator}**\n"
            f"Display name: **{bot.user.display_name}**\n"
            f"ID: **{bot.user.id}**"
        )

    @info.command(name="author", description="Reveal GregBot's creators.")
    async def author(self, interaction: discord.Interaction):
        await interaction.response.send_message('''My father is <@627465945522241555>\nMy mother is <@575710766787985435>''')

    @info.command(name="serverinfo", description="Display information about the current Discord server.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild

        embed = discord.Embed(
            title=f"{guild.name}",
            color=discord.Color.blurple()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        owner = await bot.fetch_user(guild.owner_id)

        embed.add_field(name="Owner", value=owner.name, inline=True)
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(guild.created_at.timestamp())}:F>", inline=False)

        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(name="Bots", value=sum(member.bot for member in guild.members), inline=True)
        embed.add_field(name="Humans", value=sum(not member.bot for member in guild.members), inline=True)

        embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
        embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
        embed.add_field(name="Categories", value=len(guild.categories), inline=True)

        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)

        embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
        embed.add_field(name="Verification", value=str(guild.verification_level).title(), inline=True)
        embed.add_field(name="AFK Timeout", value=f"{guild.afk_timeout // 60} min", inline=True)

        embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Info(bot))
