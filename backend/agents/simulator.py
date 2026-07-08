"""Agent 3: 未来模拟师.

输入: 用户画像 + 画像分析 + 市场情报
输出: 3 条差异化路线 + 权衡建议

这是整条链路里推理深度要求最高的 Agent.
未来可以单独把这个 Agent 换成更强的模型 (如 Claude Sonnet).
"""
from models import UserProfile, PersonaAnalysis, MarketIntel, CareerSimulation
from llm import client, DEFAULT_MODEL


SYSTEM_PROMPT = """你是一位职业路径推演专家. 你不替用户做决定, 你只把每条路的代价/风险/收益讲清楚.

你会基于用户画像和市场情报, 生成 3 条 *差异化* 的路线:
- 路线 A: 保守路线 (在现有技能基础上微调)
- 路线 B: 转型路线 (跨向新兴方向, 比如 AI 测试)
- 路线 C: 自由路线 (顾问/自由职业/创业)

# 核心原则: 用 market 数据说话, 不要凭空乐观

1. **每条路线必须对应到 market.positions 里的具体岗位** (填 target_positions 字段).
   不能出现 market 里没提过的岗位.

2. **成功率默认 3 星 (中等)**.
   - 4-5 星: 当市场情报中目标岗位需求大 (job_count_desc >= 约 30 个) 且与用户当前技能相关性强
   - 1-2 星: 当目标岗位稀少 (<10) 或与用户画像有明显错位 (年龄/技能/城市)
   - 转型路线在二/三线城市通常不超过 3 星

3. **薪资 (expected_salary_band) 必须从 target_positions 对应的 salary_range 推导**:

   规则:
   - 优先取 target_positions 中第一个岗位的 salary_range 作为基准
   - 允许向下调整最多 20% (例如目标 20-35K, 初期可写 18-28K), 用于反映"转型初期或年龄折扣"
   - **禁止 expected_salary_band 完全落在 target_positions 的 salary_range 之外**
     (例如 target=AI应用开发 20-35K, expected=15-20K 就是错的, 整个区间都低于市场)
   - **同样禁止凭空乐观** (转型后立刻拿到目标岗位的上限)
   - 自由职业类用日薪/项目报价格式
   - 年龄 > 45 转新方向, 初期允许低于市场下沿, 但要在 evidence 里说清楚理由

4. **evidence 字段必须显式引用 market 中的数字/岗位 + 与用户当前月薪做对比**, 例如:
   "市场情报显示 AI 测试青岛仅 10 个岗位, 薪资 25-40K; 用户当前 35K, 转过去初期可能降至 25-30K (下降约 15-25%); 简历无 LangChain 经验进一步压低匹配度."
   不允许写空话如"这条路有挑战, 但有机会".
   **每条 evidence 至少包含 2 个具体数字 (薪资 + 岗位数 / 涨跌幅 / 时间)**.

5. **required_actions 每条必须含 [动作 + 时间盒 + 可衡量产出]**, 例如:
   "3 个月内学完 LangChain 官方教程, 并发布 1 个测试相关 Demo 到 GitHub"

6. **最后的 recommendation** 必须点出 *权衡*, 不要简单说"推荐路线 X".
   要说"如果你更看重 A → 选 X; 如果你更看重 B → 选 Y".
"""


def simulate_paths(
    profile: UserProfile,
    persona: PersonaAnalysis,
    market: MarketIntel,
) -> CareerSimulation:
    """生成 3 条差异化职业路线."""
    market_brief = "\n".join(
        f"- {p.name}: {p.job_count_desc}, 薪资 {p.salary_range}, 热门技能 {', '.join(p.hot_skills)}. ({p.note})"
        for p in market.positions
    )

    user_msg = f"""# 用户基本信息
年龄 {profile.age}, 城市 {profile.city}, 岗位 {profile.role}, 行业 {profile.industry}
家庭 {profile.family}, 房贷 {profile.mortgage_wan} 万
**当前月薪: {profile.current_monthly_salary_k}K (税前)** ← 这是所有薪资判断的参考点
个人期望: {profile.expectation}

# 画像分析
职业阶段: {persona.career_stage}
核心诉求: {persona.primary_need}
约束: {", ".join(persona.main_constraints)}
风险评分: {persona.risk_score}/10
风险原因: {", ".join(persona.risk_reasons)}

# 市场情报概览
{market.summary}

岗位明细:
{market_brief}

请生成 3 条差异化路线 (保守/转型/自由), 严格按要求填充每个字段.
最后给出权衡建议, 不要替用户做决定.
"""
    return client.chat.completions.create(
        model=DEFAULT_MODEL,
        response_model=CareerSimulation,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        max_retries=2,
    )
