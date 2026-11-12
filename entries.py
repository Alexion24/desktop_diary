import sqlite3
from calendar import monthrange
from contextlib import closing
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Entry:
    feelings: str = ""
    methods: str = ""
    notes: str = ""


class EntryStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS diary_entries (
                    day TEXT NOT NULL PRIMARY KEY,
                    feelings TEXT NOT NULL,
                    methods TEXT NOT NULL,
                    notes TEXT NOT NULL
                )
            """)

    def load(self, day: date) -> Entry:
        with closing(sqlite3.connect(self.path)) as db:
            row = db.execute(
                "SELECT feelings, methods, notes FROM diary_entries WHERE day = ?",
                (day.isoformat(),),
            ).fetchone()
        return Entry(*row) if row is not None else Entry()

    def save(self, day: date, entry: Entry) -> None:
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("""
                INSERT INTO diary_entries (day, feelings, methods, notes)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(day) DO UPDATE SET
                    feelings = excluded.feelings,
                    methods = excluded.methods,
                    notes = excluded.notes
            """, (day.isoformat(), entry.feelings, entry.methods, entry.notes))

    def load_month(self, year: int, month: int) -> list[tuple[date, Entry]]:
        first = date(year, month, 1)
        last = date(year, month, monthrange(year, month)[1])
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute(
                """
                SELECT day, feelings, methods, notes
                FROM diary_entries
                WHERE day BETWEEN ? AND ?
                ORDER BY day
                """,
                (first.isoformat(), last.isoformat()),
            )
            return [
                (date.fromisoformat(day), Entry(feelings, methods, notes))
                for day, feelings, methods, notes in rows
            ]
