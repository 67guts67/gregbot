import turso.sync
from dotenv import load_dotenv
import os
from functools import wraps
from inspect import iscoroutinefunction

load_dotenv("secrets.env")
DB_DIR = "database"

def database_operation(write=False):
    def decorator(func):
        if iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                try:
                    result = await func(self, *args, **kwargs)

                    if write:
                        self.bot.database.db.commit()
                        self.bot.database.db.push()

                    return result

                except Exception:
                    if write:
                        self.bot.database.db.rollback()
                    raise

            return async_wrapper

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            try:
                result = func(self, *args, **kwargs)

                if write:
                    self.bot.database.db.commit()
                    self.bot.database.db.push()

                return result

            except Exception:
                if write:
                    self.bot.database.db.rollback()
                raise

        return sync_wrapper

    return decorator

class Database:
    def __init__(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self.db = turso.sync.connect(
            os.path.join(DB_DIR, "gregbot.db"),
            remote_url=os.getenv("TURSO_DATABASE_URL"),
            auth_token=os.getenv("TURSO_AUTH_TOKEN"),
        )

        self.db.pull()

        self.db.execute("BEGIN TRANSACTION")

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS orgs(
            orgCode TEXT PRIMARY KEY,
            nameEN TEXT,
            nameDE TEXT)
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS courses (
            courseNumber TEXT,
            semesterCode TEXT,
            courseType TEXT,
            titleEN TEXT,
            titleDE TEXT,
            instituteCode TEXT,
            PRIMARY KEY (courseNumber, semesterCode))
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS members (
            id TEXT PRIMARY KEY,
            huemerPoints INTEGER DEFAULT 0,
            warnings_received INTEGER DEFAULT 0,
            warnings_issued INTEGER DEFAULT 0,
            bans_received INTEGER DEFAULT 0,
            bans_issued INTEGER DEFAULT 0,
            rieners_received INTEGER DEFAULT 0,
            rieners_issued INTEGER DEFAULT 0,
            on_timeout INTEGER DEFAULT 0)
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS quotes (id TEXT PRIMARY KEY)
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS quotes (id INTEGER PRIMARY KEY)
        """)

        self.db.execute("""
            CREATE TABLE IF NOT EXISTS table_metadata(
            table_name TEXT PRIMARY KEY,
            last_updated DATETIME)
        """)

        for table in ["orgs", "courses"]:
            self.db.execute("""
                INSERT OR IGNORE INTO table_metadata 
                VALUES (?, DATETIME('now'))""",
                (table,))

            self.db.execute(f"""
                CREATE TRIGGER IF NOT EXISTS {table}_insert
                AFTER INSERT ON {table}
                BEGIN
                    INSERT OR REPLACE INTO table_metadata
                    (table_name, last_updated)
                    VALUES ('{table}', datetime('now'));
                END;
            """)

            self.db.execute(f"""
                CREATE TRIGGER IF NOT EXISTS {table}_update
                AFTER UPDATE ON {table}
                BEGIN
                    INSERT OR REPLACE INTO table_metadata
                    (table_name, last_updated)
                    VALUES ('{table}', datetime('now'));
                END;
            """)

        self.db.commit()
        self.db.push()
        print("Database ready", flush=True)

    def close(self):
        self.db.close()

    def get_columns(self, table_name, col_type):
        cols = self.db.execute("SELECT sql FROM sqlite_master WHERE name = (?)", (table_name, )).fetchone()[0]
        cols = cols[cols.find("(") + 1:cols.find(")")].split(", ")
        return [col.split(" ")[0] for col in cols if col.split(" ")[1] == col_type]

    # ====================== Tiss Org Functionality ======================


    # ====================== Discord Member Functionality ======================

    def check_user(self, memberID: int):
        self.db.execute(f"INSERT OR IGNORE INTO members (id) VALUES (?)", (memberID,))

    def update_user_int(self, memberID: int, points: int, category: str) -> None | int:
        self.check_user(memberID)
        if category not in self.get_columns("members", "INTEGER"):
            return None

        self.db.execute(f"UPDATE members SET {category} = {category} + (?) WHERE id = (?)", (points, memberID))
        return self.db.execute(f"SELECT {category} FROM members WHERE id = {memberID}").fetchone()[0]

    # ====================== Discord Quote Functionality ======================

    def add_quote(self, quote) -> None:
        self.db.execute("INSERT OR IGNORE INTO quotes (id) VALUES (?)", (quote,))

    def get_quote(self) -> str:
        return self.db.execute("SELECT * FROM quotes ORDER BY random() LIMIT 1").fetchone()[0]