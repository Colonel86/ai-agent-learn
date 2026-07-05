# L8 · 非结构化数据的 Schema 提案：NER + Fact Type 双专家 Agent

> 课程：Agentic Knowledge Graph Construction（DeepLearning.AI × Neo4j，C2）
> 本课任务：为 markdown 产品评论设计**两个专家子 Agent**，共同产出"如何从非结构化文本抽取图谱"的**提案（plan）**——注意是提取计划，不是提取本身。

## 0. 本课定位与衔接（承 L7）

L7 处理的是**结构化数据**的 schema 提案：一个 proposer 提出 graph schema，一个 critic 挑刺，外面包一个 `refinement_loop_as_tool` 反复精炼——这是经典的 critic / evaluator-optimizer 模式。产出是 `approved_construction_plan`（CSV → 节点/关系的构建规则）。

L8 把镜头转向**非结构化数据**（markdown 格式的产品评论）。整条 unstructured 工作流开头同样有 user intent、file suggestion 两个 Agent（本课直接模拟它们的输出，不重复搭建），焦点放在新概念：**Entity and Fact Type Proposal Agent**。

```
结构化流水线(L5-L7)                    非结构化流水线(L8)
user intent ─► file suggestion ─►      user intent ─► file suggestion ─►
   schema proposal(critic loop)           Entity&FactType Proposal Agent
   └► approved_construction_plan              ├─ NER schema agent
                                              └─ fact type extraction agent
                                           └► approved_entity_types
                                              approved_fact_types
```

> **架构师视角**：这门课把"决定图谱长什么样"和"真正把数据搬进图谱"彻底拆开。L5-L8 全是 Agent 在**产出计划**（schema / construction plan / entity types / fact types），L9-L10 才是**工具执行计划**。Agent 只出现在需要判断力的建模环节，确定性搬运不浪费一次 LLM 调用——这是把 token 花在刀刃上的分层。

## 1. 一个 Agent，内含两个专家子 Agent

`Entity and Fact Type Proposal Agent` 由两个各司其职的子 Agent 组成，且它们的输出都是**计划而非结果**：

| 子 Agent | 职责 | 产出 |
|---|---|---|
| NER schema agent | 命名实体识别：读文本，找出"有哪些**类型**的实体" | `approved_entity_types`（如 Product / Issue / Feature / Location） |
| fact type extraction agent | 第二遍扫描：找出"这些实体之间会出现哪些**类型**的陈述" | `approved_fact_types`（三元组类型，如 Product-has_issue-Issue） |

关键区别（讲师反复强调）：NER agent 不抽取具体实体，只识别"有哪些实体类型可抽"；fact agent 不抽取具体事实，只提出"有哪些事实类型可抽"。两者合起来是一份支撑用户目标（把产品投诉沿制造流程回溯做根因分析）的**抽取蓝图**。

## 2. NER 子 Agent：三段式 instructions

instructions 沿用全课统一的三段拼装法（role/goal + hints + chain-of-thought），组合成一个字符串喂给 Agent：

```python
# ① 角色与目标：顶级 NLP 算法，只找"实体类型"，不抽实例
ner_agent_role_and_goal = """
  You are a top-tier algorithm designed for analyzing text files and proposing
  the kind of named entities that could be extracted ... relevant for a user's goal.
"""

# ② 提示：实体是 people/places/things/qualities，不是 quantities
#    两类实体 —— 见下表
ner_agent_hints = """... well-known entities / discovered entities ..."""

# ③ 思维链：先备料(get_user_goal / get_approved_files / get_well_known_types)
#    再 sample_file 采样 → 提出类型 → set_proposed_entities → 交用户审批
ner_agent_chain_of_thought_directions = """Prepare... Think step by step..."""
```

两类实体是这一课的核心设计：

| 类型 | 定义 | 例子 |
|---|---|---|
| **well-known** | 已存在于上一步结构化 schema 里的节点标签，若文本里也出现就一并抽 | Product、Part、Supplier |
| **discovered** | schema 里没有、但文本里高频出现且贴合用户目标的新实体 | Issue（投诉）、Feature（产品特性） |

