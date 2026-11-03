import html
import re
from datetime import datetime, timezone

import aiohttp
import xml.etree.ElementTree as ET
from urllib.parse import quote

from config import BASE_URL, PSEARCH
from services.tiss_cache import tiss_cache

from typing import TypedDict

class Languages(TypedDict):
    german: str
    english: str

class CourseInfo(TypedDict):
    """
    Represents a Tiss course returned from the Tiss API.
    Attributes
    ---
    courseNumber
    semesterCode
    courseType
    title
    lectures
    objective
    teachingContent
    additionalInformation
    lectureNotes
    examinationModalities
    recommendation
    weeklyHours
    registration
    url
    institute
    instituteCode
    """
    courseNumber: str
    semesterCode: str
    courseType: str
    title: Languages
    lectures: list[str]
    objective: Languages
    teachingContent: Languages
    additionalInformation: Languages
    lectureNotes: Languages
    examinationModalities: Languages
    recommendation: Languages
    weeklyHours: str
    registration: str
    language: str
    url: str
    institute: Languages
    instituteCode: str

class Person(TypedDict):
    """
    Represents a Tiss person returned from the Tiss API.
    Attributes
    ---
    tiss_id
    oid
    first_name
    last_name
    """
    tiss_id: str
    oid: str
    first_name: str
    last_name: str

@tiss_cache.cached(ttl=60 * 60 * 24, miss_ttl=60 * 5)
async def tiss_oidsearch(session: aiohttp.ClientSession, oid) -> Person | None:
    url = f"https://tiss.tuwien.ac.at/api/person/v23/oid/{oid}"

    async with session.get(url) as response:
        if response.status != 200:
            return None
        data = await response.json()

    return data

@tiss_cache.cached(ttl=60 * 60 * 24, miss_ttl=60 * 5)
async def tiss_psearch(session: aiohttp.ClientSession, name: str):
    url = BASE_URL + PSEARCH + "?q=" + quote(name)

    async with session.get(url) as response:
        if response.status != 200:
            return None
        data = await response.json()

    results = data.get("results", [])
    return results[0] if results else None

@tiss_cache.cached(ttl=60 * 60 * 24, miss_ttl=60 * 5)
async def tiss_csearch(session: aiohttp.ClientSession, oid: int, semester: str) -> list[dict]:
    url = f"https://tiss.tuwien.ac.at/api/course/lecturer/{oid}/?semester={semester}"

    async with session.get(url) as response:
        if response.status != 200:
            return []
        xml_text = await response.text()

    root = ET.fromstring(xml_text)

    courses = []

    for course in root.findall("{*}course"):

        def text(tag: str, default: str = "N/A") -> str:
            el = course.find(f"{{*}}{tag}")
            return el.text.strip() if el is not None and el.text else default

        courses.append({
            "number": text("courseNumber"),
            "type": text("courseType"),
            "title": course.findtext("{*}title/{*}en", default="N/A"),
            "hours": text("weeklyHours"),
            "url": text("url"),
            "registration": text("registration"),
            "institute": course.findtext("{*}instituteName/{*}en", default="N/A"),
            "language": course.findtext("{*}language/{*}en", default="N/A"),
        })

    return courses

@tiss_cache.cached(ttl=60 * 60 * 24, miss_ttl=60 * 5)
async def tiss_course(session: aiohttp.ClientSession, name: str) -> dict[str, CourseInfo]:
    matches = {}
    courses: dict[str, CourseInfo] = await tiss_courses(session)
    for cNr, course in courses.items():
        if course["title"].get("english") == name or course["title"].get("german") == name:
            matches[cNr] = course

    return matches

    '''
    url = f"https://tiss.tuwien.ac.at/api/course/{number}-{semester}"

    async with session.get(url) as response:
        if response.status != 200:
            return None
        xml_text = await response.text()

    root = ET.fromstring(xml_text)
    course = root.find("{*}course")
    if course is None:
        return None

    def text(tag: str, default: str = "N/A") -> str:
        el = course.find(f"{{*}}{tag}")
        return el.text.strip() if el is not None and el.text else default

    return {
        "number": text("courseNumber"),
        "semester": text("semesterCode"),
        "type": text("courseType"),
        "title": course.findtext("{*}title/{*}en", default="N/A"),
        "objective": clean_html(course.findtext("{*}objective/{*}en", default="")),
        "teaching_content": clean_html(course.findtext("{*}teachingContent/{*}en", default="")),
        "examination_modalities": clean_html(course.findtext("{*}examinationModalities/{*}en", default="")),
        "hours": text("weeklyHours"),
        "url": text("url"),
        "registration": text("registration"),
        "institute": course.findtext("{*}instituteName/{*}en", default="N/A"),
        "language": course.findtext("{*}language/{*}en", default="N/A"),
    }
    '''

@tiss_cache.cached(ttl=60 * 60 * 24, miss_ttl=60 * 5)
async def tiss_exam_dates(session: aiohttp.ClientSession, number: str) -> list[dict]:
    url = f"https://tiss.tuwien.ac.at/api/course/{number}/examDates"

    async with session.get(url) as response:
        if response.status != 200:
            return []
        xml_text = await response.text()

    root = ET.fromstring(xml_text)
    exams = []

    for exam in root.findall("{*}exam"):

        def text(tag: str, default: str = "N/A") -> str:
            el = exam.find(f"{{*}}{tag}")
            return el.text.strip() if el is not None and el.text else default

        exams.append({
            "id": exam.get("id"),
            "title": text("title"),
            "examination_begin": text("examinationBegin"),
            "application_end": text("applicationEnd"),
            "deregistration_end": text("deregistrationEnd"),
        })

    return exams

