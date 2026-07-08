"""向量存储层, 把 Chroma 包成业务友好的 API.

# 设计要点 (面试常问)

1. **文档构造**: 一个 Job 怎么变成 "可被语义检索的文本"?
   只放语义信息 (title/skills/description/category), 不放硬过滤项 (city/salary).
   硬过滤项放 metadata, 检索时按需 where 过滤.

2. **distance vs similarity**: Chroma 返回的是 distance (越小越相似).
   我们对外暴露 similarity = 1 - distance, 便于阅读 (0.85 比 0.15 直观).

3. **持久化**: PersistentClient(path=...) 会把索引存盘.
   下次启动直接 load, 不用重建. 重要!

4. **embedding 隔离**: 不用 Chroma 默认的 embedding (英文模型),
   我们自己调 get_embedder() 算好向量再传进去. 这样模型可控.
"""
from __future__ import annotations

import json
from pathlib import Path

import chromadb
from chromadb.config import Settings

from embeddings import EmbeddingProvider, get_embedder
from models import Job


CHROMA_DIR = Path(__file__).parent / "chroma_data"
COLLECTION_NAME = "jobs_v1"


# ---------- 文档拼接 ----------

def job_to_document(job: Job) -> str:
    """把 Job 拼成"用于语义检索的纯文本".

    重要: 只放语义维度, 不放 city/salary (那些是 metadata 过滤项).
    顺序按"重要度递减", 因为 embedding 模型对前面 token 更敏感.
    """
    skills = ", ".join(job.skills) if job.skills else "无"
    return (
        f"岗位: {job.title}\n"
        f"分类: {job.category.value}\n"
        f"技能要求: {skills}\n"
        f"经验: {job.experience}\n"
        f"描述: {job.description}\n"
        f"公司: {job.company}"
    )


def job_to_metadata(job: Job) -> dict:
    """metadata 用于 where 过滤, 必须是基础类型 (str/int/float/bool)."""
    return {
        "job_id": int(job.id) if job.id is not None else -1,
        "city": job.city,
        "category": job.category.value,
        "company": job.company,
        "salary_min_k": int(job.salary_min_k),
        "salary_max_k": int(job.salary_max_k),
        # title/skills 也存一份, 方便检索后无需回查 SQLite
        "title": job.title,
        "skills_json": json.dumps(job.skills, ensure_ascii=False),
    }


# ---------- Store ----------

class JobVectorStore:
    """jobs 集合的封装, 业务代码只跟它打交道."""

    def __init__(self, embedder: EmbeddingProvider | None = None):
        self.embedder = embedder or get_embedder()
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=str(CHROMA_DIR),
            settings=Settings(anonymized_telemetry=False),  # 不要上报数据
        )
        # 显式指定 cosine 距离, 跟 BGE 模型训练目标一致
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine", "embedder": embedder.model_name if embedder else "default"},
        )

    # ----- 写 -----

    def add_jobs(self, jobs: list[Job]) -> int:
        """批量灌入. 已有同 id 会被覆盖 (upsert)."""
        if not jobs:
            return 0
        ids = [f"job_{j.id}" for j in jobs]
        docs = [job_to_document(j) for j in jobs]
        metas = [job_to_metadata(j) for j in jobs]
        # 自己算向量, 不依赖 Chroma 默认 embedding
        vectors = self.embedder.embed(docs)
        self.collection.upsert(
            ids=ids,
            documents=docs,
            embeddings=vectors,
            metadatas=metas,
        )
        return len(jobs)

    def clear(self) -> None:
        """删整个 collection, 重建空表. 全量重建索引时用."""
        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    # ----- 读 -----

    def count(self) -> int:
        return int(self.collection.count())

    def search(
        self,
        query: str,
        k: int = 8,
        city: str | None = None,
        categories: list[str] | None = None,
    ) -> list[dict]:
        """语义检索.

        Returns:
            list of {
                "job_id": int,
                "title": str,
                "company": str,
                "city": str,
                "category": str,
                "skills": list[str],
                "salary_min_k": int,
                "salary_max_k": int,
                "document": str,           # 原文 (用于看检索质量)
                "similarity": float,       # 0~1, 越大越相似
            }
        """
        if self.count() == 0:
            return []

        # 构造 metadata 过滤条件 (Chroma 的 where 语法)
        where: dict | None = None
        clauses: list[dict] = []
        if city:
            clauses.append({"city": city})
        if categories:
            clauses.append({"category": {"$in": list(categories)}})
        if len(clauses) == 1:
            where = clauses[0]
        elif len(clauses) > 1:
            where = {"$and": clauses}

        # 把查询文本变成向量, 然后让 Chroma 找最近邻
        query_vec = self.embedder.embed([query])[0]
        raw = self.collection.query(
            query_embeddings=[query_vec],
            n_results=k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        results: list[dict] = []
        ids = raw.get("ids", [[]])[0]
        docs = raw.get("documents", [[]])[0]
        metas = raw.get("metadatas", [[]])[0]
        dists = raw.get("distances", [[]])[0]
        for _id, doc, meta, dist in zip(ids, docs, metas, dists):
            results.append({
                "job_id": meta.get("job_id"),
                "title": meta.get("title"),
                "company": meta.get("company"),
                "city": meta.get("city"),
                "category": meta.get("category"),
                "skills": json.loads(meta.get("skills_json", "[]")),
                "salary_min_k": meta.get("salary_min_k"),
                "salary_max_k": meta.get("salary_max_k"),
                "document": doc,
                "similarity": round(1.0 - float(dist), 4),
            })
        return results


_singleton: JobVectorStore | None = None


def get_store() -> JobVectorStore:
    """全局单例."""
    global _singleton
    if _singleton is None:
        _singleton = JobVectorStore()
    return _singleton