设计规则里还有反面约束：**不要把定量信息当实体**（如别把 "Age" 提成实体，它应当是 Person 上的 `age` 属性）——这直接决定了图谱是"实体丰富"还是"节点爆炸"。

> **对比 11-design-patterns.md（propose-then-approve / human-in-the-loop）**：NER agent 走的是"提议→人审→批准"闭环，`set_proposed_entities` 与 `approve_proposed_entities` 是两个独立工具，Agent 提完必须停下等人点头。这不是 L7 那种 Agent-审 Agent 的 evaluator-optimizer 自动循环，而是把**人**放进 critic 位。建模阶段的判断成本高、错了代价大，所以留人工闸门；这正是设计模式选型里"自动化程度"与"可控性"的权衡。

## 3. NER 工具集：propose / approve 双工具 + well-known 抽取

工具遵循全课一致的"先 propose 再 approve"模式（此处无花哨逻辑）：

```python
PROPOSED_ENTITIES = "proposed_entity_types"
APPROVED_ENTITIES = "approved_entity_types"

def set_proposed_entities(proposed_entity_types, tool_context):
    tool_context.state[PROPOSED_ENTITIES] = proposed_entity_types   # 只写 proposed
    return tool_success(PROPOSED_ENTITIES, proposed_entity_types)

def approve_proposed_entities(tool_context):
    if PROPOSED_ENTITIES not in tool_context.state:                 # 没提议不许批
        return tool_error("No proposed entity types to approve...")
    tool_context.state[APPROVED_ENTITIES] = tool_context.state[PROPOSED_ENTITIES]
    return tool_success(APPROVED_ENTITIES, ...)
```

关键 getter 工具 `get_well_known_types`：从上一步的 `approved_construction_plan` 里抽出所有 `construction_type == "node"` 的 label，作为"已知实体类型"喂给 NER agent——这是把结构化 schema 的成果**接力**给非结构化建模的那根线：

```python
def get_well_known_types(tool_context):
    plan = tool_context.state.get("approved_construction_plan", {})
    approved_labels = {e["label"] for e in plan.values()
                       if e["construction_type"] == "node"}
    return tool_success("approved_labels", approved_labels)
```

## 4. 运行 NER：初始 state 与"提议但不擅自批准"

因为 Agent 处在长工作流中段，要手工构造它假设已积累的 state：`approved_user_goal`、`approved_files`（10 个 markdown 评论文件）、`approved_construction_plan`（此处只填 node 部分，relationship 本课用不到）。

跑一条消息 `"Add product reviews to the knowledge graph to trace product complaints back through the manufacturing process."`，观察两个验收点：
1. Agent 产出合理的 proposed entities（视频里得到 Product / Issue / Feature / Location 等）；
2. **只写进 `proposed_entity_types`，没有自动写 `approved_entity_types`**——正确地停在等待人审。

讲师提到一个真实坑：Agent 常把"Assembly（组装动作）"和"Assembly（组装件实体）"混为一谈——因为 well-known 列表里有 "Assembly"，文本里又有"组装家具很费劲"的抱怨。根治办法是上一课 schema 提案时给每个 label 存一段 description。LLM 输出有随机性，不满意可重跑一格。

## 5. Fact Type 抽取子 Agent：三元组类型

第二个子 Agent 找"事实类型"。事实 = **三元组 (subject, predicate, object)**，subject/object 必须是已批准的实体类型，predicate 描述关系：

```python
fact_agent_hints = """
  Do not propose specific individual facts, but the general TYPE of facts.
  e.g. NOT "ABK likes coffee" but "Person likes Beverage".
  Facts are triplets (subject, predicate, object) where subject/object are
  approved entity types ...
  - the predicate must appear in the source text. Do not guess.
"""
```

与 NER 的一处**微妙差别**：NER 一次性 `set` 整个实体类型列表；fact agent 用 `add_proposed_fact` **逐条**添加事实类型。讲师点明这是刻意取舍：逐条 = 更多轮次 = 更贵的 token，但换来每条都能被单独校验/纠错——是"成本 vs 质量"的显式权衡。

## 6. Fact 工具的护栏：subject/object 必须已批准

fact agent 的工具比 NER 多一层 sanity check，这也是**把两者拆成两个 Agent 的意义**——分开才能在中间插校验：

