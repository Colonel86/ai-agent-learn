# L7 · Schema 提案 + Critic 精炼循环（proposal / critic / LoopAgent）

> 课程：Agentic Knowledge Graph Construction（DeepLearning.AI × Neo4j，C2）
> 本课任务（对应课程 Lesson 6）：构建 Structured Data 工作流的**第三环**——Schema Proposal Agent。给定 `approved_user_goal` 和 `approved_files`，产出 `approved_construction_plan`（一组把 CSV 转成 node/relationship 的**构建规则**）。本课引入两个新范式：**critic pattern（提案-批评双 agent）**，和用 **LoopAgent** 把它们塞进循环精炼。

## 0. 在架构里的位置：一个"内含多 agent"的 agent

前两环各是单个 LLM agent；本课这个"agent"其实内部是**一整套 agent 协作**。顶层 coordinator 只有三样工具：`refinement_loop_as_tool`（一个循环 agent 被当工具用）、`get_proposed_construction_plan`、`approve_proposed_construction_plan`。真正干活的是那个 loop：

```
schema_refinement_loop (LoopAgent, max_iterations=2)
 ├─ schema_proposal_agent   提方案：为每个文件产出 node/relationship 构建规则
 ├─ schema_critic_agent     挑刺：只读，输出 'valid' 或 'retry + 反馈清单'
 └─ CheckStatusAndEscalate  判停：看 critic 的 feedback 决定是否 escalate 退出循环
        ↑____________________ 循环，直到 valid 或达 max_iterations ____________________|
```

- **输入**：`approved_user_goal`、`approved_files`
- **输出**：`approved_construction_plan`
- **工具**：`get_approved_user_goal`、`get_approved_files`、`sample_file`、`search_file`、`propose_node_construction`、`propose_relationship_construction`、`remove_*`、`get_/approve_proposed_construction_plan`

## 1. Construction Rule：不是直接建图，而是产出"怎么建"的规则

关键概念：agent 不直接写图，而是为每个文件产出一条 **construction rule**（构建规则），汇成 construction plan（一个 dict，key 唯一）。两类规则：

```python
# node 规则：文件 → 一类节点
{ "construction_type": "node",
  "source_file": "parts.csv",
  "label": "Part",                    # 节点标签（人/地/物的"物"）
  "unique_column_name": "part_id",    # CSV 里唯一标识列
  "properties": ["part_name", ...] }  # 要导入成节点属性的列（可只取子集）

# relationship 规则：文件 → 一类关系
{ "construction_type": "relationship",
  "source_file": "part_supplier_mapping.csv",
  "relationship_type": "SUPPLIED_BY",
  "from_node_label": "Part",  "from_node_column": "part_id",
  "to_node_label": "Supplier", "to_node_column": "supplier_id",
  "properties": [...] }
```

`propose_node_construction` 内部同样 trust-but-verify——先用 `search_file` 确认 unique 列真的存在于文件里，否则报错让 agent 重来：

```python
def propose_node_construction(approved_file, proposed_label, unique_column_name,
                              proposed_properties, tool_context):
    search_results = search_file(approved_file, unique_column_name)   # 校验列存在
    if search_results["search_results"]["metadata"]["lines_found"] == 0:
        return tool_error(f"{approved_file} does not have column {unique_column_name}. ...")
    plan = tool_context.state.get(PROPOSED_CONSTRUCTION_PLAN, {})
    plan[proposed_label] = { "construction_type": "node", "source_file": approved_file, ... }
    tool_context.state[PROPOSED_CONSTRUCTION_PLAN] = plan             # 累加进 plan，label 作 key
    return tool_success(NODE_CONSTRUCTION, plan[proposed_label])
```

因为 agent 在循环里跑，可能需要撤销之前的提案，所以还配了 `remove_node_construction` / `remove_relationship_construction`。

## 2. 把数据建模的"手艺"写进 prompt

LLM 会做图建模但"不够精"。本课把 data engineer 拿到一堆文件时的判断经验**显式编码进 proposal agent 的 hints**（本课最长的一段 prompt）：

| 线索 | 判定 |
|---|---|
| 文件名单数 + 只有 1 个唯一标识 | 大概率是 **node** |
| 文件名像两个东西的组合（如 part_supplier） | 大概率是 **full relationship** |
| 文件名像节点，但有多个唯一标识 | node + **reference relationship**（外键） |
| 没有单一唯一标识 | 强烈暗示是 full relationship |

