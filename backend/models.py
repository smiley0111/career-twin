"""所有 Agent 之间传递的结构化数据模型.

设计原则:
- 强类型, 让 Instructor 强制 LLM 按这个结构返回, 避免解析失败
- 每个字段都有 Field(description=...), LLM 会读这个描述, 提升输出质量
- 字段尽量是枚举或受限文本, 减少自由发挥
"""
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


# ---------- 岗位分类 ----------

class JobCategory(str, Enum):
    """岗位大类. 用户也用这个 enum 选自己的 role_category."""
    DEVELOPER = "developer"   # 后端/前端/全栈/移动/嵌入式
    TEST = "test"             # 测试/QA/自动化/SDET
    AI = "ai"                 # 算法/AI 应用/大模型/CV/NLP
    PM = "pm"                 # 产品经理
    MANAGER = "manager"       # 技术/研发经理/总监
    OTHER = "other"           # 架构师/DevOps/运维/数据等


# ---------- 输入 ----------

class UserProfile(BaseModel):
    """用户在前端填写的原始信息."""
    age: int = Field(description="年龄")
    role: str = Field(description="当前岗位, 例如 测试经理")
    role_category: JobCategory = Field(
        description="岗位大类, 用于从岗位库筛选相关市场情报. "
                    "developer=研发, test=测试, ai=AI/算法, pm=产品, manager=管理, other=其他.",
        default=JobCategory.DEVELOPER,
    )
    industry: str = Field(description="所在行业, 例如 互联网电视")
    city: str = Field(description="所在城市")
    family: str = Field(description="家庭状况, 自由文本")
    mortgage_wan: float = Field(description="房贷余额(万元)", ge=0)
    current_monthly_salary_k: int = Field(
        description="当前税前月薪 (单位 K, 例如 30 表示 30K/月). "
                    "所有 Agent 的薪资判断都会以此为参考点.",
        ge=0, le=500,
    )
    expectation: str = Field(description="对未来的期望, 自由文本")


# ---------- Agent 1: 画像分析 ----------

class PersonaAnalysis(BaseModel):
    """画像分析师的结构化输出."""
    career_stage: Literal["早期", "中期", "中后期", "晚期"] = Field(
        description="职业生涯所处阶段"
    )
    primary_need: str = Field(description="最核心的诉求, 一句话")
    main_constraints: list[str] = Field(
        description="主要约束条件, 3-5 条", min_length=2, max_length=6
    )
    risk_score: int = Field(
        description="综合风险评分 1-10, 数字越大风险越高", ge=1, le=10
    )
    risk_reasons: list[str] = Field(
        description="风险来源具体原因, 2-4 条", min_length=2, max_length=5
    )


# ---------- Agent 2: 市场情报 ----------

class PositionIntel(BaseModel):
    """单个岗位的市场情报."""
    name: str = Field(description="岗位名称")
    job_count_desc: str = Field(
        description="岗位规模描述. 普通岗位用'约 N 个'; "
                    "自由职业/顾问类没有固定岗位, 写'无固定岗位, 按项目'; "
                    "数据稀疏时可以写'稀少 (<10)'."
    )
    salary_range: str = Field(description="薪资区间, 例如 25K-45K, 月薪")
    hot_skills: list[str] = Field(description="热门技能要求, 3-6 个, 必须是具体技术名词")
    note: str = Field(description="一句话补充说明, 例如 招聘节奏/竞争激烈度")


class MarketIntel(BaseModel):
    """市场情报分析师的整体输出."""
    summary: str = Field(description="当前市场整体判断, 2-3 句话")
    positions: list[PositionIntel] = Field(
        description="相关岗位的情报, 4 个左右", min_length=3, max_length=6
    )


# ---------- Agent 3: 路线推演 ----------

