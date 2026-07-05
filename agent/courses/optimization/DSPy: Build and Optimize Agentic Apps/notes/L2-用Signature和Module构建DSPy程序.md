# L2 · 用 Signature 和 Module 构建 DSPy 程序

> 课程：DSPy: Build and Optimize Agentic Apps（DeepLearning.AI × Databricks）
> 本课任务：掌握 DSPy 编程的两大抽象——**signature**（LLM 调用的输入输出契约）与 **module**（携带自定义逻辑与 LLM 对话的接口），先用内置 module 搭情感分类器，再自定义 module 实现"猜名人"游戏 agent。

## 0. 本课目标与两个交付物

实验室两步走：**① 用 DSPy 内置 module 构建一个简单的情感分析程序**（学 fundamentals）；**② 自定义 module 构建 agent**——"name the celebrity"游戏：玩家一（人）心里想一个名人，玩家二（LM）不断问 yes/no 问题，直到猜中名字或用完提问配额。

## 1. Signature：写在客户端的输入输出契约

延续 L1 的心智模型：DSPy 中与 LLM 交互 ≈ 调用一个输入输出格式良定义的 RESTful API，**只是格式定义发生在客户端**而非服务端。定义的载体就是 signature：

> Signature 定义 LM 交互的 **input/output fields**，连同**类型**和**注释**。

### 1.1 Class-based signature（推荐）：五个组成部分

```python
class SentimentClassifier(dspy.Signature):
    """Classify the sentiment of a text."""          # ① docstring = 指令：LM 调用的目的/任务概述

    text: str = dspy.InputField(                     # ② 字段名 text ③ InputField 标记输入
        desc="input text to classify sentiment")     # ④ desc：字段名不自解释时补充信息
    sentiment: int = dspy.OutputField(               # ③ OutputField 标记输出 ⑤ 类型 int
        desc="sentiment, the higher the more positive",
        ge=0, le=10)                                 # pydantic 约束：限定 0~10，DSPy 完整支持
```

| 部分（课件色块） | 是什么 | 备注 |
|---|---|---|
| ① 指令（红） | signature 类的 docstring | 通常几句话即可；已有现成长 prompt 不想简化，可整段贴进 docstring |
| ② 字段名（橙） | 传入输入 / 访问输出用的名字 | — |
| ③ Input/OutputField（蓝） | 标记该字段是输入还是输出 | — |
| ④ desc（紫） | 字段的实际含义信息 | 字段名不自解释时很有用 |
| ⑤ 类型（绿） | 内置 Python 类型 / 自定义类 / pydantic model | 主要用于输出字段——指定后访问输出时**自动是期望的类型** |

### 1.2 String-based signature（原型用）

```python
str_signature = dspy.make_signature("text -> sentiment")  # 箭头前输入、箭头后输出，逗号分隔多字段
```

更轻，但丢失了 class-based 的信息（类型、desc、约束）。**原型阶段可用，通用场景推荐 class-based**——更灵活、支持更强。

## 2. Module：用 signature 与 LM 对话的最小构件

Signature 只是**静态信息**，还需要一个东西拿着它去和 LM 实际交互——这就是 module：

> Module 是 DSPy 程序的**最小 building block**，大多数情况下**附着一个 signature**；除 signature 外还有可配置属性（如 `demos` 携带 few-shot 示例）；可以为自定义逻辑而定制，也可以**由子 module 组合**。

内置 module 一览（完整清单见官方文档）：

| 内置 module | 一句话 |
|---|---|
| `dspy.Predict` | 最小、最重要：把用户查询格式化成 LM prompt，并按 signature 解析 LM 响应——**所有复杂 module 的 building block** |
| `dspy.ChainOfThought` | 除了最终回答，还要求给出答案背后的 **reasoning** |
| `dspy.ReAct` | reasoning + act，构建 AI agent 的常用标准（L3 会用） |
| `dspy.ProgramOfThought` | 类似 ReAct，但工具调用就是**写代码** |
| `dspy.Refine` | 设置 reward function 和阈值，不达标就带着 LM 反馈重试 |

用法：**把 signature 传给内置 module 造实例，再用关键字参数传入输入字段**：

```python
cot = dspy.ChainOfThought("question -> answer")  # 单输入字段 question
cot(question="...")                              # 调用时按字段名传值
```

## 3. 上手：情感分类器

```python
import dspy
dspy.settings.configure(lm=dspy.LM("openai/gpt-4o-mini"))  # 第一步：选 LM
# 字符串格式 = "provider名/model名"，如 openai/gpt-4o、anthropic/...  换模型只改这个字符串

predict = dspy.Predict(SentimentClassifier)      # signature 喂给 Predict 造实例
output = predict(text="I am feeling pretty happy!")  # 唯一输入字段 text

print(output.sentiment)      # 属性访问
print(output["sentiment"])   # 键访问——两者等价
```

