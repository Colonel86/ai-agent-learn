# EP08: End-to-End System（端到端系统 — 把所有模块拼成完整客服助手）

> 学习日期：2026-04-21
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI · Building Systems with the ChatGPT API（Isa Fulford）

---

## 本课概览

| 主题 | 核心内容 | 重要程度 |
|---|---|---|
| 7 步 Pipeline | 把前几课的模块串成完整流水线 | ⭐⭐⭐ |
| 对话历史管理 | all_messages 累积上下文，支持多轮追问 | ⭐⭐⭐ |
| 双重 Moderation | 输入侧 + 输出侧各做一次安全过滤 | ⭐⭐⭐ |
| 模型自评兜底 | Step 6 评估回答质量，不合格转人工 | ⭐⭐ |
| Panel 聊天 UI | 用 `panel` 库快速搭出可交互的 chatbot 界面 | ⭐⭐ |
| 持续迭代思路 | 上线后监控多轮输入，按需优化各步 | ⭐⭐ |

> **关键洞察**：这节课的价值不是某个新技术，而是**系统思维的落地**——把 Moderation、Extraction、RAG 检索、生成、输出检查、质量评估这六个独立模块，用一个函数 `process_user_message` 串成有状态的流水线，同时用 `all_messages` 维护多轮对话上下文。这正是构建生产级 LLM 应用的标准范式。

---

## 一、完整 7 步 Pipeline

```
用户输入 (user_input)
    │
    ▼
Step 1: Moderation API（输入侧）
    ├── flagged → 返回拒绝消息，终止
    └── pass ↓
    ▼
Step 2: 提取产品类别 & 名称列表
    │   utils.find_category_and_product_only()
    │   utils.read_string_to_list()
    ▼
Step 3: 查询产品详情（RAG 检索）
    │   utils.generate_output_string()
    │   若无匹配产品 → product_information = ""
    ▼
Step 4: 生成回答
    │   system_message + 用户消息 + 产品信息 + 对话历史
    │   get_completion_from_messages(all_messages + messages)
    ▼
Step 5: Moderation API（输出侧）
    ├── flagged → 返回拒绝消息，终止
    └── pass ↓
    ▼
Step 6: 模型自评（回答是否充分？）
    │   把 user_input + final_response 交给模型评估
    ▼
Step 7: 路由决策
    ├── 自评 Y → 返回 final_response 给用户
    └── 自评 N → 返回"转人工"消息
```

---

## 二、核心函数 `process_user_message`

```python
def process_user_message(user_input, all_messages, debug=True):
    delimiter = "```"

    # Step 1: 输入安全检查
    response = openai.Moderation.create(input=user_input)
    if response["results"][0]["flagged"]:
        return "Sorry, we cannot process this request."

    # Step 2: 提取产品列表
    category_and_product_response = utils.find_category_and_product_only(
        user_input, utils.get_products_and_category()
    )
    category_and_product_list = utils.read_string_to_list(category_and_product_response)

    # Step 3: 查询产品详情
    product_information = utils.generate_output_string(category_and_product_list)

    # Step 4: 生成回答
    system_message = """
    You are a customer service assistant for a large electronic store.
    Respond in a friendly and helpful tone, with concise answers.
    Make sure to ask the user relevant follow-up questions.
    """
    messages = [
        {'role': 'system',    'content': system_message},
        {'role': 'user',      'content': f"{delimiter}{user_input}{delimiter}"},
        {'role': 'assistant', 'content': f"Relevant product information:\n{product_information}"}
    ]
    final_response = get_completion_from_messages(all_messages + messages)
    all_messages = all_messages + messages[1:]  # 累积对话历史（不含 system）

    # Step 5: 输出安全检查
    response = openai.Moderation.create(input=final_response)
    if response["results"][0]["flagged"]:
        return "Sorry, we cannot provide this information."

    # Step 6: 模型自评
    eval_user_message = f"""
    Customer message: {delimiter}{user_input}{delimiter}
    Agent response: {delimiter}{final_response}{delimiter}
    Does the response sufficiently answer the question?
    """
    evaluation_response = get_completion_from_messages([
        {'role': 'system', 'content': system_message},
        {'role': 'user',   'content': eval_user_message}
    ])

    # Step 7: 路由
    if "Y" in evaluation_response:
        return final_response, all_messages
    else:
        return "I'm unable to provide the information you're looking for. I'll connect you with a human representative for further assistance.", all_messages
