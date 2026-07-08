"""SQLite 连接 + schema 初始化.

设计原则:
- 不引入 SQLAlchemy 这种重 ORM, 用 stdlib sqlite3 + Pydantic 验证就够了
- DB 文件就在 backend/jobs.db, gitignored
- 首次启动 (或主动调用 init_db) 会自动建表
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "jobs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    title         TEXT NOT NULL,
    company       TEXT NOT NULL,
    city          TEXT NOT NULL,
    category      TEXT NOT NULL,           -- developer/test/ai/pm/manager/other
    salary_min_k  INTEGER NOT NULL,
    salary_max_k  INTEGER NOT NULL,
    salary_text   TEXT NOT NULL,
    experience    TEXT NOT NULL,
    skills        TEXT NOT NULL,           -- JSON array of strings
    description   TEXT NOT NULL,
    source        TEXT NOT NULL DEFAULT 'manual',
    source_url    TEXT,
    posted_at     TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_jobs_city     ON jobs(city);
CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category);
"""


def get_conn() -> sqlite3.Connection:
    """每次调用返回新连接 (FastAPI 单请求生命周期内用一个)."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """幂等地创建表. 首次启动或 seed_jobs.py 都会调."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)
