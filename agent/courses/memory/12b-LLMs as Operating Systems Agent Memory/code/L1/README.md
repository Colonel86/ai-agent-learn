# L1 从零实现自编辑记忆 — 本地演示项目

把 `Implementing_Editable_Memory.ipynb`（12b·L1）改造成可直接命令行运行的演示。核心思想（MemGPT）：**把"编辑记忆"做成工具交给 LLM 自己调**——LLM 是程序里最聪明的部件，记忆管理不该硬编码。

## 演示的递进结构

```mermaid
flowchart LR
    A["① 无记忆<br/>答不出名字"] --> B["② 只读记忆<br/>人手写进 prompt"]
    B --> C["③ save 工具·单步<br/>LLM 自己写记忆<br/>但存/答二选一"]
    C --> D["④ agentic loop<br/>tool call 继续循环<br/>纯文本才交还用户"]
    D --> E["⑤ 新会话验证<br/>历史清零仍答对"]
```

- **核心循环**：`agent_step` 里 `while True` 调 LLM——返回 tool call 就执行 `core_memory_save`、把工具结果喂回消息列表继续；返回纯文本就跳出循环交还用户。这就是 MemGPT"有些工具中断循环（发消息给用户），有些不中断（编辑记忆）"的最简版
- **记忆每轮重新拼装**：`[MEMORY]` 作为第二条 system 消息注入，永远反映最新状态
- **⑤ 的意义**：`chat_history=[]` 下仍能答对，证明起作用的是记忆而非会话历史 → 跨会话持久

## 运行

全课程共用 `code/` 根目录的一个 venv 与 `.env`（见 `code/README.md`），L1 不需要起任何服务：

```bash
cd L1
../.venv/bin/python main.py
```

## 与课程 notebook 的差异

| 差异点 | notebook | 本项目 | 原因 |
|---|---|---|---|
| 模型 | `gpt-4o-mini` | `.env` 中 `MODEL`（deepseek-v4-flash） | 本地用 DeepSeek 的 OpenAI 兼容 API |
| thinking | — | DeepSeek 时 `extra_body` 显式关闭 | v4 默认开 thinking，拖慢演示且与 tool call 交互不稳 |
| 工具结果回填时机 | 先回填"Updated memory"再执行工具（**回填的是旧状态**） | 先执行再回填 | 修复原 notebook 的顺序 bug |
| 多 tool call | 只取 `tool_calls[0]` | 遍历全部并逐个回 `tool` 消息 | OpenAI 协议要求每个 tool_call_id 都有应答 |
| 依赖 | `letta==0.6.50` | 只留 `openai` + `dotenv` | letta 是 L3+ 才用的 |
| 语言 | 英文 Bob | 中文张伟（工具 schema 保留英文） | 演示直观；schema 是 function calling 约束 |
