# QA：消息协议与短期记忆（基于 L2 main.py 的答疑整理）

> 源头问题：`create_prompt` 里的 `+ state["messages"]` 是干什么的？短期记忆放在哪？
> 结论均可在 `code/L2/main.py` 用 `--verbose` 亲眼验证。

## 一、核心公式

```text
每轮发给 LLM 的完整输入 = system（每轮现拼的规则） + history（累积的事件轨迹）
```

- **system → 重建（rebuild）**：`create_prompt` 每轮重新 `format` 一条 system 消息放最前，它是配置，不是"发生过的事"，**从不进入 state 累积**
- **history → 追加（append）**：`state["messages"]` 靠 `Annotated[list, add_messages]` reducer 逐轮累积，只含 user / assistant / tool 三种角色

两个关键推论：

1. **LLM 是无状态的**：每轮全量重发，不是增量。`--verbose` 里"本轮 2 条 → 4 条 → 6 条消息"就是可视化证据；没有 `+ state["messages"]`，第二轮 LLM 就不知道上一轮调过什么工具、返回了什么，循环无法收敛。
2. **system 每轮重建是 L5 的伏笔**：正因 system 不进历史，L5 把指令搬进 store 后，optimizer 改写指令**下一轮立即生效**——若 system 也累积在 history 里，旧指令会赖着不走。

**triage_router 的对照**：它同样每次现拼 system/user prompt，但它是**单发调用**——两条消息进、结构化结果出，无循环无累积，连短期记忆都没有（纯函数式分类器）。其 system_prompt 动态构建在 L2 是伏笔，L4 兑现（few-shot 按邮件语义检索注入，每封的 system 都不同）、L5 再兑现（三段规则从 store 现读）。统一的设计原则：**凡是未来可能变化的 prompt，从第一天起就按运行时数据对待**——调用时 format，不在模块加载时算好。

## 二、短期记忆的定位

**短期记忆 = 本次运行的事件轨迹（history 区）+ 让它塞进窗口的管理机制（修剪/摘要/压实）**，不放 system prompt。它不只是"聊天"——tool 消息（日历结果、发信回执）也在其中。进程结束即消失；"跨运行还记得"是长期记忆（store）的事。

"记忆注入哪个区"是架构选择，三门课三种答案：

| 课程 | 记忆注入位置 | 理由 |
|---|---|---|
| 12 (LangGraph) | 轨迹在 history；few-shot/指令进 system；semantic 以 ToolMessage 进 history | 规则性进 system，事件性进 history |
| 12a (Oracle) | 五段记忆全拼进 **user 消息**（`## Conversation Memory` 等分区），system 只解释分区语义 | 确定性装配，system 保持稳定 |
| 12b (MemGPT) | Core memory blocks **常驻 system 区**，agent self-edit | 少量高价值状态要常驻 + 可原地改写 |

取舍轴：system 区 = 高遵守优先级 + **prompt cache 红利**（前缀不变才命中，verbose 日志里的 `cached_tokens: 640`）；history 区 = 时序与角色结构完整、reducer 自动管理。12b 把记忆放 system 牺牲缓存，换常驻性和权威性。

## 三、四种角色的准确语义

| 角色 | 语义 | 关键点 |
|---|---|---|
| system | 规则/配置 | 每轮重建，不累积 |
| user | 任务与素材，**不一定是人** | L2 里 `请回复这封邮件 {...}` 是 triage_router 代码注入的；12a 连五段记忆都拼在 user 里 |
| assistant | LLM 的一切输出 | 带 `tool_calls` = 要调工具；**不带 = 最终回答，这就是 ReAct 循环的退出条件** |
| tool | 工具执行结果 | 带 `tool_call_id` 与发起调用的 assistant 消息配对（支持一轮并发多个调用） |

## 四、LangChain 类 ↔ API 角色映射

| LangChain 类 | API 角色 | `m.type` |
|---|---|---|
| SystemMessage | system | `"system"` |
| HumanMessage | user | `"human"` |
| AIMessage | assistant | `"ai"` |
| ToolMessage | tool | `"tool"` |

- 裸 dict `{"role": "system", ...}` 与 Message 对象**可混用**，LangChain 发请求前统一归一化（`create_prompt` 就是混着写的）
- `AIMessage` 比 API assistant 多带框架层元数据：解析好的 `tool_calls`、`usage_metadata`、`response_metadata`
- **判断消息类型用 `m.type` 字符串，别用 `isinstance`**（序列化往返后类可能变，type 稳定）

> 关联：`L1-Agent三大记忆类型与邮件助理蓝图.md`（长短期记忆分界）、`../../面试回答骨架.md`（12a/12b 分区语义那条共识）。
