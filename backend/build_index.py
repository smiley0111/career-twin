"""把 jobs.db 里所有岗位灌进 Chroma 向量库.

运行方式:
    python build_index.py             # 增量 upsert (相同 id 覆盖)
    python build_index.py --rebuild   # 全量重建 (先清空再灌)

什么时候要跑:
- 第一次启动: 必须跑一次, 否则 Agent 2 检索空表
- 改了 seed_jobs.py 增加了新岗位: 增量跑一次
- 改了 vector_store.job_to_document() 文档拼接逻辑: --rebuild

未来 (阶段 4b/4c) 抓爬虫入库后, 也调用 store.add_jobs() 即可,
不必每次全量重建.
"""
import sys
import time

from db import init_db
from jobs_repo import list_jobs
from vector_store import get_store


def main(rebuild: bool = False) -> None:
    init_db()
    jobs = list_jobs(limit=10000)
    if not jobs:
        print("[build_index] jobs.db 是空的, 先跑 python seed_jobs.py")
        return

    store = get_store()
    if rebuild:
        print(f"[build_index] --rebuild: 清空旧索引...")
        store.clear()

    t0 = time.time()
    n = store.add_jobs(jobs)
    cost = time.time() - t0
    print(
        f"[build_index] 灌入 {n} 个岗位, 耗时 {cost:.1f}s, "
        f"当前索引总数 = {store.count()}"
    )

    # 自检: 随便检索一下, 看返回质量
    print("\n[build_index] 自检: 用 'Java 后端' 测试检索...")
    for hit in store.search("Java 后端开发, 微服务", k=3):
        print(
            f"  - sim={hit['similarity']:.3f}  "
            f"{hit['company']:<10} {hit['title']}"
        )


if __name__ == "__main__":
    main(rebuild="--rebuild" in sys.argv)
