import html
import re
from datetime import datetime, timezone

import aiohttp
import xml.etree.ElementTree as ET
from urllib.parse import quote

from config import BASE_URL, PSEARCH
from services.tiss_cache import tiss_cache


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
async def tiss_course(session: aiohttp.ClientSession, number: str, semester: str) -> dict | None:
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