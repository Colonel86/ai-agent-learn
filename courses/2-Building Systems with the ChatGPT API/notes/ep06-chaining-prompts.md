# EP06: Chaining Prompts（链式 Prompt — 把复杂任务拆成子任务）

> 学习日期：2026-04-17
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI · Building Systems with the ChatGPT API（Isa Fulford）

---

## 本课概览

| 主题 | 核心内容 | 重要程度 |
|---|---|---|
| CoT vs Chaining | 单次长 Prompt vs 多次小 Prompt | ⭐⭐⭐ |
| 状态机视角 | 程序维护 state，按状态调不同 Prompt | ⭐⭐⭐ |
| 三步流水线 | 提取 → 查询 → 回答 | ⭐⭐⭐ |
| 动态加载上下文 | 按需把产品信息塞进 Prompt | ⭐⭐⭐ |
| 上下文长度限制 | 避免一次性塞进所有目录 | ⭐⭐ |
| 外部工具调用 | 在链的某一步调用 API / DB / 知识库 | ⭐⭐ |
| Embeddings 预告 | 模糊检索，弥补精确匹配的不足 | ⭐⭐ |

> **关键洞察**：**Chain-of-Thought** 是让模型"一次调用内按步骤想"；**Chaining Prompts** 是**把复杂工作流拆成多次调用**，**程序本身维护状态机**——状态在代码里，决策在模型里。
>
> 这也是**复杂 LLM 系统 → AI Agent** 的分水岭：Agent 本质上就是一个由状态、路由、工具调用组成的链。

---

## 一、为什么要拆 Prompt —— 两个类比

### 类比 1：一口气做一桌菜 vs 分阶段做

- **一口气**：同时管理多种食材、多种火候——容易漏掉、错位、混乱
- **分阶段**：一个组件做到位再做下一个——更可控，出错概率低

### 类比 2：意大利面式代码 vs 模块化程序

- 长 Prompt 像一堆耦合在一起的代码块，规则互相牵连 → 难调试
- 多个 Prompt 就像独立函数，**每个只处理一个状态**

> 适用判断：**问题有很多条可能同时适用的规则**时 → 拆。规则少、场景单一时 → 一个 Prompt 更省事。

---

## 二、CoT vs Chaining

| 维度 | Chain-of-Thought（EP05）| Chaining Prompts（EP06）|
|---|---|---|
| 调用次数 | **1 次** | **N 次** |
| 状态 | 隐含在一次推理中 | **程序显式维护** |
| 规则量 | 少到中等 | 多（每个状态一套指令）|
| 上下文需求 | 固定 | **可按需动态注入** |
| 调用工具 / API | 不方便 | **可以在链的某一步调用** |
| 调试 / 观测 | 整段输出一起看 | **每步可独立测试** |
| 成本 | 单次但可能长 | 多次但每次更短 |

> **核心判据**：**需不需要"根据上一步结果决定下一步"**。需要 → 必须 Chaining。

---

## 三、三步流水线（课程主例）

### 场景
客户问："给我讲讲 SmartX ProPhone 和 FotoSnap DSLR 相机。还有你们的电视。"

### 流水线

```
[Step 1] Extraction Prompt
  输入：用户消息
  输出：JSON 格式的 {category, products} 列表
           │
           ▼
[Step 2] 本地查询（非 LLM）
  输入：JSON 列表
  动作：查字典拿到完整产品描述
  输出：结构化产品信息字符串
           │
           ▼
[Step 3] Answer Prompt
  输入：用户消息 + Step 2 得到的产品信息
  输出：对用户的最终回复
```

### 3.1 Step 1：提取产品和分类

**System message（关键部分）**：

```text
You will be provided with customer service queries, delimited with ####.
Output a Python list of objects, where each object has either:
  'category': <one of Computers and Laptops, Smartphones and Accessories, ...>
OR
  'products': <a list of products from the allowed list below>

If no products or categories are found, output an empty list.

Allowed products:
Computers and Laptops category:
  TechPro Ultrabook
  BlueWave Gaming Laptop
  ...
Smartphones and Accessories category:
  SmartX ProPhone
  ...
```

**模型输出**：

```json
[
  {"category": "Smartphones and Accessories", "products": ["SmartX ProPhone"]},
  {"category": "Cameras and Camcorders",      "products": ["FotoSnap DSLR Camera"]},
  {"category": "Televisions and Home Theater Systems"}
]
```

第三项没有 `products`，因为用户只问了"电视"这个类别——**类别级别**的查询。

---

### 3.2 Step 2：本地查询（不用 LLM）

把 JSON 字符串读成 Python 对象，用本地字典查询产品详情。

```python
import json

def read_string_to_list(input_string: str | None) -> list | None:
    if input_string is None:
        return None
    try:
        input_string = input_string.replace("'", '"')
        return json.loads(input_string)
    except json.JSONDecodeError:
        print("Error: Invalid JSON string")
        return None

def get_product_by_name(name):
    return products.get(name)

def get_products_by_category(category):
    return [p for p in products.values() if p["category"] == category]
```

