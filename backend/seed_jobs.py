"""初始化青岛岗位库种子数据.

运行方式 (一次性, 重复执行会清空表后重新种):
    python seed_jobs.py

数据来源: 基于 2025-2026 年青岛 IT 招聘市场常识手工编写.
**这些数据是有偏差的示例**, 不是精确的实时招聘信息.
未来阶段 4 会用抓取脚本替换.

特别包含:
- 中车青岛四方 2 个 AI 相关岗位 (用户专门提到这个雇主在招 AI)
- NOKIA 青岛通讯岗 (用户当前雇主, 作为现状对照)
- 覆盖 developer/test/ai/pm/manager/other 全部分类
"""
import sys

from db import init_db
from jobs_repo import clear_jobs, count_jobs, insert_job
from models import Job, JobCategory


SEED_JOBS: list[Job] = [
    # ============ developer (8 条) ============
    Job(
        title="Java 后端开发工程师 (智能家居中台)",
        company="海尔智家", city="青岛", category=JobCategory.DEVELOPER,
        salary_min_k=18, salary_max_k=30, salary_text="18K-30K·14薪", experience="5-10年",
        skills=["Java", "Spring Cloud", "MySQL", "Redis", "Kafka"],
        description="负责智能家居中台高并发服务, 日均亿级请求, 需要分布式系统经验.",
    ),
    Job(
        title="Python 全栈开发工程师",
        company="海信集团", city="青岛", category=JobCategory.DEVELOPER,
        salary_min_k=20, salary_max_k=35, salary_text="20K-35K·13薪", experience="3-5年",
        skills=["Python", "Django", "React", "PostgreSQL"],
        description="AI 显示产品线, 全栈开发数据可视化与算法接口.",
    ),
    Job(
        title="资深 Go 后端工程师 (工业互联网)",
        company="海尔卡奥斯", city="青岛", category=JobCategory.DEVELOPER,
        salary_min_k=25, salary_max_k=42, salary_text="25K-42K·14薪", experience="5-10年",
        skills=["Go", "微服务", "Kubernetes", "Kafka", "gRPC"],
        description="工业互联网平台后端, 千万级设备接入, 强调架构能力.",
    ),
    Job(
        title="C++ 嵌入式开发工程师 (轨道交通信号)",
        company="中车青岛四方", city="青岛", category=JobCategory.DEVELOPER,
        salary_min_k=15, salary_max_k=25, salary_text="15K-25K·15薪", experience="3-5年",
        skills=["C++", "Linux", "嵌入式", "实时系统"],
        description="高铁列车信号系统嵌入式软件开发, 安全等级要求高.",
    ),
    Job(
        title="Android 应用开发工程师 (VR 设备)",
        company="歌尔股份", city="青岛", category=JobCategory.DEVELOPER,
        salary_min_k=18, salary_max_k=28, salary_text="18K-28K·13薪", experience="3-5年",
        skills=["Android", "Kotlin", "OpenGL", "Jetpack"],
        description="为头部 VR 厂商代工的 Android 系统层开发.",
    ),
    Job(
        title="Java 后端开发工程师 (充电桩平台)",
        company="青岛特锐德", city="青岛", category=JobCategory.DEVELOPER,
        salary_min_k=15, salary_max_k=25, salary_text="15K-25K·13薪", experience="3-5年",
        skills=["Java", "Spring Boot", "MySQL", "MQTT"],
        description="充电桩物联网平台, 设备状态采集和计费业务.",
    ),
    Job(
        title="Go 后端开发工程师 (金融业务中台)",
        company="海尔金控", city="青岛", category=JobCategory.DEVELOPER,
        salary_min_k=22, salary_max_k=35, salary_text="22K-35K·14薪", experience="5-10年",
        skills=["Go", "gRPC", "Kafka", "Redis", "高并发"],
        description="金融业务中台 + 风控系统, 需要金融业务理解力.",
    ),
    Job(
        title="5G RAN Software Engineer",
        company="NOKIA 青岛", city="青岛", category=JobCategory.DEVELOPER,
        salary_min_k=18, salary_max_k=30, salary_text="18K-30K·13薪", experience="5-10年",
        skills=["C++", "5G 协议", "Linux", "通信"],
        description="5G 基站软件开发, 与全球研发协作. (外企节奏, 业务持续收缩)",
    ),

    # ============ test (4 条) ============
    Job(
        title="自动化测试工程师 (智能家居 APP)",
        company="海尔智家", city="青岛", category=JobCategory.TEST,
        salary_min_k=15, salary_max_k=25, salary_text="15K-25K·14薪", experience="3-5年",
        skills=["Appium", "Pytest", "Selenium", "Python"],
        description="智能家居 APP 端到端自动化测试, 兼容多设备型号.",
    ),
    Job(
        title="测试开发工程师 SDET (大屏 OS)",
        company="海信视像", city="青岛", category=JobCategory.TEST,
        salary_min_k=18, salary_max_k=28, salary_text="18K-28K·13薪", experience="3-5年",
        skills=["Python", "Pytest", "CI/CD", "Jenkins"],
        description="电视 OS 测试工具链开发, 偏开发型测试.",
    ),
    Job(
        title="性能测试工程师 (智慧地铁系统)",
        company="青岛地铁", city="青岛", category=JobCategory.TEST,
        salary_min_k=14, salary_max_k=20, salary_text="14K-20K·14薪", experience="3-5年",
        skills=["JMeter", "LoadRunner", "Linux", "MySQL"],
        description="智慧地铁运营系统性能测试, 国企编制.",
    ),
    Job(
        title="测试经理 (5G 业务平台)",
        company="中国移动山东", city="青岛", category=JobCategory.MANAGER,
        salary_min_k=25, salary_max_k=35, salary_text="25K-35K·15薪", experience="8-15年",
        skills=["团队管理", "测试架构", "5G 业务", "敏捷"],
        description="带 15 人测试团队, 负责省级 5G 业务平台质量.",
    ),

    # ============ ai (4 条, 包含中车 2 个) ============
    Job(
        title="AI 算法工程师 (智能调度)",
        company="中车青岛四方", city="青岛", category=JobCategory.AI,
        salary_min_k=25, salary_max_k=40, salary_text="25K-40K·15薪", experience="3-5年",
        skills=["Python", "PyTorch", "强化学习", "运筹优化"],
        description="高铁/地铁智能调度算法, 探索 RL 在轨道交通的应用. (用户实测中提到的真实方向)",
    ),
    Job(
        title="LLM 应用开发工程师 (运维知识库)",
        company="中车青岛四方", city="青岛", category=JobCategory.AI,
        salary_min_k=22, salary_max_k=35, salary_text="22K-35K·14薪", experience="不限",
        skills=["LangChain", "RAG", "向量数据库", "Python", "Prompt"],
        description="为高铁维修运维场景搭建大模型知识库, 经验不限, 看项目作品.",
    ),
    Job(
        title="计算机视觉算法工程师 (AI 画质)",
        company="海信视像", city="青岛", category=JobCategory.AI,
        salary_min_k=25, salary_max_k=45, salary_text="25K-45K·13薪", experience="3-8年",
        skills=["OpenCV", "PyTorch", "图像处理", "C++"],
        description="电视 AI 画质算法, 与韩国/日本同业竞争, 团队成熟.",
    ),
    Job(
        title="大模型应用工程师 (工业知识助手, 可远程)",
        company="海尔卡奥斯", city="青岛/远程", category=JobCategory.AI,
        salary_min_k=25, salary_max_k=40, salary_text="25K-40K·14薪", experience="3-5年",
        skills=["LangChain", "LlamaIndex", "Qwen/DeepSeek", "Prompt Engineering"],
        description="工业互联网知识库智能问答, 远程友好, 接受全国候选人.",
    ),

    # ============ pm (2 条) ============
    Job(
        title="产品经理 (智能家居 APP)",
        company="海尔智家", city="青岛", category=JobCategory.PM,
        salary_min_k=18, salary_max_k=30, salary_text="18K-30K·14薪", experience="3-5年",
        skills=["用户研究", "原型设计", "数据分析", "C端经验"],
        description="智能家居 APP 主端产品经理, 千万级 DAU.",
    ),
    Job(
        title="B 端 SaaS 产品经理 (工业互联网)",
        company="海尔卡奥斯", city="青岛", category=JobCategory.PM,
        salary_min_k=22, salary_max_k=35, salary_text="22K-35K·14薪", experience="5-10年",
        skills=["B端产品", "SaaS", "工业行业", "需求分析"],
        description="负责工业互联网 SaaS 产品线, 需要 B 端 + 行业 know-how.",
    ),

    # ============ manager (1 条) ============
    Job(
        title="技术总监 (智能化研发中心)",
        company="中车青岛四方", city="青岛", category=JobCategory.MANAGER,
        salary_min_k=50, salary_max_k=80, salary_text="50K-80K·15薪", experience="10年+",
        skills=["团队管理", "架构设计", "AI 转型", "行业经验"],
        description="带领 100+ 人研发中心进行 AI 化转型, 央企背景.",
    ),

    # ============ other (1 条) ============
    Job(
        title="高级架构师 (云原生平台)",
        company="海尔卡奥斯", city="青岛", category=JobCategory.OTHER,
        salary_min_k=30, salary_max_k=50, salary_text="30K-50K·14薪", experience="8-15年",
        skills=["Kubernetes", "Service Mesh", "分布式", "云原生"],
        description="工业互联网云原生平台架构, 跨团队技术决策.",
    ),
]


def main(reset: bool = True) -> None:
    init_db()
    if reset:
        clear_jobs()
        print("Cleared existing jobs.")

    for job in SEED_JOBS:
        new_id = insert_job(job)
        print(f"  + [{new_id}] {job.category.value:<10} {job.company} - {job.title}")

    total = count_jobs()
    print(f"\nDone. {total} jobs in DB.")


if __name__ == "__main__":
    main(reset="--no-reset" not in sys.argv)
