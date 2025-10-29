from __future__ import annotations
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    homework_text: Optional[str] = None  # The actual homework assignment text
    source: Optional[str] = None
    # use a timezone-aware ISO8601 timestamp generated at instance-creation time
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class PageSnapshot:
    id: Optional[int]
    date: str  # YYYY-MM-DD
    html: str
    source: Optional[str] = None
    # use a timezone-aware ISO8601 timestamp generated at instance-creation time
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    parser_version: Optional[str] = None

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
                    homework_text TEXT,
                    source TEXT,
                    created_at TEXT NOT NULL
                );
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_homework_date ON homework(date);
            ''')
            # pages table for raw HTML snapshots & metadata
            conn.execute('''
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL UNIQUE,
                    html TEXT NOT NULL,
                    source TEXT,
                    fetched_at TEXT NOT NULL,
                    parser_version TEXT
                );
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_pages_date ON pages(date);
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
                        '''INSERT INTO homework(date, subject, description, due_date, homework_text, source, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (item.date, item.subject, item.description, item.due_date, item.homework_text, item.source, item.created_at)
                    )
                    count += 1
                except sqlite3.IntegrityError:
                    # already exists; skip
                    pass
            conn.commit()
        return count

    def list_by_date(self, date: str) -> List[HomeworkItem]:
        with self._connect() as conn:
            cur = conn.execute('SELECT id, date, subject, description, due_date, homework_text, source, created_at FROM homework WHERE date = ? ORDER BY subject', (date,))
            rows = cur.fetchall()
        return [HomeworkItem(*row) for row in rows]
    
    def list(self) -> List[HomeworkItem]:
        with self._connect() as conn:
            cur = conn.execute('SELECT id, date, subject, description, due_date, homework_text, source, created_at FROM homework ORDER BY date, subject', ())
            rows = cur.fetchall()
        return [HomeworkItem(*row) for row in rows]

    def latest_dates(self, limit: int = 7) -> list[str]:
        with self._connect() as conn:
            cur = conn.execute('SELECT DISTINCT date FROM homework ORDER BY date DESC LIMIT ?', (limit,))
            return [r[0] for r in cur.fetchall()]

    # ----- pages (raw HTML) helpers -----
    def save_page(self, date: str, html: str, source: Optional[str] = None, parser_version: Optional[str] = None) -> int:
        """Store raw HTML snapshot (upsert by date). Returns the row id."""
        fetched_at = datetime.utcnow().isoformat()
        with self._connect() as conn:
            # Use SQLite UPSERT to insert or update the snapshot for the date
            conn.execute('''
                INSERT INTO pages(date, html, source, fetched_at, parser_version)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(date) DO UPDATE SET
                    html=excluded.html,
                    source=excluded.source,
                    fetched_at=excluded.fetched_at,
                    parser_version=excluded.parser_version
            ''', (date, html, source, fetched_at, parser_version))
            conn.commit()
            cur = conn.execute('SELECT id FROM pages WHERE date = ?', (date,))
            row = cur.fetchone()
            return row[0] if row else -1

    def get_page_html(self, date: str) -> Optional[str]:
        """Return stored raw HTML for a given date, or None if not found."""
        with self._connect() as conn:
            cur = conn.execute('SELECT html FROM pages WHERE date = ?', (date,))
            row = cur.fetchone()
            return row[0] if row else None

    def list_pages(self, limit: int = 50) -> List[PageSnapshot]:
        """Return recent page snapshots ordered by date desc."""
        with self._connect() as conn:
            cur = conn.execute('SELECT id, date, html, source, fetched_at, parser_version FROM pages ORDER BY date DESC LIMIT ?', (limit,))
            rows = cur.fetchall()
        return [PageSnapshot(*row) for row in rows]