然后根据 JSON 里每项是 `products` 还是 `category` **分别查**：

```python
def generate_output_string(data_list):
    output = ""
    for data in data_list:
        if "products" in data:
            for name in data["products"]:
                output += json.dumps(get_product_by_name(name), indent=4) + "\n"
        elif "category" in data:
            for p in get_products_by_category(data["category"]):
                output += json.dumps(p, indent=4) + "\n"
    return output
```

### 3.3 Step 3：生成最终回复

把 Step 2 的结果**作为 assistant role 的消息**注入，让模型有"上下文"去回答：

```python
messages = [
    {"role": "system",    "content": "You are a customer service assistant..."},
    {"role": "user",      "content": user_message},
    {"role": "assistant", "content": f"Relevant product information:\n{product_info}"},
]
final_response = get_completion_from_messages(messages)
```

---

## 四、为什么不一次性塞全部产品信息？

### 三个理由（按重要性排序）

| 理由 | 说明 |
|---|---|
| 1. **上下文长度限制** | 真实商品目录可能上万条，塞不进窗口 |
| 2. **成本** | 按 token 收费，无用信息就是烧钱 |
| 3. **模型注意力** | 信息越多越容易"分心"（对旧模型影响大，GPT-4 能较好忽略无关内容）|

> **核心设计哲学**：**"把语言模型当作一个推理 agent"——它需要的是"必要上下文"，而不是"全量知识"。**

---

## 五、动态上下文加载的通用模式

```
用户输入
   │
   ▼
[LLM] 识别需要什么信息
   │
   ▼
[程序] 去数据源拿信息
  (Products API, Knowledge Base, Search, SQL, ...)
   │
   ▼
[LLM] 基于这些信息生成回复
```

这**就是 RAG（Retrieval-Augmented Generation）的雏形**，也是 **ChatGPT Plugins** 的底层思路。

---

## 六、精确匹配的局限 —— Embeddings 的切入点

### 6.1 本课用的是"精确名字匹配"

- 用户必须说"SmartX ProPhone"才能查到
- 用户说"我想要一部手机" → 匹配不到任何东西

### 6.2 Embeddings 的优势

> **Semantic search（语义搜索）**：把查询和文档都映射到向量空间，按相似度找，不依赖关键词精确匹配。

- 用户说 "a mobile phone" → 能匹配到 "SmartX ProPhone"
- 用户说 "something for gaming" → 能匹配到 "BlueWave Gaming Laptop"

**生产级 Chaining Prompts 系统几乎都会用 Embeddings 做第一步检索。**

---

## 七、实践要点

### 7.1 Prompt 拆分的粒度

- **过细**：每步 5 行 Prompt——链路太长、延迟累积
- **过粗**：每步塞几十条规则——又回到 CoT 的问题了
- **合适**：**每个状态一套规则**——状态机清晰

### 7.2 用 JSON 结构化中间输出

- **必做**：严格要求模型输出 JSON（用 system message 明确）
- **加一层容错**：`try/except` + `.replace("'", '"')` 应对单引号
- **降级方案**：parse 失败时给兜底回答，别让程序崩

### 7.3 把中间产物塞回对话

- 注入 **`role: assistant`** 消息**比**塞进 system 更自然——模型会把它当作自己的知识
- 格式："Relevant product information:\n<JSON>" 这样的前缀最好

### 7.4 测试 / 观测

- 每一步都可以**单独测试**（输入一条用户消息，断言 Step 1 输出正确）
- 监控每一步的成功率，找瓶颈
- 支持 **Human-in-the-loop**：某一步失败时切到人工处理

---

## 八、与 AI Agent 的关联

> **Chaining Prompts 就是无工具调用版本的 Agent**。

加一层"让模型自己决定下一步调什么工具"——Agent 就成型了：

```
[Agent 雏形]                     [完整 Agent]
                                 ┌──────────────┐
Input                            │  Tool Router │
  │                              │   (LLM)      │
  ▼                              └───┬──────────┘
Extract (LLM)                        │
  │                      ┌───────────┴──────────┐
  ▼                      ▼           ▼          ▼
Query (code)          Search API  Database   Calculator
  │                      │           │          │
  ▼                      └───────┬───┴──────────┘
Answer (LLM)                     ▼
                              Observe
                                 │
                                 ▼
                              Answer (LLM)
```

**差别**：Agent 让**模型来决定路由**，Chaining 让**开发者写死路由**。生产系统里往往**混用**——简单分支写死，复杂决策交给模型。

---

## 九、预告：下一节

搭完了输入评估（EP04）+ 处理（EP05、EP06），下一课进入 **Check Outputs**——在把结果展示给用户之前，**再做一次把关**（内容安全、事实正确性）。
