# career-twin 后端镜像 (FastAPI + Chroma RAG)
#
# 构建上下文 = career-twin/ 仓库根 (不是 backend/), 因为:
# - main.py 要读同级的 ../test-cases/*.json
# - 所以把 backend 和 test-cases 一起拷进镜像, 保持相对目录结构
#
# embedder 走 API (硅基流动), 镜像里不装 fastembed/onnxruntime, 又轻又躲开 DLL 坑.
FROM python:3.12-slim

# git: requirements.txt 里的 dodu-ai 是 git+https 安装, 需要 git
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先拷依赖清单单独装, 利用 Docker layer 缓存 (代码改了不用重装依赖)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 再拷代码 + 测试画像
COPY backend ./backend
COPY test-cases ./test-cases

WORKDIR /app/backend

# 平台会注入 $PORT (Railway/Fly 都是). 本地默认 8000.
ENV PORT=8000
EXPOSE 8000

# 启动: 先幂等 seed + 建向量索引 (平台文件系统是临时的, 每次冷启动都要保证数据在),
# 再拉起 uvicorn.
CMD ["sh", "-c", "python prestart.py && uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
