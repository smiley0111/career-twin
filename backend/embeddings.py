"""Embedding provider 抽象 + 两种实现 (本地 / 远程 API).

# 为什么需要这一层

向量检索的第一步是把"文本 -> 向量". 不同的模型有不同的:
- 维度 (BGE-small-zh = 512, BGE-M3 = 1024, OpenAI ada = 1536)
- 语言能力 (BGE 中文系列 SOTA, OpenAI ada 中文一般)
- 部署方式 (本地 ONNX vs API 调用)

把这层抽象出来, 以后换模型只改这个文件, 业务代码不用动.

# 当前选型

通过环境变量 EMBEDDING_PROVIDER 切换:
- local    (默认): fastembed + BAAI/bge-small-zh-v1.5  (需要 Visual C++ Runtime)
- api               : OpenAI 兼容 API (硅基流动 / 智谱 / 阿里通义 / 任何 OpenAI 兼容服务)

# API 模式配置 (.env)

EMBEDDING_PROVIDER=api
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1   # 硅基流动 (推荐, 免费额度)
EMBEDDING_API_KEY=sk-xxxxxxxxxx
EMBEDDING_MODEL=BAAI/bge-m3                          # 1024 维, 多语言 SOTA
EMBEDDING_DIM=1024
"""
import os
from typing import Protocol

from dotenv import load_dotenv

load_dotenv()


class EmbeddingProvider(Protocol):
    """所有 embedding 实现都遵守的协议."""

    def embed(self, texts: list[str]) -> list[list[float]]: ...

    @property
    def dimension(self) -> int: ...

    @property
    def model_name(self) -> str: ...


# ---------- 实现 1: 本地 BGE-small-zh (fastembed + ONNX) ----------

class LocalBGEProvider:
    """本地 BGE-small-zh, 走 fastembed (ONNX Runtime).

    优点: 离线, 免费, 不限速
    缺点: 依赖系统 Visual C++ Redistributable, Windows 上有时碰到 DLL 问题
    """

    def __init__(self, model_id: str = "BAAI/bge-small-zh-v1.5"):
        from fastembed import TextEmbedding  # 延迟 import, 避免 DLL 错误污染 API 模式

        self._model_id = model_id
        print(f"[embeddings] loading local {model_id} ... (首次需下载 ~95MB)")
        self._model = TextEmbedding(model_name=model_id)
        print(f"[embeddings] local ready, dimension={self.dimension}")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return [list(map(float, v)) for v in self._model.embed(texts)]

    @property
    def dimension(self) -> int:
        return 512

    @property
    def model_name(self) -> str:
        return self._model_id


# ---------- 实现 2: OpenAI 兼容 API (硅基流动 / 智谱 / 通义...) ----------

class OpenAICompatibleProvider:
    """走 OpenAI 兼容的 embedding API.

    推荐供应商:
    - 硅基流动 SiliconFlow: https://api.siliconflow.cn/v1, 免费 14 元额度送 BGE-M3
    - 智谱 ZhipuAI: https://open.bigmodel.cn/api/paas/v4, embedding-3 便宜
    - 阿里 DashScope (OpenAI 兼容模式)
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "BAAI/bge-m3",
        dimension: int = 1024,
    ):
        from openai import OpenAI

        self._client = OpenAI(base_url=base_url, api_key=api_key)
        self._model = model
        self._dim = dimension
        print(f"[embeddings] using API {base_url} model={model} dim={dimension}")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        # OpenAI 接口批量限制一般 64-128, 这里简单按 64 切片
        out: list[list[float]] = []
        BATCH = 64
        for i in range(0, len(texts), BATCH):
            chunk = texts[i:i + BATCH]
            resp = self._client.embeddings.create(model=self._model, input=chunk)
            out.extend([d.embedding for d in resp.data])
        return out

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model


# ---------- 工厂 ----------

_singleton: EmbeddingProvider | None = None


def get_embedder() -> EmbeddingProvider:
    """全局单例. 避免重复加载模型 / 重复建连接."""
    global _singleton
    if _singleton is not None:
        return _singleton

    provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()

    if provider == "api":
        base_url = os.getenv("EMBEDDING_BASE_URL", "https://api.siliconflow.cn/v1")
        api_key = os.getenv("EMBEDDING_API_KEY", "")
        model = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
        dimension = int(os.getenv("EMBEDDING_DIM", "1024"))
        if not api_key:
            raise RuntimeError(
                "EMBEDDING_PROVIDER=api 但缺 EMBEDDING_API_KEY. "
                "去 https://cloud.siliconflow.cn 注册拿个免费 key."
            )
        _singleton = OpenAICompatibleProvider(base_url, api_key, model, dimension)
    else:
        _singleton = LocalBGEProvider()

    return _singleton
