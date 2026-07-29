"""FastAPI 入口.

启动: uvicorn main:app --reload --port 8000
"""
import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from models import UserProfile, CareerReport, TestCase, Job, JobCategory, PersonaAnalysis
from orchestrator import run_career_twin
from db import init_db
from jobs_repo import list_jobs, count_jobs
from agents.persona import analyze_persona
from agents.market import debug_retrieve

TEST_CASES_DIR = Path(__file__).parent.parent / "test-cases"

# 首次启动自动建表 (幂等).
init_db()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="Career Twin", version="0.1.0")

# CORS 来源可通过环境变量覆盖 (逗号分隔). 部署后前端走 Next.js rewrite 代理,
# 浏览器只跟 Vercel 域名通信, 本不触发 CORS; 但若有人直连后端 API, 这层就有用.
# 例: CORS_ORIGINS="https://career-twin.vercel.app,https://mydomain.com"
_default_origins = "http://localhost:3000"
_origins_env = os.getenv("CORS_ORIGINS", _default_origins)
_allow_origins = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/api/career-twin", response_model=CareerReport)
def career_twin(profile: UserProfile) -> CareerReport:
    try:
        return run_career_twin(profile)
    except Exception as e:
        logging.exception("career_twin failed")
        raise HTTPException(status_code=500, detail=str(e))


# 一个调试入口: 不调 LLM, 只验证整条数据通路
DEFAULT_PROFILE = UserProfile(
    age=47,
    role="测试经理",
    role_category=JobCategory.MANAGER,
    industry="互联网电视",
    city="青岛",
    family="两个孩子",
    mortgage_wan=60,
    current_monthly_salary_k=30,
    expectation="尽量保持收入",
)


@app.get("/api/default-profile", response_model=UserProfile)
def default_profile() -> UserProfile:
    """返回默认画像, 给前端做占位."""
    return DEFAULT_PROFILE


@app.get("/api/test-cases", response_model=list[TestCase])
def list_test_cases() -> list[TestCase]:
    """列出 test-cases/ 文件夹下所有压力测试画像. 按文件名排序."""
    if not TEST_CASES_DIR.exists():
        return []
    cases: list[TestCase] = []
    for path in sorted(TEST_CASES_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as f:
            cases.append(TestCase.model_validate(json.load(f)))
    return cases


# ---------- 岗位库接口 (Stage 3) ----------

@app.get("/api/jobs", response_model=list[Job])
def get_jobs(
    city: str | None = None,
    category: JobCategory | None = None,
    limit: int = 200,
) -> list[Job]:
    """列出岗位库所有岗位, 支持按城市和分类过滤."""
    categories = [category] if category else None
    return list_jobs(city=city, categories=categories, limit=limit)


@app.get("/api/jobs/stats")
def jobs_stats() -> dict:
    """岗位库的元数据 (总数 + 各分类计数), 给前端 /jobs 页面顶部展示."""
    all_jobs = list_jobs(limit=10000)
    by_cat: dict[str, int] = {}
    by_city: dict[str, int] = {}
    for j in all_jobs:
        by_cat[j.category.value] = by_cat.get(j.category.value, 0) + 1
        by_city[j.city] = by_city.get(j.city, 0) + 1
    return {
        "total": count_jobs(),
        "by_category": by_cat,
        "by_city": by_city,
    }


# ---------- RAG 调试接口 (Stage 4) ----------

class RetrieveRequest(BaseModel):
    profile: UserProfile
    k: int = 10


@app.post("/api/debug/retrieve")
def debug_retrieve_endpoint(req: RetrieveRequest) -> dict:
    """**不调 LLM**, 只跑 RAG 检索, 看看用这个画像能召回哪些岗位.

    用法: 前端按"查看检索结果"按钮调这个, 调试 RAG 质量很有用.
    """
    try:
        persona = analyze_persona(req.profile)
        return debug_retrieve(req.profile, persona, k=req.k)
    except Exception as e:
        logging.exception("debug_retrieve failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug/index-stats")
def debug_index_stats() -> dict:
    """看向量索引当前的状态, 用于判断需不需要重建."""
    from vector_store import get_store
    store = get_store()
    return {
        "vector_count": store.count(),
        "sql_count": count_jobs(),
        "synced": store.count() == count_jobs(),
        "embedder": store.embedder.model_name,
        "dimension": store.embedder.dimension,
    }