@tiss_cache.cached(ttl=60 * 60 * 24, miss_ttl=60 * 5)
async def tiss_orgs(session: aiohttp.ClientSession) -> list[str]:
    def findIns(item) -> list[str]:
        if item.get("type") == "INS":
            return [item.get("code")]
        codes: list[str] = []
        if "children" in item:
            for child in item.get("children"):
                codes += findIns(child)
        return codes

    url = f"https://tiss.tuwien.ac.at/api/orgunit/v23/organigramm"

    async with session.get(url) as response:
        if response.status != 200:
            print(response)
        body = await response.json()

    return findIns(body)

@tiss_cache.cached(ttl=60 * 60 * 24, miss_ttl=60 * 5)
async def tiss_courses(session: aiohttp.ClientSession) -> dict[str, CourseInfo]:
    print("Fetching orgs", flush=True)
    orgs = await tiss_orgs(session)
    print(f"Fetched {len(orgs)} orgs\n\n", flush=True)

    coursesDict: dict[str, CourseInfo] = {}

    courseCount = 0

    for iteration, org in enumerate(orgs):
        orgUrl = f"https://tiss.tuwien.ac.at/api/course/orgUnit/{org}"

        print(f"Fetching {orgUrl}", flush=True)
        async with session.get(orgUrl) as response:
            if response.status != 200:
                print(response, flush=True)
            courses = await response.text()

        print(f"Fetched {orgUrl} ({iteration + 1}/{len(orgs)})", flush=True)

        root = ET.fromstring(courses)

        for course in root.findall("{*}course"):
            cNr = course.findtext("{*}courseNumber")
            if cNr:
                coursesDict[cNr] = {
                    "courseNumber": course.findtext("{*}courseNumber", default = "N/A"),
                    "semesterCode": course.findtext("{*}semesterCode", default = "N/A"),
                    "courseType": course.findtext("{*}courseType", default = "N/A"),
                    "title": {"german": course.findtext("{*}title/{*}de", default = "N/A"),
                              "english": course.findtext("{*}title/{*}en", default = "N/A")},
                    "lectures": [lecturers.text for lecturers in course.findall("{*}lecturers/{*}oid") if lecturers.text is not None],
                    "objective": {"german": course.findtext("{*}objective/{*}de", default = "N/A"),
                                "english": course.findtext("{*}objective/{*}en", default = "N/A")},
                    "teachingContent": {"german": course.findtext("{*}teachingContent/{*}de", default = "N/A"),
                                        "english": course.findtext("{*}teachingContent/{*}en", default = "N/A")},
                    "additionalInformation": {"german": course.findtext("{*}additionalInformation/{*}de", default = "N/A"),
                                              "english": course.findtext("{*}additionalInformation/{*}en", default = "N/A")},
                    "lectureNotes": {"german": course.findtext("{*}lectureNotes/{*}de", default = "N/A"),
                                     "english": course.findtext("{*}lectureNotes/{*}en", default = "N/A")},
                    "examinationModalities": {"german": course.findtext("{*}examinationModalities/{*}de", default = "N/A"),
                                              "english": course.findtext("{*}examinationModalities/{*}en", default = "N/A")},
                    "recommendation": {"german": course.findtext("{*}related/{*}recommendation/{*}de", default = "N/A"),
                                       "english": course.findtext("{*}related/{*}recommendation/{*}en", default = "N/A")},
                    "weeklyHours": course.findtext("{*}weeklyHours", default = "N/A"),
                    "registration": course.findtext("{*}registration", default = "N/A"),
                    "language": course.findtext("{*}language", default = "N/A"),
                    "url": course.findtext("{*}url", default = "N/A"),
                    "institute": {"german": course.findtext("{*}instituteName/{*}en", default = "N/A"),
                                  "english": course.findtext("{*}instituteName/{*}en", default = "N/A")},
                    "instituteCode": course.findtext("{*}instituteCode", default = "N/A")
                }

        print(f"{len(coursesDict.keys()) - courseCount} courses cached.", flush=True)

    return coursesDict

def format_exam_date(iso_str: str) -> str:
    if not iso_str or iso_str == "N/A":
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d.%m.%Y %H:%M")
    except ValueError:
        return iso_str


def clean_html(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", html.unescape(text)).strip()


def build_picture_url(picture_uri: str | None) -> str | None:
    if not picture_uri:
        return None
    return BASE_URL + picture_uri


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def parse_tiss_datetime(iso_str: str) -> datetime | None:
    if not iso_str or iso_str == "N/A":
        return None
    try:
        return datetime.fromisoformat(iso_str)
    except ValueError:
        return None


def clean_exam_title(title: str) -> str:
    return re.sub(r"\s*\(\d{4}-\d{2}-\d{2}\)\s*$", "", title).strip()


def format_exam_block(exams: list[dict]) -> str:
    if not exams:
        return "No exam dates found."

    now = datetime.now(timezone.utc)
    lines = []

    for exam in exams:
        dt = parse_tiss_datetime(exam["examination_begin"])
        date_str = dt.strftime("%d.%m.%Y %H:%M") if dt else "date TBD"

        deadline_dt = parse_tiss_datetime(exam["application_end"])
        deadline_str = deadline_dt.strftime("%d.%m.%Y") if deadline_dt else "N/A"

        title = clean_exam_title(exam["title"])
        is_past = dt is not None and dt < now

        if is_past:
            lines.append(f"~~{title}~~ — {date_str} (past)")
            continue

        lines.append(f"{title} — {date_str}\nRegistration closes {deadline_str}")

    text = "\n\n".join(lines)
    return truncate(text, 1024)