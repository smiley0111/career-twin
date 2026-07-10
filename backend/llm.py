"""统一的 LLM 客户端入口 (基于 dodu_ai SDK).

变更历史:
- Stage 1-4: 直接 openai.OpenAI + instructor.from_openai
- Stage 5 (2026-07 重构): 收敛到 dodu_ai.DoduClient, 白得成本追踪 (dodu.stats)

对外接口保持不变, 3 个 agent 仍然 from llm import client, DEFAULT_MODEL 即可.
新增了 dodu 对象, 可以通过它拿到 .stats.summary() / .stats.total_cost_usd 等.
"""
import os

from dodu_ai import DoduClient


def _pick_provider() -> str:
    """按当前 .env 中已配置的 key 自动挑选 provider.

    保持向后兼容: 老的 .env 只填 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 都能跑.
    """
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return os.getenv("DODU_AI_PROVIDER", "deepseek")


dodu: DoduClient = DoduClient(
    provider=_pick_provider(),
    base_url=os.getenv("DEEPSEEK_BASE_URL") or os.getenv("OPENAI_BASE_URL"),
    default_model=os.getenv("DEEPSEEK_MODEL") or os.getenv("OPENAI_MODEL"),
)

client = dodu.instructor()
DEFAULT_MODEL: str = dodu.default_model
