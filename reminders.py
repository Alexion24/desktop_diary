import sqlite3
from contextlib import closing
from pathlib import Path


class ReminderStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS reminder_times (minute INTEGER PRIMARY KEY)")

    def load(self) -> list[int]:
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute("SELECT minute FROM reminder_times ORDER BY minute")
            return [minute for (minute,) in rows]

    def save(self, minutes: set[int]) -> None:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("DELETE FROM reminder_times")
            db.executemany(
                "INSERT INTO reminder_times (minute) VALUES (?)",
                [(minute,) for minute in minutes],
            )