输出是 **`dspy.Prediction`**：类似 dict，但**同时支持属性访问和键访问**；这里只有一个值，对应输出字段 sentiment（int，0~10——类型和约束自动生效）。

中途换模型：`dspy.configure(lm=dspy.LM("openai/gpt-4o"))` 再调用同一实例即可（课堂上换 4o 得到相同的值），随后再换回 4o-mini。

## 4. "我的 prompt 在哪？"——inspect_history 与 Adapter 机制

代码里干干净净没有 prompt，但和 LLM 说话必然有 prompt。DSPy 提供 `dspy.inspect_history(n=1)`（n = 从记忆里拉取的条数），pretty-print 出多轮消息和 LM 响应：

- **system message**：字段信息（input/output fields、desc、pydantic 约束）+ 与 LM 约定的**输入输出格式**；
- **user message**：实际用户输入，按上面定义的格式排版；
- **response**：LM 响应，同样按约定格式返回。

换成 `ChainOfThought` 再跑：输出除了 sentiment（值不变）还多了 **reasoning** 字段——再 inspect_history，可见输出字段定义里多了 reasoning 及其格式约定。

幕后机制（以最小的 `dspy.Predict` 解释）：

```
用户输入 (kwargs)
     │
Module（Predict/CoT：自身携带 signature、demos 等属性）
     │  forward 把全部信息交给 ↓
Adapter ──格式化──▶ 实际 prompt（多轮消息）──▶ LM
     ▲                                          │
     └────── 按约定格式解析响应 ◀── LM 响应 ────┘
     │
Prediction（dict-like：.sentiment / ["sentiment"]）
```

- **Adapter** 负责把 signature + 用户查询 + 其他属性组合成实际 prompt，并告诉 LM 用什么格式回复——**正因为响应格式是我们在 prompt 里约定的，adapter 才能自动把字段值解析出来**；回程就是逆过程：解析进输出字段、包成 Prediction 还给 module；
- 默认 adapter 的格式是"**section header + 值**"；通常 **DSPy 根据语言模型自动选 adapter**，也可手动切换：

```python
dspy.configure(adapter=dspy.JSONAdapter())  # 模型支持 structured output（GPT-4o/4o-mini 等）时的好选择
```

切到 JSONAdapter 后同样的调用，prompt 里改为要求输出 JSON 对象，响应也变成 JSON 再被解析。

一句话总结本节：**DSPy 把 signature + module 信息 + 实际输入组合成多轮 prompt，再按 signature 解析 LM 响应——LM 就像一个输入输出良定义的 API**。

> **对比 07a《Getting Structured LLM Output》**：那门课的结构化输出是**面向单次调用**的——手工写 response_format/JSON schema，换模型要重新适配各家 API。DSPy 的 adapter 把"结构化 I/O 协议"抽成了**可插拔层**：signature 声明"要什么字段"，adapter 决定"用什么线缆协议去要"（section header 还是 JSON），模型换了就换 adapter，signature 与业务代码一行不动。这正是 L1 说的 LM-agnostic 在工程上的落点。

> **架构师视角**：Module–Adapter–LM 是一个干净的三层分离：**意图层**（signature：要什么）、**协议层**（adapter：怎么编解码）、**执行层**（LM：谁来算）。手写 prompt 的做法等于把三层揉在一个字符串里，所以才会"换模型全废"。评估任何 LLM 框架时可以拿这个问题当探针：**它有没有把 prompt 格式从业务意图里分离出来？** 分离了，优化器才有介入的接口——这也是 L4 optimizer 能自动改 prompt 的结构性前提。

## 5. 自定义 Module："猜名人"游戏 agent

内置 module 覆盖不了复杂逻辑时，就自定义 module——**做法与 PyTorch 极像**：subclass `dspy.Module`，在 `forward` 方法里写自定义逻辑，实例本身可调用。

两个子 module 各配一个 signature：

```python
class QuestionGenerator(dspy.Signature):
    """Generate a yes or no question in order to guess the celebrity name in users' mind.
    You can ask in general or directly guess the name if you think the signal is enough.
    You should never ask the same question in the past_questions."""
    past_questions: list[str] = dspy.InputField(desc="past questions asked")   # 历史问题，从空列表开始
    past_answers: list[bool] = dspy.InputField(desc="past answers")            # 历史答案
    new_question: str = dspy.OutputField(desc="new question that can help narrow down the celebrity name")
    guess_made: bool = dspy.OutputField(desc="...")  # True=直接猜名字，False=一般性问题

class Reflection(dspy.Signature):
    """Provide reflection on the guessing process"""  # 游戏结束后自我复盘：哪里做得好、哪里可改进
    correct_celebrity_name: str = dspy.InputField(...)
    final_guessor_question: str = dspy.InputField(...)
    past_questions: list[str] = dspy.InputField(...)
    past_answers: list[bool] = dspy.InputField(...)
    reflection: str = dspy.OutputField(...)
```