```

---

## 三、对话历史管理

### 设计要点

- `all_messages` 从外部传入，函数内部**追加并返回**，由调用方持有状态
- 每轮只追加 `messages[1:]`（跳过 system message），避免 system prompt 在历史中重复堆叠
- 产品信息以 `assistant` role 注入（`Relevant product information:\n{product_information}`），让模型把它当作"自己已知的上下文"

### 多轮追问示例

```
用户: 你们有哪些电视？
助手: 我们有 CineView 4K / 8K / OLED，SoundMax 家庭影院…

用户: 最便宜的是哪款？    ← all_messages 已包含上一轮
助手: SoundMax Soundbar，199.99 美元

用户: 给我详细介绍一下最贵的    ← 上下文连续
助手: CineView 8K TV，2999.99 美元，65寸，8K HDR…
```

---

## 四、Panel 聊天 UI

用 `panel` 库快速搭出可交互界面，适合 Notebook 内演示：

```python
import panel as pn
pn.extension()

panels = []
context = [{'role': 'system', 'content': "You are Service Assistant"}]

def collect_messages(debug=False):
    user_input = inp.value_input
    if not user_input:
        return
    inp.value = ''
    global context
    response, context = process_user_message(user_input, context, debug=False)
    context.append({'role': 'assistant', 'content': response})
    panels.append(pn.Row('User:',      pn.pane.Markdown(user_input, width=600)))
    panels.append(pn.Row('Assistant:', pn.pane.Markdown(response,   width=600,
                                        style={'background-color': '#F6F6F6'})))
    return pn.Column(*panels)

inp = pn.widgets.TextInput(placeholder='Enter text here…')
button = pn.widgets.Button(name="Service Assistant")
dashboard = pn.Column(inp, pn.Row(button),
                      pn.panel(pn.bind(collect_messages, button),
                               loading_indicator=True, height=300))
dashboard
```

> `panel` 只是演示工具，生产环境会换成 Streamlit / FastAPI + 前端框架。

---

## 五、设计模式总结

### 双重 Moderation 的必要性

| 检查点 | 目标 | 触发时的处置 |
|---|---|---|
| Step 1（输入侧）| 拦截恶意用户输入 | 直接拒绝，不进入后续步骤 |
| Step 5（输出侧）| 防止模型意外产出有害内容 | 拒绝返回，可选转人工 |

两道关卡缺一不可：输入侧防攻击，输出侧防模型幻觉/越界。

### `all_messages` 状态机设计

```
调用方持有 context（all_messages）
    └── 每次调用 process_user_message(user_input, context)
            └── 函数返回 (response, updated_context)
    └── 调用方更新 context，下次传入
```

这是**函数式状态管理**：函数无副作用，状态由调用方显式维护，方便测试和调试。

---

## 六、上线后的迭代思路

监控大量真实输入后，可能发现：

- 某些 prompt 提取产品不准 → 优化 Step 2 的提取 prompt
- 某些步骤在简单问题中完全不必要 → 按问题类型短路跳过
- 精确关键词匹配不够用 → Step 3 换成 Embeddings 模糊检索
- 特定类型问题模型自评总判 N → 调整 Step 6 的评估 rubric

> 这正是 EP09 将要讨论的**评估与迭代**话题。

---

## 七、与前序课程的关系

| 课程 | 提供的模块 | 在本课的位置 |
|---|---|---|
| EP04 | Moderation API | Step 1、Step 5 |
| EP05 | CoT / 分类 | Step 2 的思路基础 |
| EP06 | Chaining Prompts + RAG 检索 | Step 2、Step 3、Step 4 |
| EP07 | 输出检查 + 模型自评 | Step 5、Step 6、Step 7 |
| **EP08** | **端到端组装 + 对话历史 + UI** | **全部串联** |
