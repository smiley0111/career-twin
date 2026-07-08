"""手写的 Agent 编排器. 整个项目的核心调度逻辑就 10 几行.

后续阶段如果需要循环/分支/并发, 再考虑引入 Pydantic AI 或 LangGraph.
现在用最朴素的写法, 让你清楚看到每一步发生什么.
"""
import logging
from models import UserProfile, CareerReport
from agents.persona import analyze_persona
from agents.market import gather_market_intel
from agents.simulator import simulate_paths

logger = logging.getLogger(__name__)


def run_career_twin(profile: UserProfile) -> CareerReport:
    """串联 3 个 Agent, 生成完整报告."""
    logger.info("Agent 1: 画像分析 starting...")
    persona = analyze_persona(profile)
    logger.info("Agent 1 done. stage=%s, risk=%d", persona.career_stage, persona.risk_score)

    logger.info("Agent 2: 市场情报 starting...")
    market = gather_market_intel(profile, persona)
    logger.info("Agent 2 done. positions=%d", len(market.positions))

    logger.info("Agent 3: 路线推演 starting...")
    simulation = simulate_paths(profile, persona, market)
    logger.info("Agent 3 done. paths=%d", len(simulation.paths))

    return CareerReport(
        profile=profile,
        persona=persona,
        market=market,
        simulation=simulation,
    )