自定义 module 把两者组合，`forward` 里就是普通 Python：

```python
class CelebrityGuess(dspy.Module):
    def __init__(self, max_tries=10):
        super().__init__()
        self.question_generator = dspy.ChainOfThought(QuestionGenerator)  # 子 module ①
        self.reflection = dspy.ChainOfThought(Reflection)                 # 子 module ②
        self.max_tries = 20                                               # 提问配额 20

    def forward(self):
        celebrity_name = input("Please think of a celebrity name...")     # 人先想好名字
        past_questions, past_answers = [], []
        correct_guess = False
        for i in range(self.max_tries):                                   # 循环：生成问题→人答 y/n→记录
            question = self.question_generator(
                past_questions=past_questions, past_answers=past_answers)
            answer = ask(f"{question.new_question}").lower() == "y"
            past_questions.append(question.new_question)
            past_answers.append(answer)
            if question.guess_made and answer:                            # 直接猜名 且 答对 → 结束
                correct_guess = True
                break
        # 游戏结束后自我复盘
        reflection = self.reflection(correct_celebrity_name=celebrity_name,
                                     final_guessor_question=question.new_question,
                                     past_questions=past_questions,
                                     past_answers=past_answers)
        print(reflection.reflection)

celebrity_guess = CelebrityGuess()
celebrity_guess()   # 实例可调用。课堂演示：想"Lebron James"，LM 依次问 演员？歌手？体育明星？现役？湖人？→ 猜中
```

游戏本身只是 for fun，讲师想借它说明两点：

1. **灵活**：`forward` 里可以写任何 Python——调 LangChain、LlamaIndex，用 SQL、文件系统 handler……没有任何限制，所以**迁入迁出 DSPy 都容易**（呼应 L1 痛点二）；
2. **signature 系统省掉解析活**：因为显式声明了 `new_question`、`guess_made` 两个输出字段，完全不用操心从 LM 响应里解析字段，也不用担心 `guess_made` 能否稳健地区分"一般问题 vs 直接猜名"——类型系统兜底。

## 6. Save & Load：两种持久化

| 方式 | 保存内容 | 写法 | 加载 |
|---|---|---|---|
| **State-only** | 仅 module 内部状态 | `celebrity_guess.save("dspy_program/celebrity.json", save_program=False)`（路径是 .json 文件） | 需先重建实例，再 `celebrity_guess.load("...json")` |
| **Whole-program** | 整个程序（经 cloudpickle） | `celebrity_guess.save("dspy_program/celebrity/", save_program=True)`（路径是目录） | `loaded = dspy.load("dspy_program/celebrity/")`——直接得到新实例，无需关心依赖重建 |

加载回来的程序**当原程序一样直接调用**：`loaded()` 即重启游戏。

## 7. 本课总结

| 要点 | 一句话 |
|---|---|
| Signature | 客户端定义的 LM 输入输出契约：docstring 指令 + 字段名 + Input/OutputField + desc + 类型（含 pydantic 约束） |
| 两种定义法 | class-based（推荐，信息全）vs string-based `"text -> sentiment"`（原型用） |
| Module | 最小构件，附着 signature；Predict 是一切复杂 module 的基础；CoT/ReAct/PoT/Refine 内置 |
| Adapter | signature+输入 → 实际 prompt → 按约定格式解析响应 → Prediction；默认自动选，可换 JSONAdapter |
| 自定义 module | subclass `dspy.Module` + `forward` 写任意 Python（PyTorch 风格），子 module 组合 |
| Save/Load | state-only（JSON）vs whole-program（cloudpickle 目录 + `dspy.load`） |

> **记忆点（引出 L3）**：本课已经能靠 `inspect_history` 看单次 LM 交互，但 CelebrityGuess 这种**多子 module、带循环**的程序一旦出错，只看"最后 n 条 prompt"远远不够——哪一轮、哪个子 module、拿什么输入断掉的？L3 引入 **MLflow tracing**：一行代码，把 DSPy 程序每一步的输入、输出、LM 调用全部串成可视化的 trace 来调试。

## 与我的资产映射

- 框架层：`agent/skills/agent-selection/2-framework/03-framework-profiles.md`——DSPy 编程模型的证据：PyTorch 风格 module 组合、forward 内可嵌 LangChain/LlamaIndex（与编排框架正交而非互斥）
- 观测/评估层：`agent/skills/agent-selection/5-observability-eval.md`——`inspect_history` 是框架内建的最小可观测性；其局限（只有 LM 调用历史、无程序级 trace）正是 L3 MLflow tracing 的切入点
- [[project_selection_matrix]]——选型矩阵真缺口的补齐素材：signature/module/adapter 三概念是 DSPy 区别于其他框架的核心抽象
