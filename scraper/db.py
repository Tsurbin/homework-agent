from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

DB_PATH = Path(__file__).resolve().parents[1]/"data"/"homework.db"

@dataclass
class HomeworkItem:
    id: Optional[int]
    date: str  # YYYY-MM-DD
    subject: str
    description: str
    due_date: Optional[str] = None  # YYYY-MM-DD
    source: Optional[str] = None
    created_at: str = datetime.utcnow().isoformat()

class HomeworkDB:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else DB_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init(self) -> None:
        with self._connect() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS homework (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    description TEXT NOT NULL,
                    due_date TEXT,
                    source TEXT,
                    created_at TEXT NOT NULL
                );
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_homework_date ON homework(date);
            ''')
            conn.commit()

    def upsert_items(self, items: Iterable[HomeworkItem]) -> int:
        # naive dedup: date+subject+description unique
        count = 0
        with self._connect() as conn:
            conn.execute('''
                CREATE UNIQUE INDEX IF NOT EXISTS uq_homework ON homework(date, subject, description);
            ''')
            for item in items:
                try:
                    conn.execute(
                        '''INSERT INTO homework(date, subject, description, due_date, source, created_at)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        (item.date, item.subject, item.description, item.due_date, item.source, item.created_at)
                    )
                    count += 1
                except sqlite3.IntegrityError:
                    # already exists; skip
                    pass
            conn.commit()
        return count

    def list_by_date(self, date: str) -> List[HomeworkItem]:
        with self._connect() as conn:
            cur = conn.execute('SELECT id, date, subject, description, due_date, source, created_at FROM homework WHERE date = ? ORDER BY subject', (date,))
            rows = cur.fetchall()
        return [HomeworkItem(*row) for row in rows]

    def latest_dates(self, limit: int = 7) -> list[str]:
        with self._connect() as conn:
            cur = conn.execute('SELECT DISTINCT date FROM homework ORDER BY date DESC LIMIT ?', (limit,))
            return [r[0] for r in cur.fetchall()]
