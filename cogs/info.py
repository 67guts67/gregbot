import discord
from discord.ext import commands


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Reveal GregBot's creators.")
    async def author(self, ctx):
        await ctx.send('''My father is <@627465945522241555>\nMy mother is <@575710766787985435>''')

    @commands.command(help="Show information about GregBot.")
    async def whoami(self, ctx):
        await ctx.send(
            f"Username: **{self.bot.user.name}#{self.bot.user.discriminator}**\n"
            f"Display name: **{self.bot.user.display_name}**\n"
            f"ID: **{self.bot.user.id}**"
        )

    @commands.command(help="Display information about the current Discord server.")
    async def serverinfo(self,ctx):
        guild = ctx.guild

        embed = discord.Embed(
            title=f"{guild.name}",
            color=discord.Color.blurple()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        owner = await self.bot.fetch_user(guild.owner_id)

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

        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Info(bot))
