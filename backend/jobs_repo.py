"""Job 表的 CRUD 封装. 所有访问 jobs 表的代码都从这里走.

设计原则:
- 不写 ORM, 直接 SQL + Pydantic 验证
- 查询函数返回 list[Job], 不暴露 sqlite3.Row
- 写入时 skills 字段自动 JSON 序列化, 读取时反序列化
"""
import json
from typing import Iterable

from db import get_conn
from models import Job, JobCategory


def _row_to_job(row) -> Job:
    return Job(
        id=row["id"],
        title=row["title"],
        company=row["company"],
        city=row["city"],
        category=JobCategory(row["category"]),
        salary_min_k=row["salary_min_k"],
        salary_max_k=row["salary_max_k"],
        salary_text=row["salary_text"],
        experience=row["experience"],
        skills=json.loads(row["skills"]),
        description=row["description"],
        source=row["source"],
        source_url=row["source_url"],
        posted_at=row["posted_at"],
    )


def list_jobs(
    city: str | None = None,
    categories: Iterable[JobCategory] | None = None,
    limit: int = 200,
) -> list[Job]:
    """通用查询. 按 city 精确匹配, 按 categories 在集合内匹配."""
    sql = "SELECT * FROM jobs WHERE 1=1"
    params: list = []
    if city:
        sql += " AND city = ?"
        params.append(city)
    if categories:
        cat_list = [c.value for c in categories]
        placeholders = ",".join("?" * len(cat_list))
        sql += f" AND category IN ({placeholders})"
        params.extend(cat_list)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_row_to_job(r) for r in rows]


def insert_job(job: Job) -> int:
    """插入一行, 返回新 id."""
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO jobs (
                title, company, city, category,
                salary_min_k, salary_max_k, salary_text,
                experience, skills, description,
                source, source_url, posted_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                job.title, job.company, job.city, job.category.value,
                job.salary_min_k, job.salary_max_k, job.salary_text,
                job.experience, json.dumps(job.skills, ensure_ascii=False), job.description,
                job.source, job.source_url, job.posted_at,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def count_jobs() -> int:
    with get_conn() as conn:
        return int(conn.execute("SELECT COUNT(*) AS c FROM jobs").fetchone()["c"])


def clear_jobs() -> None:
    """种子脚本会用. 谨慎."""
    with get_conn() as conn:
        conn.execute("DELETE FROM jobs")
        conn.commit()
