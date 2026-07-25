# 12c · Mem0 Hands-On(自设计动手课)

> **性质**:不是外部课程,是基于 mem0 官方文档(docs.mem0.ai,2026-07)自设计的动手实验,
> 目的是把 [`Memory框架/框架现状.md`](../Memory框架/框架现状.md) 里对 mem0 的纸面判断全部落到代码验证。
> **栈**:DeepSeek API + fastembed 本地 embedding + 嵌入式向量库(Chroma → 后期换 pgvector),沿用课程 12 系列的本地化标准栈。

## 与已有课程的关系

| 课程 | 框架 | 控制权模式(框架现状.md §五) |
|---|---|---|
| 12(LangGraph/LangMem) | 混合派 | 触发 LLM/代码,内容 LLM |
| 12a(Oracle 26ai) | 确定性派 | 触发代码,内容代码规则 + LLM |
| 12b(Letta/MemGPT) | 自治派 | 触发 LLM,内容 LLM |
| **12c(mem0,本课)** | **sidecar 派** | **触发代码(显式 add),内容 LLM(两阶段抽取 + 消解)** |

四门跑完,控制权四象限每格都有亲手实现,面试里"四派光谱"就不是背的了。

## 课程表

| 课 | 主题 | 对应官方文档 | 要验证的判断 |
|---|---|---|---|
| **L1** | 快速上手:最小闭环(add/search/get_all/history) | `open-source/python-quickstart` | 跑通本地栈,history 表初见 |
| **L2** | 写路径解剖:ADD/UPDATE/DELETE/NOOP 消解实验 | `core-concepts/memory-operations/add` | ⭐ 造 10 组矛盾对话测消解判对率——完成框架现状.md §2.7 待验证① |
| **L3** | 读路径:search 打分 / metadata 过滤 / threshold | `memory-operations/search`、`features/metadata-filtering` | 相关性/重要性/时近性加权是否可观察 |
| **L4** | 作用域:user_id / agent_id / run_id 隔离实验 | 官方 scopes 文档 | 多租户隔离是否严格 |
| **L5** | 定制写入:custom instructions + 写入分流 | `features/custom-instructions` | "关键事实确定性写入,体验型记忆自动抽取"能否落地 |
| **L6** | 换底座:Chroma → pgvector(复用 12a 的 PG) | `components/vectordbs/dbs/pgvector` | "mem0 是存储之上的一层"——迁移成本几行配置 |
| L7(可选) | mini 项目:跨会话个性化聊天助手 | `cookbooks/companions/*` | 端到端体感 + 延迟/成本实测(§2.7 待验证②) |
| L8(可选) | graph memory(Kuzu 嵌入式)/ REST server(docker) | `open-source/features/rest-api` 等 | 关系记忆与服务化形态 |

## 学习方法

每课节奏一致:**跑 `code/Lx/main.py` → 对照 README 观察点 → 蒸馏一篇 `notes/Lx-*.md`**(纯文字 + mermaid,不贴截图)。
L1–L6 是主线,L7/L8 视兴趣。

## 目录

```text
12c-Mem0 Hands-On/
├── README.md          # 本文件
├── code/              # 每课独立可运行 demo(共享一个 .venv)
│   ├── README.md      # 环境搭建(一次性)
│   ├── .env.example
│   └── L1/ L2/ ...
└── notes/             # 跑完每课后的蒸馏笔记
```

> **最后核对:2026-07**