- **full relationship**：专门的关系文件，含 source/destination 节点的引用，**自己没有唯一标识**——这是最强判据（类比关系库的 join table）。
- **reference relationship**：藏在 node 文件里的外键列，列名往往暗示目标节点和关系类型（类比外键；层级 has/contains/成员关系，或 knows/see-also 这类同类自引用）。
- 收尾硬要求：**结果 schema 必须是全连通图，不能有孤立分量**（否则"算不上图，也没用"）。

CoT 里还要求 agent 每发现一个疑似唯一标识，就用 `search_file`（Python 版 grep）**验证它是否真的唯一**——看该值是否多次出现。

> **架构师视角**：这段 prompt 的价值不在于让 LLM "更聪明"，而在于把**领域专家的启发式规则**从工程师脑子里搬进了系统、还可版本化迭代。同样一句"文件名是两个东西的组合就可能是关系"，人做数据建模时是隐性直觉，写进 prompt 后它变成可审查、可 A/B、可被 critic 校验的显式资产。这正是 agentic 构图相对手写 ETL 脚本的分野：ETL 把规则写死在代码里，agentic 把规则写成 prompt+工具，让系统能对**没见过的文件集**泛化，同时保留人类经验作为护栏。

## 3. Critic Pattern：提案 agent + 批评 agent

第二个 agent 是 **critic**——同样是 KG 建模专家，但职责不是提案而是**挑刺**。它的工具是**只读的**（`get_*` + `sample_file` + `search_file`），无法直接改 schema，只能提意见：

critic 检查清单（hints）：唯一标识真唯一吗（composite 复合键不接受）？某些 node 其实该是 relationship 吗？能否从源数据手动追溯回答一个假想问题？每个 node 都连通吗、缺哪些关系？有没有缺失的层级容器关系？**有没有冗余关系**（语义等价或互为逆）——提案 agent 常"过于热情"造出多余关系。

critic 的输出约定极简：

```
schema 没问题 → 回单个词 'valid'
有问题       → 回 'retry' + 一份简洁 bullet list 反馈
```

最妙的是 critic 怎么把反馈交回去——用 **`output_key`**：

```python
schema_critic_agent = LlmAgent(
    name="schema_critic_agent_v1",
    model=llm,
    instruction=critic_agent_instruction,
    tools=schema_critic_agent_tools,     # 全是只读工具
    output_key="feedback",               # ★ 把 final 响应文本自动存进 state["feedback"]
    before_agent_callback=log_agent,
)
```

而 proposal agent 的 prompt 里有 `<feedback>{feedback}</feedback>` 模板槽——**ADK 在拼 prompt 时会用 `state["feedback"]` 的值填进去**（用 XML 式分隔符是因为 feedback 可能很长、初始为空，防止和 prompt 其余部分混淆）。于是闭环成立：critic 写 `feedback` → 下一轮 proposal 读 `feedback` → 针对性改进。

> **对比 11-design-patterns.md 的 evaluator-optimizer（≈Reflection）**：这就是 evaluator-optimizer 模式的教科书实现——proposal 是 optimizer、critic 是 evaluator，两者循环直到评估通过。对照 L5 的"人肉确认"和 L4 的"单向委派"，本课是本课程第一次把**评估这一环也自动化**。设计矩阵里选这个模式的信号：**任务有明确质量标准、单次生成不可靠、且验证比生成容易**——schema 建模恰好满足（对不对连通、唯一键真不真唯一，验证成本远低于从零建模）。critic 用只读工具是刻意的职责隔离：评估者不该有权改被评估对象。

## 4. LoopAgent + 自定义判停 agent

光有 proposal 和 critic 还不够——谁决定停？第三个是**自定义 agent**（继承 `BaseAgent`，不是 LLM agent，纯代码逻辑）：

```python
class CheckStatusAndEscalate(BaseAgent):
    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        feedback = ctx.session.state.get("feedback", "valid")   # 没 feedback 就当 valid
        should_stop = (feedback == "valid")
        yield Event(author=self.name, actions=EventActions(escalate=should_stop))
        # escalate=True → 跳出 loop；escalate=False → 继续下一轮
```

三个 sub-agent 塞进 ADK 的 **LoopAgent**（一个纯编排、零推理的 workflow agent）：

```python
schema_refinement_loop = LoopAgent(
    name="schema_refinement_loop",
    max_iterations=2,        # ★ 上限：最多循环 2 次，防止无限循环
    sub_agents=[schema_proposal_agent, schema_critic_agent,
                CheckStatusAndEscalate(name="StopChecker")],
    before_agent_callback=log_agent,
)
```

