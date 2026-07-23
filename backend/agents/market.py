"""Agent 2: 市场情报分析师 (Stage 4 RAG 版).

# 历史

- Stage 2: 用 mock_market.json 写死, LLM 看着 json 编 (容易脱离实际)
- Stage 3: SQLite 硬过滤 city + category, 把候选岗位喂给 LLM 聚合
- Stage 4: **向量检索**, 让 "37岁通讯行业想转 AI" 这种语义意图能跨 category 匹配

# 关键设计 (RAG 工程套路)

1. **查询构造 (build_query)**: 把 UserProfile + PersonaAnalysis 拼成自然语言.
   语义匹配的质量很大程度取决于 query 写得好不好.

2. **混合检索 (hybrid)**:
   - metadata 过滤: city (硬约束, 一定要本地)
   - 向量检索: 余弦相似度找 top-K
   - 我们故意**不在 metadata 里强过滤 category**, 让模型有机会跨分类推荐

3. **fallback**: 如果索引为空 (没跑 build_index.py), 退回到 SQL 过滤老逻辑
"""
from models import (
    PersonaAnalysis, UserProfile, MarketIntel, Job, JobCategory,
)
from llm import routed_client
from jobs_repo import list_jobs
from vector_store import get_store


# Stage 3 的 category fallback 映射, 索引空时用
_RELATED_CATEGORIES: dict[JobCategory, list[JobCategory]] = {
    JobCategory.DEVELOPER: [JobCategory.DEVELOPER, JobCategory.AI, JobCategory.OTHER],
    JobCategory.TEST:      [JobCategory.TEST, JobCategory.AI, JobCategory.DEVELOPER],
    JobCategory.AI:        [JobCategory.AI, JobCategory.DEVELOPER, JobCategory.OTHER],
    JobCategory.PM:        [JobCategory.PM, JobCategory.MANAGER, JobCategory.AI],
    JobCategory.MANAGER:   [JobCategory.MANAGER, JobCategory.DEVELOPER, JobCategory.TEST, JobCategory.AI],
    JobCategory.OTHER:     [JobCategory.OTHER, JobCategory.DEVELOPER, JobCategory.AI],
}


# ---------- 查询构造 ----------

def _build_query(profile: UserProfile, persona: PersonaAnalysis) -> str:
    """把用户画像拼成自然语言, 给 embedding 模型理解.

    经验法则:
    - 把"想匹配什么"放前面 (embedding 对前面 token 更敏感)
    - 同时给"现状"和"期望", 让向量能往两个方向找
    - 不要太长 (BGE 上限 512 token, 但有效信号集中在前 200)
    """
    return (
        f"{profile.age}岁 {profile.role}, 在{profile.industry}行业, "
        f"工作经验丰富, 当前月薪 {profile.current_monthly_salary_k}K. "
        f"个人期望: {profile.expectation}. "
        f"职业核心诉求: {persona.primary_need}. "
        f"主要约束: {', '.join(persona.main_constraints[:3])}. "
        f"寻找在 {profile.city} 的合适岗位, 包含同方向晋升/横向迁移/转型机会."
    )


# ---------- 候选岗位获取 ----------

def _retrieve_via_rag(profile: UserProfile, persona: PersonaAnalysis, k: int = 10) -> tuple[list[dict], str, str]:
    """走向量检索. 返回 (hits, query, source_tag)."""
    query = _build_query(profile, persona)
    store = get_store()
    hits = store.search(query, k=k, city=profile.city)
    return hits, query, "rag"


def _retrieve_via_sql(profile: UserProfile) -> tuple[list[dict], str, str]:
    """fallback: SQL 硬过滤 (老逻辑). 返回 (hits, query, source_tag)."""
    categories = _RELATED_CATEGORIES[profile.role_category]
    jobs = list_jobs(city=profile.city, categories=categories, limit=20)
    hits = [
        {
            "job_id": j.id, "title": j.title, "company": j.company, "city": j.city,
            "category": j.category.value, "skills": j.skills,
            "salary_min_k": j.salary_min_k, "salary_max_k": j.salary_max_k,
            "document": "", "similarity": None,
        }
        for j in jobs
    ]
    return hits, f"city={profile.city}, categories={[c.value for c in categories]}", "sql_fallback"


