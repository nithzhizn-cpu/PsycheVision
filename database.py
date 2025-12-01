
import sqlite3
from datetime import datetime

DB_PATH = "PsycheVision.db"

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cur = self.conn.cursor()
        self._init_schema()

    def _init_schema(self):
        self.cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                test_id TEXT,
                test_title TEXT,
                raw_score REAL,
                level TEXT,
                summary TEXT,
                meta_json TEXT,
                created_at TEXT
            )
            '''
        )
        self.conn.commit()

    def save_result(self, user_id, username, test_id, test_title, raw_score, level, summary, meta_json="{}"):
        created_at = datetime.utcnow().isoformat()
        self.cur.execute(
            "INSERT INTO results (user_id, username, test_id, test_title, raw_score, level, summary, meta_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, test_id, test_title, raw_score, level, summary, meta_json, created_at),
        )
        self.conn.commit()

    def get_user_results(self, user_id, limit=50):
        rows = self.cur.execute(
            "SELECT * FROM results WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]
