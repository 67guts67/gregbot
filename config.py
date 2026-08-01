import re

# moderation.py
GREGOR_ID = 575710766787985435
MAX_PURGE = 100
MESSAGE_LINK_RE = re.compile(
    r"https://(?:canary\.)?discord(?:app)?\.com/channels/\d+/(\d+)/(\d+)"
)
GREGOR_WARNS = 0

ALLOWED_ROLE_IDS = {
    1438155180171595786,  # Zeichenspiele
    1444330125347782717,  # Minecraft
    1444330248031178822,  # League
    1444330309200908551,  # Friendslop
    1444330436858744946,  # Mario Kart
    1503123095760666644,  # repo
    1521817122131673088,  # test
    1499383073320472586   # unemploymentsquad
}

QUOTE_CHANNEL_ID = 1286299111238271028

GUTS_ID = 627465945522241555

TYPE_TO_GET_BANNED_ID = 1521583642609188895

#tiss.py
BASE_URL = "https://tiss.tuwien.ac.at"
#tiss api endpoints
PSEARCH = "/api/person/v23/psuche"

CSEARCH = "/api/course/lecturer/"

SEMESTER_MATCH = re.compile(
    r"\d{4}([WS])$"
)