class CareerPath(BaseModel):
    """一条具体的职业路线."""
    name: str = Field(description="路线名称, 例如 继续测试管理")
    one_liner: str = Field(description="一句话描述这条路")

    success_probability: int = Field(
        description="成功概率 1-5 星. 默认 3 星 (中等). "
                    "只有当市场情报中目标岗位明显需求大、用户画像匹配度高时才能给 4-5 星; "
                    "目标岗位稀少或与用户画像有明显错位时给 1-2 星. "
                    "禁止盲目乐观.",
        ge=1, le=5,
    )
    expected_months: int = Field(description="预计达成所需的月数")

    expected_salary_band: str = Field(
        description="走这条路在 6-12 个月后能达到的月薪区间, 例如 '22K-30K'. "
                    "自由职业类写日薪或项目报价区间. "
                    "**必须基于 target_positions 中岗位的 salary_range, "
                    "允许下调最多 20%, 但不允许完全脱离市场区间**. "
                    "既不允许凭空乐观 (直接拿目标上限), 也不允许凭空悲观 (大幅低于市场下限)."
    )
    target_positions: list[str] = Field(
        description="这条路对应市场情报里的哪些岗位 (必须引用 MarketIntel.positions 中出现过的 name). "
                    "至少 1 个, 最多 3 个. 自由职业类可以写 '质量顾问' 等具体方向.",
        min_length=1, max_length=3,
    )

    main_risks: list[str] = Field(
        description="主要风险, 2-4 条", min_length=1, max_length=5
    )
    required_actions: list[str] = Field(
        description="为了走这条路, 接下来要做什么, 3-5 条具体行动. "
                    "每条必须含具体动作 + 时间盒 + 可衡量产出, "
                    "例如 '3 个月内完成 1 个 LangChain Demo 并发布到 GitHub'",
        min_length=2, max_length=6,
    )

    evidence: str = Field(
        description="本路线的成功率和薪资判断基于什么? "
                    "必须明确引用市场情报中的具体数字/岗位/趋势, 不能空泛.",
        min_length=20,
    )


class CareerSimulation(BaseModel):
    """未来模拟师的整体输出."""
    paths: list[CareerPath] = Field(
        description="3 条差异化的路线: 保守路线 / 转型路线 / 自由路线",
        min_length=3, max_length=3
    )
    recommendation: str = Field(
        description="基于用户约束和市场情况, 最值得优先尝试的路线及原因. 不替用户做决定, 只指出权衡."
    )


# ---------- 最终聚合 ----------

class CareerReport(BaseModel):
    """返回给前端的完整报告."""
    profile: UserProfile
    persona: PersonaAnalysis
    market: MarketIntel
    simulation: CareerSimulation


# ---------- 测试画像库 ----------

class TestCase(BaseModel):
    """test-cases/*.json 文件的结构. 用于前端快速切换不同画像做压力测试."""
    id: str = Field(description="唯一短 ID")
    name: str = Field(description="显示给用户的简短名")
    description: str = Field(description="这个画像描述什么场景")
    probe: str = Field(description="这个画像想验证什么 / 想找出什么 bug")
    profile: UserProfile


# ---------- 岗位库 (Stage 3 真实数据) ----------

class Job(BaseModel):
    """SQLite jobs 表的一行. 来自手工种子数据或未来的抓取脚本."""
    id: int | None = None
    title: str = Field(description="岗位标题")
    company: str = Field(description="招聘公司")
    city: str = Field(description="工作城市")
    category: JobCategory = Field(description="岗位大类")
    salary_min_k: int = Field(description="月薪下限 (K)", ge=0)
    salary_max_k: int = Field(description="月薪上限 (K)", ge=0)
    salary_text: str = Field(description="原始薪资文本, 例如 '20K-35K·14薪'")
    experience: str = Field(description="经验要求, 例如 '3-5 年' / '不限'")
    skills: list[str] = Field(description="技能标签", default_factory=list)
    description: str = Field(description="一句话岗位描述")
    source: str = Field(description="数据来源 manual / boss / lagou", default="manual")
    source_url: str | None = None
    posted_at: str | None = Field(description="发布日期 ISO 格式 (可选)", default=None)
