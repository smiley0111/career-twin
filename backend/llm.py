"""统一的 LLM 客户端入口.

设计原则:
- 一个文件管所有模型, 切换厂商只改这里
- 用 Instructor 包一层, 强制结构化输出
- DeepSeek/通义/Qwen 都兼容 OpenAI 协议, 所以底层都用 openai SDK
"""
import os
from openai import OpenAI
import instructor
from dotenv import load_dotenv

load_dotenv()


def _build_client() -> tuple[instructor.Instructor, str]:
    """根据环境变量构造一个 Instructor 客户端 + 默认模型名."""
    api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL") or os.getenv("OPENAI_BASE_URL")
    model = os.getenv("DEEPSEEK_MODEL") or os.getenv("OPENAI_MODEL") or "deepseek-chat"

    if not api_key:
        raise RuntimeError(
            "未找到 API KEY. 请复制 .env.example 为 .env 并填入 DEEPSEEK_API_KEY"
        )

    raw = OpenAI(api_key=api_key, base_url=base_url)
    # Instructor 把 LLM 输出强制对齐到 Pydantic 模型, 失败自动重试
    client = instructor.from_openai(raw, mode=instructor.Mode.JSON)
    return client, model


client, DEFAULT_MODEL = _build_client()
