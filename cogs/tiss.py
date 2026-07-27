import asyncio

import discord
from discord.ext import commands

from services.tiss import tiss_psearch, clean_html, tiss_csearch, build_picture_url, tiss_course, \
    tiss_exam_dates, format_exam_block, truncate


class Tiss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(help="Search a person per TISS")
    async def psearch(self, ctx, *, person: str = None):

        if person is None:
            await ctx.send("No person provided.")
            return

        query = person
        person = await tiss_psearch(self.bot.http_session, query)
        if person is None:
            await ctx.send(f"No person found matching `{query}`.")
            return

        embed = discord.Embed(
            title=f"{person['first_name']} {person['last_name']}",
            url=f"https://tiss.tuwien.ac.at{person['card_uri']}",
            description=person.get("preceding_titles"),
            color=discord.Color.red()
        )

        employee = person["employee"][0]
        room = employee.get("room")

        embed.add_field(
            name="Department",
            value=employee["org_ref"]["name_en"],
            inline=False
        )

        embed.add_field(
            name="Position",
            value=employee.get("display_function", "N/A"),
            inline=True
        )

        embed.add_field(
            name="Contact",
            value=(
                f"{person.get('main_email', 'N/A')}\n"
                f"{person.get('main_phone_number', 'N/A')}"
            ),
            inline=False
        )

        if room:
            address = room.get("address", {})

            embed.add_field(
                name="Office",
                value=(
                    f"{room.get('room_code', 'N/A')}\n"
                    f"{address.get('street', '')}\n"
                    f"{address.get('zip_code', '')} {address.get('city', '')}"
                ),
                inline=False
            )

        if person.get("consultation_hours"):
            embed.add_field(
                name="Consultation Hours",
                value=clean_html(person["consultation_hours"][0]),
                inline=False
            )

        if person.get("picture_uri"):
            embed.set_thumbnail(
                url=f"https://tiss.tuwien.ac.at{person['picture_uri']}"
            )

        embed.set_footer(
            text=f"TISS ID: {person['tiss_id']}"
        )

        await ctx.send(embed=embed)

    @commands.command(help="Search courses per TISS. Usage: ^csearch <oid|name> <semester>")
    async def csearch(self, ctx, *, args: str = None):
        if not args:
            await ctx.send(
                "Usage: `^csearch <oid|name> <semester>`\n"
                "Example: `^csearch 1113253 2026S` or `^csearch Franz Puntigam 2026S`"
            )
            return

        parts = args.rsplit(" ", 1)
        if len(parts) != 2:
            await ctx.send(
                "Usage: `^csearch <oid|name> <semester>`\n"
                "Example: `^csearch 1113253 2026S` or `^csearch Franz Puntigam 2026S`"
            )
            return

        target, semester = parts
        target = target.strip()

        person = None

        if target.isdigit():
            oid = int(target)
        else:
            person = await tiss_psearch(self.bot.http_session, target)
            if person is None:
                await ctx.send(f"No lecturer found matching `{target}`.")
                return
            oid = person["oid"]

        courses = await tiss_csearch(self.bot.http_session, oid, semester)

        if not courses:
            await ctx.send(f"No courses found for `{target}` in semester `{semester}`.")
            return

        display_name = f"{person['first_name']} {person['last_name']}" if person else str(oid)
        picture_url = build_picture_url(person.get("picture_uri")) if person else None

        embed = discord.Embed(
            title=f"Courses for {display_name} ({semester})",
            color=discord.Color.red()
        )
        if picture_url:
            embed.set_thumbnail(url=picture_url)

        MAX_FIELDS = 25
        shown = courses[:MAX_FIELDS]

        for course in shown:
            name = f"{course['title']} — {course['number']} ({course['type']})"
            value = (
                f"{course['hours']} hours/week\n"
                f"{course['institute']}\n"
                f"Language: {course['language']}\n"
                f"[TISS Link]({course['url']})"
            )
            embed.add_field(name=name[:256], value=value[:1024], inline=False)

        if len(courses) > MAX_FIELDS:
            embed.set_footer(text=f"Showing {MAX_FIELDS} of {len(courses)} courses")

        await ctx.send(embed=embed)

    @commands.command(help="Get course details and exam dates. Usage: ^course <number> <semester>")
    async def course(self, ctx, number: str = None, semester: str = None):
        if not number or not semester:
            await ctx.send("Usage: `^course <number> <semester>`\nExample: `^course 192134 2026W`")
            return

        course_info, exam_dates = await asyncio.gather(
            tiss_course(self.bot.http_session, number, semester),
            tiss_exam_dates(self.bot.http_session, number),
        )

        if course_info is None:
            await ctx.send(f"No course found for `{number}` in semester `{semester}`.")
            return

        embed = discord.Embed(
            title=course_info["title"],
            url=course_info["url"] if course_info["url"] != "N/A" else None,
            description=(
                f"`{course_info['number']}` · **{course_info['type']}** · "
                f"{course_info['hours']}h/week · {course_info['language']} · "
                f"{semester}"
            ),
            color=discord.Color.red()
        )

        embed.add_field(name="Institute", value=course_info["institute"], inline=True)
        embed.add_field(name="Registration", value=course_info["registration"], inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)

        if course_info["objective"]:
            embed.add_field(
                name="Objective",
                value=truncate(course_info["objective"], 500),
                inline=False
            )

        if course_info["examination_modalities"]:
            embed.add_field(
                name="Examination Modalities",
                value=truncate(course_info["examination_modalities"], 500),
                inline=False
            )

        embed.add_field(
            name="Exam Dates",
            value=format_exam_block(exam_dates),
            inline=False
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Tiss(bot))