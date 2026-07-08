# Career Twin · 职业分身

> AI 不替你做决定, 只帮你看清未来有哪几条路, 以及每条路的代价/风险/机会.

这是一个**自用 + 学习 AI** 的项目. 阶段 1 的目标:
- 跑通 3 个 Agent 的完整链路 (画像分析 → 市场情报 → 路线推演)
- 验证 "通用 LLM + 我的真实数据" 比直接问豆包好用
- 学会 Pydantic + Instructor 的结构化输出 (这是所有 Agent 项目的基础设施)

后续阶段路线见本仓库 chat 历史.

---

## 技术栈

| 层 | 选择 | 备注 |
|---|---|---|
| 编排 | **手写 orchestrator** | 故意不引入 LangGraph, 3 个 Agent 用不上图 |
| 结构化输出 | **Pydantic + Instructor** | 这是核心, 替代手写 JSON 解析 |
| 模型 | **DeepSeek-V3** (默认) | 便宜, 国内直连; 可一键切到 OpenAI/Qwen/Claude |
| 后端 | FastAPI | 自带异步 + Pydantic |
| 前端 | Next.js 15 + Tailwind | 单页面应用, 阶段 2 再加可视化 |

---

## 运行步骤 (Windows PowerShell)

### 1. 准备 API Key

```powershell
cd career-twin\backend
copy .env.example .env
# 编辑 .env, 填入 DEEPSEEK_API_KEY
# (在 https://platform.deepseek.com/ 注册, 充 10 元够用很久)
```

### 2. 启动后端

```powershell
cd career-twin\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# 国内推荐用阿里云镜像, 比 PyPI 快 100 倍
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
# 首次启动: 把 20 条种子岗位灌入 SQLite (重复执行会清空重灌)
python seed_jobs.py
# 注意: 必须用 python -m uvicorn, 不要直接 uvicorn,
# 否则 Windows 上可能走到全局 uvicorn, 加载错误的 Python 环境
python -m uvicorn main:app --reload --port 8001
```

验证: 浏览器打开 http://127.0.0.1:8000/health 应返回 `{"ok": true}`.

### 3. 启动前端

新开一个终端窗口:

```powershell
cd career-twin\frontend
npm install
npm run dev
```

> **PowerShell 上 npm 报错 "Cannot find module ... npm-prefix.js"?**
> 这是 Windows Node 安装的 PATH 顺序 bug. 解决: 编辑系统环境变量,
> 从 PATH 里删掉 `C:\Program Files\nodejs\node_modules\npm\bin`, 保留 `C:\Program Files\nodejs\`.
> 临时绕过: 用绝对路径 `& "C:\Program Files\nodejs\npm.cmd" install`.

打开 http://localhost:3000 , 表单已经预填了 "47 岁测试经理" 的画像, 直接点 "生成职业分身" 就会跑完整条链路.

---

## 项目结构

```
career-twin/
├── backend/
│   ├── models.py            # Pydantic 数据模型 (Agent 之间的契约)
│   ├── llm.py               # 统一 LLM 客户端 (切换厂商只改这里)
│   ├── orchestrator.py      # 手写编排, 10 几行串起 3 个 Agent
│   ├── main.py              # FastAPI 入口
│   ├── agents/
│   │   ├── persona.py       # Agent 1: 画像分析
│   │   ├── market.py        # Agent 2: 市场情报 (阶段 1 用 mock)
│   │   └── simulator.py     # Agent 3: 路线推演
│   └── data/
│       └── mock_market.json # 阶段 1 用的内部市场数据, 阶段 3 换 RAG
└── frontend/
    └── app/
        ├── page.tsx         # 输入表单 + 报告展示
        ├── types.ts         # 与后端模型对应的 TS 类型
        ├── layout.tsx
        └── globals.css
```

---

## 学习重点 (阶段 1)

读代码时建议按这个顺序:

1. **`models.py`** —— 整个项目的契约. 看 `Field(description=...)` 是怎么给 LLM 留提示的.
2. **`llm.py`** —— 看 Instructor 怎么把任意 OpenAI 兼容模型包成 "强制结构化输出" 的客户端.
3. **`agents/persona.py`** —— 最简单的 Agent. 一个 system prompt + 一个 user message + `response_model`.
4. **`agents/market.py`** —— 多了一个 "把本地数据塞进 prompt" 的模式, 是 RAG 的前身.
5. **`agents/simulator.py`** —— 最复杂的 Agent, 输入是前面两个 Agent 的结构化输出.
6. **`orchestrator.py`** —— 看这里就明白为什么阶段 1 用不上 LangGraph.

---

## 已知 TODO

- [ ] 阶段 2: 加入 reactflow 画路线树
- [ ] 阶段 2: 关键节点 (simulator) 换 Claude Sonnet
- [ ] 阶段 3: 抓取真实 Boss 直聘数据, 替换 mock_market.json
- [ ] 阶段 3: 向量化 + Chroma, Agent 2 改成 RAG
- [ ] 阶段 4: 加入 "每月体检" 跟踪自己技能补充进度
