"""career-twin 的 LLM 客户端入口 (基于 dodu_ai SDK, 带按 task 路由).

变更历史:
- Stage 1-4: 直接 openai.OpenAI + instructor.from_openai
- Stage 5 (2026-07-10): 收敛到 dodu_ai.DoduClient, 白得成本追踪
- Stage 6 (2026-07-23): 引入 dodu_ai.RoutedClient, 按 task 分模型
    * persona / market: deepseek-chat  (快, 便宜, 只做摘要)
    * simulator:        deepseek-reasoner  (关键节点, 需要长链推理)
    * default:          deepseek-chat

设计要点:
- 只维护一张路由表, 不散在各 agent 里
- 所有 agent 共享同一个 Stats (rc.stats.summary() 一屏看完成本)
- .env 里的 DEEPSEEK_MODEL / DEEPSEEK_REASONING_MODEL 依然生效, 覆盖默认

Agent 用法:
    from llm import routed_client
    client, model = routed_client("persona")
    result = client.chat.completions.create(
        model=model, response_model=X, messages=[...], max_retries=2,
    )

外部 (main.py / 脚本) 用法:
    from llm import rc
    print(rc.stats.summary())
"""
import os

from dodu_ai import ModelRouter, ModelSpec, RoutedClient


def _pick_provider() -> str:
    """按当前 .env 中已配置的 key 自动挑选默认 provider.

    保持向后兼容: 老的 .env 只填 DEEPSEEK_API_KEY 或 OPENAI_API_KEY 都能跑.
    """
    if os.getenv("DEEPSEEK_API_KEY"):
        return "deepseek"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return os.getenv("DODU_AI_PROVIDER", "deepseek")


_PROVIDER = _pick_provider()

if _PROVIDER == "deepseek":
    _CHAT = ModelSpec("deepseek", os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))
    _REASONING = ModelSpec(
        "deepseek", os.getenv("DEEPSEEK_REASONING_MODEL", "deepseek-reasoner")
    )
elif _PROVIDER == "openai":
    _CHAT = ModelSpec("openai", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    _REASONING = ModelSpec("openai", os.getenv("OPENAI_REASONING_MODEL", "o1-mini"))
else:
    _CHAT = ModelSpec(_PROVIDER, os.getenv("DODU_AI_DEFAULT_MODEL", "deepseek-chat"))
    _REASONING = _CHAT


router: ModelRouter = (
    ModelRouter(default=_CHAT)
        .add("persona", _CHAT)
        .add("market", _CHAT)
        .add("simulator", _REASONING)
)

rc: RoutedClient = RoutedClient(router)


def routed_client(task: str = "", complexity: str = ""):
    """获取按 task 路由后的 (instructor_client, model) 元组.

    典型用法 (在 agent 里):
        from llm import routed_client
        client, model = routed_client("persona")
        result = client.chat.completions.create(
            model=model, response_model=X, messages=[...], max_retries=2,
        )
    """
    spec = rc.spec_for(task, complexity)
    ic = rc.instructor_for(task, complexity)
    return ic, spec.model