```python
def add_proposed_fact(approved_subject_label, proposed_predicate_label,
                      approved_object_label, tool_context):
    approved_entities = tool_context.state.get(APPROVED_ENTITIES, [])
    if approved_subject_label not in approved_entities:      # 护栏：主语必须已批准
        return tool_error(f"Approved subject label {approved_subject_label} not found. Try again.")
    if approved_object_label not in approved_entities:       # 护栏：宾语必须已批准
        return tool_error(f"Approved object label {approved_object_label} not found. Try again.")
    current = tool_context.state.get(PROPOSED_FACTS, {})
    current[proposed_predicate_label] = {                    # 存成 {谓词: 三元组} 字典
        "subject_label": approved_subject_label,
        "predicate_label": proposed_predicate_label,
        "object_label": approved_object_label }
    tool_context.state[PROPOSED_FACTS] = current
    return tool_success(PROPOSED_FACTS, current)
```

标签不在批准列表时，工具**主动注入一条 error 回传给 Agent**，让它重试——这是用工具返回值反向纠偏 Agent 行为。逐条添加正是为了"一次纠一条"。

> **架构师视角**：护栏写在**工具**里而不是 prompt 里。prompt 里的"只用已批准类型"是软约束（LLM 可能违反），工具里的 `if not in: return error` 是硬约束（违反就打回）。生产级 Agent 的可靠性靠的就是这种"软提示 + 硬校验"双层：prompt 引导方向，工具兜底正确性。fact 与 entity 的因果依赖（fact 依赖 entity 已定）被编码成工具的前置检查,而非寄望模型记住顺序。

## 7. 运行 fact agent：一次真实的失败与重试

fact agent 的初始 state 直接**复制 NER agent 的 end state**（真实多 Agent 系统里它们顺序运行、共享 state）。跑 `"Propose fact types that can be found in the text."`：

视频里第一次跑翻车了——Agent 用纯文本给出了提案，却**没真正调用 `add_proposed_fact` 工具**，导致 session state 里没有 proposed facts。讲师的处理：直接重跑（真实系统里会自动检测"无 proposed facts 就 retry"）。第二次成功，提出 `Product has_issue Issue`、`Product includes_feature Feature`、`Product used_in_location Location` 等，并正确停在等待审批。审批后 `approved_fact_types` 落定。

得到的关键产物（供 L10 复用）：
```python
approved_entities   = ['Product', 'Issue', 'Feature', 'Location']
approved_fact_types = {'has_issue':       {'subject_label':'Product','predicate_label':'has_issue','object_label':'Issue'},
                       'includes_feature':{...'Feature'},
                       'used_in_location':{...'Location'}}
```

## 本课总结

| 要点 | 一句话 |
|---|---|
| 双专家子 Agent | NER 找实体类型 + fact agent 找事实类型，输出是抽取**计划**不是抽取 |
| well-known vs discovered | 复用结构化 schema 的标签 + 发现文本里的新实体，两条腿走路 |
| propose-then-approve | 提议与批准是两个工具，人审插在中间（human-in-the-loop critic） |
| 工具即护栏 | fact 的主宾必须是已批准实体，工具用 return error 硬性打回重试 |
| 逐条 vs 批量 | fact 逐条 add，多轮次换单条可校验——成本/质量的显式权衡 |

> **记忆点（引出 L9）**：到这里，结构化的 `construction_plan` 与非结构化的 `entity_types / fact_types` 两份**计划**都已备齐,但图谱一个节点都还没建。L9 开始"执行"：先用**纯确定性工具（无 Agent）**把 CSV 按 construction plan 搬进 Neo4j，构出 domain graph。

## 与我的资产映射

- 设计模式层：`agent/skills/agent-selection/11-design-patterns.md`（propose-approve 的 human-in-the-loop critic;与 L7 的 evaluator-optimizer 自动循环对照）
- 工具层：`agent/skills/agent-selection/4-tools.md`（工具即护栏——软 prompt + 硬校验双层可靠性）
- 面试包：`07-safety-guardrails`（工具返回 error 反向纠偏）、`08-foundations-function-calling-and-rag`（NER / triple 抽取）
- [[project_selection_matrix]]