`max_iterations=2` 是安全阀：要么达成共识（critic 说 valid，escalate 退出），要么跑满 2 轮强制退出——绝不无限跑。跑满仍未通过时，控制权交回顶层 coordinator，由它 **human-in-the-loop** 问用户"我拿不准，你看怎么办"。

实际跑一次 verbose：`refinement_loop → proposal_v1 → critic → proposal（再来） → critic → 仍 retry`。讲师这次的运行里 critic 两轮都不满意（嫌关系有重叠、数据不全），于是 loop 到顶终止、把反馈甩回 coordinator 找人。这真实展示了 agent 的非确定性——不保证收敛，所以既要 `max_iterations` 兜底，又要人兜底。

而 proposal agent 单独跑（未经 critic）时表现其实相当好：为 assemblies/parts/products/suppliers 各建 node，还"很有创意"地识别出 `part_supplier_mapping.csv` 是 join table → 转成 `SUPPLIED_BY` 关系（而非节点），把 assemblies 里的外键转成 `INCLUDED_IN` 关系带 quantity 属性。

> **对比 L4 的委派 / L6 的可测试性**：本课把三种 ADK 编排原语凑齐了——L4 的 `sub_agents` 自动委派（LLM 驱动路由）、本课 `LoopAgent`（确定性循环编排）、以及 `AgentTool`（把整个 loop 当一个工具塞给 coordinator）。选型含义：**能用确定性 workflow agent（Loop/Sequential）就别让 LLM 去"自由发挥"控制流**——判停这种逻辑用一个 20 行的 `BaseAgent` 子类比让 LLM 自己决定何时停可靠得多。这呼应 11-design-patterns.md 的"最轻起步"原则：控制流能写死就写死，把 LLM 的不确定性关进单个 agent 内部。

## 5. 本课总结

| 要点 | 一句话 |
|---|---|
| construction rule | agent 产出"怎么建"的规则（node/relationship），不直接建图 |
| 建模手艺入 prompt | 把 node vs relationship 的判定启发式显式编码进 hints |
| critic pattern | proposal（可写工具）+ critic（只读工具）职责隔离 |
| output_key + 模板槽 | critic 写 `feedback` → ADK 注入 proposal 的 `<feedback>` 槽，闭环 |
| LoopAgent + 判停 | 纯代码 `CheckStatusAndEscalate` 靠 escalate 控停，`max_iterations` 兜底 |
| 不保证收敛 | 跑满仍失败 → 交回 coordinator 找人（human-in-the-loop） |

> **记忆点（引出 L8）**：到这里，从 CSV 构图的完整工作流（意图 → 选文件 → 提 schema）已经打通。L8 转向**非结构化数据**：从 markdown 文件抽图。它开头会"模拟"意图和文件建议两环的输出（这两环对 markdown 同样需要，但本课直接给），把焦点放在新角色 **Entity and Fact Type Proposal Agent**——它内部又是两个专职 sub-agent：**NER schema agent**（命名实体识别）+ **fact type extraction agent**（事实类型抽取）。你会看到本课的 proposal/critic 双 agent 骨架被复用到"从自由文本里定义抽什么实体、抽什么事实"的新问题上。

## 与我的资产映射

- 设计模式层：`agent/skills/agent-selection/11-design-patterns.md`（evaluator-optimizer/Reflection = 本课 proposal-critic 循环；确定性 workflow agent vs LLM 自由控制流的取舍）
- 观测·eval 层：`agent/skills/agent-selection/5-observability-eval.md`（critic 作为"inline LLM-judge"、`before_agent_callback` 打日志观测每个 sub-agent 进出）
- 工具层：`agent/skills/agent-selection/4-tools.md`（可写工具 vs 只读工具的职责隔离——评估者不该有权改被评估对象）
- 检索/数据层：`agent/skills/agent-selection/3-retrieval.md`（agentic 构图 vs 确定性 ETL：规则写进 prompt+工具以泛化到未见文件集）
- 框架层：`agent/skills/agent-selection/2-framework/`（ADK 三原语：sub_agents 委派 / LoopAgent / AgentTool）
- 面试包：`agent/interview/jd-senior-agent-engineer/`（critic pattern、如何防无限循环、output_key 传递 feedback 的机制）· `agent/interview/ai agent 评测.md`
- [[project_selection_matrix]] · [[project_asset_reuse]]
