"""容器启动前置脚本 (幂等).

部署平台 (Railway / Fly / 容器) 的文件系统通常是**临时的**: 每次冷启动/重新部署,
上一次跑 seed_jobs.py / build_index.py 建好的 jobs.db 和 chroma_data 都会没.

所以启动 uvicorn 之前先跑一遍这个脚本, 保证:
1. SQLite 有种子岗位数据
2. Chroma 向量索引已建好 (否则 market agent 会 fallback 到 SQL, 不是我们要的 RAG)

幂等: 已有数据就跳过, 不会重复灌 / 不会清空线上可能已存在的持久卷数据.
"""
import sys

from db import init_db
from jobs_repo import count_jobs


def main() -> None:
    init_db()

    n_jobs = count_jobs()
    if n_jobs == 0:
        print("[prestart] jobs 表为空 -> 种入种子数据")
        import seed_jobs
        seed_jobs.main(reset=True)
    else:
        print(f"[prestart] jobs 表已有 {n_jobs} 条, 跳过 seed")

    # 向量索引: 放在 seed 之后, 且延迟 import (触发 embedder 初始化需要 EMBEDDING_* 环境变量)
    from vector_store import get_store
    store = get_store()
    if store.count() == 0:
        print("[prestart] 向量索引为空 -> 建索引")
        import build_index
        build_index.main(rebuild=True)
    else:
        print(f"[prestart] 向量索引已有 {store.count()} 条, 跳过建索引")

    print("[prestart] done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # 建索引依赖外部 embedding API, 失败时打清楚日志但不阻断启动
        # (main.py 里 market agent 有 SQL fallback, 服务仍可用, 只是暂时非 RAG)
        print(f"[prestart] WARNING: 前置准备失败: {e}", file=sys.stderr)
        print("[prestart] 服务仍会启动, market agent 将走 SQL fallback", file=sys.stderr)