def _format_hits(hits: list[dict]) -> str:
    if not hits:
        return "(检索结果为空, 该城市岗位库可能为空, 请用一般市场常识推断)"
    lines = []
    for h in hits:
        skills = ", ".join(h["skills"][:5]) if h["skills"] else "-"
        salary = f"{h['salary_min_k']}K-{h['salary_max_k']}K"
        sim = f"sim={h['similarity']:.2f} " if h.get("similarity") is not None else ""
        lines.append(
            f"- {sim}[{h['category']:<10}] {h['company']:<14} | {h['title']} "
            f"| {salary} | 技能: {skills}"
        )
    return "\n".join(lines)


# ---------- Prompt ----------

SYSTEM_PROMPT = """你是一位中国互联网招聘市场的资深情报分析师, 熟悉 Boss 直聘/拉勾/猎聘的真实行情.

你会收到:
1. 用户的画像 (年龄/岗位/城市/期望等)
2. **通过语义检索从真实岗位库中召回的 Top-K 岗位** (按相似度排序, 已经按用户画像匹配过)

你的任务: 把这些**真实召回岗位**聚合成 3-5 个 PositionIntel, 给出针对该用户最相关的方向情报.

# 关键原则

1. **必须基于召回的真实岗位数据进行聚合**, 不要凭空编造没出现过的岗位/公司
2. 聚合时把相似岗位合并 (例如 3 个 Java 后端可以合并成一个 "Java 后端开发" PositionIntel)
3. 必须覆盖 "维持现状", "向上转型/AI", "横向迁移" 至少 3 种方向
4. **如果召回里有 AI 相关岗位 (无论 category=ai 还是 description 提到 AI/大模型), 必须给 AI 方向独立 PositionIntel**
5. salary_range 字段必须取该方向所有岗位 salary 的真实区间, 不要乱估
6. 用户期望转 AI 时, 优先把 AI 类岗位放前面

# job_count_desc 字段约定

- 看到的岗位 N >= 5: 写 "约 N 个 (近期招聘)"
- 2 <= N < 5: 写 "稀少 (仅 N 个)"
- N <= 1: 写 "极少, 几乎无机会" 或 "无固定岗位, 按项目"

# summary 字段要求

不要写"市场需求平稳"这种废话. 要基于真实数据指出具体洞察, 例如:
- "青岛 AI 岗位主要集中在 X 公司 + Y 公司, 共 N 个, 其中 K 个支持远程"
- "传统通讯方向 (NOKIA / 中国移动) 还在招, 但薪资天花板 30K, 远低于 AI 方向 40K+"
"""


# ---------- 主入口 ----------

def gather_market_intel(profile: UserProfile, persona: PersonaAnalysis) -> MarketIntel:
    """RAG 优先, SQL fallback."""
    store = get_store()
    if store.count() > 0:
        hits, query_text, source = _retrieve_via_rag(profile, persona, k=10)
    else:
        # 索引空: 提示用户去建索引, 用 SQL 兜底
        print("[market] vector store empty, fallback to SQL filter")
        hits, query_text, source = _retrieve_via_sql(profile)

    hits_text = _format_hits(hits)

    user_msg = f"""# 用户画像
年龄: {profile.age}, 城市: {profile.city}, 岗位: {profile.role} ({profile.role_category.value}), 行业: {profile.industry}
当前月薪: {profile.current_monthly_salary_k}K
职业阶段: {persona.career_stage}
核心诉求: {persona.primary_need}
主要约束: {", ".join(persona.main_constraints)}
个人期望: {profile.expectation}

# 检索方式: {source}
# 检索查询: {query_text}

# 召回岗位 ({len(hits)} 条, 按相似度从高到低)
{hits_text}

请把上面的真实召回岗位聚合成 3-5 个 PositionIntel, 覆盖维持/转型/横向至少 3 种方向.
**如果召回里有 AI 岗位, 必须独立给一个 PositionIntel**.
**summary 要点出真实数据中的具体洞察**, 不要套话.
"""
    client, model = routed_client("market")
    return client.chat.completions.create(
        model=model,
        response_model=MarketIntel,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_retries=2,
    )


# ---------- 调试 helper (前端可调用看检索质量) ----------

def debug_retrieve(profile: UserProfile, persona: PersonaAnalysis, k: int = 10) -> dict:
    """返回检索过程的中间结果, 用于前端展示 "Agent 2 检索到了什么"."""
    store = get_store()
    if store.count() > 0:
        hits, query_text, source = _retrieve_via_rag(profile, persona, k=k)
    else:
        hits, query_text, source = _retrieve_via_sql(profile)
    return {
        "source": source,
        "query": query_text,
        "k": k,
        "total_indexed": store.count(),
        "hits": hits,
    }
