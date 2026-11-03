import aiohttp
import discord
from discord.ext import commands
from discord import app_commands

from config import SEMESTER_MATCH

from services.tiss import tiss_psearch, clean_html, tiss_csearch, build_picture_url, tiss_course, \
    tiss_exam_dates, format_exam_block, truncate, CourseInfo, tiss_courses, tiss_oidsearch

from markdownify import markdownify as md

class LanguageButton(discord.ui.Button):
    def __init__(self, language, label, menu: CourseMenu):
        self.menu = menu
        self.language = language
        super().__init__(label=label)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.menu.updateLanguage(self.language, interaction)

class DeleteButton(discord.ui.Button):
    def __init__(self, language: str):
        label = "Delete" if language == "english" else "Löschen"
        super().__init__(label=label, style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            await interaction.delete_original_response()
        except Exception as e:
            print(e, flush=True)

class CourseSelector(discord.ui.Select):
    def __init__(self, courses: dict[str, CourseInfo], language: str, menu: CourseMenu):
        self.courses = courses
        self.menu = menu
        options = [
            discord.SelectOption(label=f"{course["title"][language]} {course["courseType"]} {course["semesterCode"]}",
                                 value=course["courseNumber"])
            for key, course in courses.items()
        ]

        super().__init__(
            placeholder="Please select a course",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await self.menu.updateCourse(self.values[0], interaction)

class CourseMenu:
    def __init__(self, courses: dict[str, CourseInfo], session: aiohttp.ClientSession):
        super().__init__()
        self.language = "english"
        self.course: CourseInfo | None = None
        self.courses: dict[str, CourseInfo] = courses
        self.session = session

        if len(list(courses.keys())) == 1:
            self.course = courses.pop(list(courses.keys())[0])

    async def updateCourse(self, key: str, interaction: discord.Interaction):
        self.course = self.courses.get(key)
        await self.updateEmbed(interaction, True)

    async def updateLanguage(self, language: str, interaction: discord.Interaction):
        self.language = language
        await self.updateEmbed(interaction, True)

    async def updateEmbed(self, interaction: discord.Interaction, edit: bool):
        menu = discord.ui.View(timeout=60.0)
        if len(list(self.courses.keys())) > 1:
            menu.add_item(CourseSelector(self.courses, self.language, menu=self))
        menu.add_item(LanguageButton(language="german",
                                     label={"english": "German", "german": "Deutsch"}.get(self.language),
                                     menu=self))
        menu.add_item(LanguageButton(language="english",
                                     label={"english": "English", "german": "Englisch"}.get(self.language),
                                     menu=self))
        menu.add_item(DeleteButton(language=self.language))

        if self.course:
            embed = await courseEmbed(self.session, self.course, self.language)
            await interaction.edit_original_response(embed=embed, view=menu)
        else:
            if edit:
                await interaction.edit_original_response(view=menu)
            else:
                await interaction.followup.send(view=menu)

        return None

async def courseEmbed(session: aiohttp.ClientSession, course_info: CourseInfo, language: str):
    exam_dates = await tiss_exam_dates(session, course_info["courseNumber"])

    embed = discord.Embed(
        title=course_info["title"][language],
        url=course_info["url"] if course_info["url"] != "N/A" else None,
        description=(
            f"`{course_info['courseNumber']}` · **{course_info['courseType']}** · "
            f"{course_info['weeklyHours']}h/week · {course_info['language']} · "
            f"{course_info['semesterCode']}"
        ),
        color=discord.Color.red()
    )

    embed.add_field(name="Institute", value=f"[{course_info["institute"][language]}](https://tiss.tuwien.ac.at/adressbuch/adressbuch/orgeinheit_via_nummer/{course_info["instituteCode"]})", inline=True)
    embed.add_field(name="Registration", value=course_info["registration"], inline=True)
    embed.add_field(name="\u200b", value="\u200b", inline=True)

    if course_info["objective"]:
        embed.add_field(
            name="Objective",
            value=truncate(md(course_info["objective"][language].replace("}{TU Maps}", "")), 1024),
            inline=False
        )

    if course_info["examinationModalities"]:
        embed.add_field(
            name="Examination Modalities",
            value=truncate(md(course_info["examinationModalities"][language].replace("}{TU Maps}", "")), 1024),
            inline=False
        )

    if course_info["additionalInformation"]:
        embed.add_field(
            name="Additional Information",
            value=truncate(md(course_info["additionalInformation"][language].replace("}{TU Maps}", "")), 1024),
            inline=False
        )

    if course_info["lectures"]:
        lectures = ""
        endOfList = "\n - ..."
        addEnd = False
        for iteration, lecturer in enumerate(course_info["lectures"]):
            person = await tiss_oidsearch(session, lecturer)
            if person:
                newLectures = f"\n - [{person.get("first_name")} {person.get("last_name")}](https://tiss.tuwien.ac.at/adressbuch/adressbuch/person/{person.get("tiss_id")})"
                if len(lectures) + len(lecturer) > 1024:
                    addEnd = True
                    continue
                elif len(lectures) + len(lecturer) > 1024 - len(endOfList) and iteration < len(
                        course_info["lectures"]) - 1:
                    addEnd = True
                    continue
                else:
                    lectures += newLectures

        if addEnd:
            lectures += endOfList

        embed.add_field(
            name="Lecture(s)",
            value=lectures,
            inline=False
        )

    if exam_dates:
        embed.add_field(
            name="Exam Dates",
            value=format_exam_block(exam_dates),
            inline=False
        )

    return embed

class Tiss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    tiss = app_commands.Group(
        name="tiss",
        description="..."
    )

    @tiss.command(name="psearch", description="Search a person per TISS.")
    @app_commands.describe(person="The name of the person")
    async def psearch(self, interaction: discord.Interaction, person: str):
        await interaction.response.defer()

        if person is None:
            await interaction.followup.send("No person provided.")
            return

        query = person
        person = await tiss_psearch(self.bot.http_session, query)
        if person is None:
            await interaction.followup.send(f"No person found matching `{query}`.")
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

        await interaction.followup.send(embed=embed)

    @tiss.command(description="Search courses per TISS.")
    @app_commands.describe(course="The name|oid of the course - Example: 1113253 or Franz Puntigam")
    @app_commands.describe(semester="The semester of the course - Example: 2026S")
    async def csearch(self, interaction: discord.Interaction, course: str, semester: str):
        if not SEMESTER_MATCH.match(semester):
            await interaction.response.send_message("Invalid semester.")
            return

        await interaction.response.defer()

        target = course

        person = None

        if target.isdigit():
            oid = int(target)
        else:
            person = await tiss_psearch(self.bot.http_session, target)
            if person is None:
                await interaction.followup.send(f"No lecturer found matching `{target}`.")
                return
            oid = person["oid"]

        courses = await tiss_csearch(self.bot.http_session, oid, semester)

        if not courses:
            await interaction.followup.send(f"No courses found for `{target}` in semester `{semester}`.")
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

        await interaction.followup.send(embed=embed)

    @tiss.command(name="course", description="Get course details and exam dates.")
    @app_commands.describe(name="The name of the course - Example: Einführung in die Programmierung 1")
    async def course(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        matches: dict[str, CourseInfo] = await tiss_course(self.bot.http_session, name)

        print(f"Number of matches: {len(matches.keys())}", flush=True)

        if len(matches.keys()) >= 1:
            try:
                courseMenu = CourseMenu(matches, self.bot.http_session)
                await courseMenu.updateEmbed(interaction, False)

            except Exception as e:
                print(e, flush=True)

        else:
            await interaction.followup.send("No course has been found")

    @tiss.command(name="cache", description="Fetches all courses if not already cached.")
    async def cache(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        courses = await tiss_courses(self.bot.http_session)
        await interaction.followup.send(f"{len(courses.keys())} courses cached.")

async def setup(bot):
    await bot.add_cog(Tiss(bot))