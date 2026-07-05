# L2 · 搭建 SQL Agent 与诊断幻觉：Schema 注入 + Structured Output

> 课程：Improving Accuracy of LLM Applications（DeepLearning.AI × Lamini × Meta）
> 本课任务：连上 SQLite 真库搭出可执行的 SQL agent；用**三步由简到繁**——prompt 里注入 schema+格式示例 → 用 **structured output** 逼模型只吐 SQL → **亲手复现并诊断** malformed 幻觉（NBA 薪资排序）。

## 0. 本课路线

SQL agent 工作流：**用户提问 → 模型产 SQL → 对数据库执行 → 用户看结果**。示例问题贯穿全课：「谁是薪水最高的 NBA 球员？」提升准确率的铁律——**永远从最容易迭代的手段起步**，所以顺序是 prompt engineering 先行。

```python
import lamini, logging, sqlite3
import pandas as pd
from util.get_schema import get_schema
from util.make_llama_3_prompt import make_llama_3_prompt

engine = sqlite3.connect("./nba_roster.db")          # 连上真库
llm = lamini.Lamini(model_name="meta-llama/Meta-Llama-3-8B-Instruct")
```

Lamini 这个库把「跑开源模型 + fine-tune + memory tune」都包好了，本课先用它做推理。`model_name` 可换成任意 HuggingFace 开源模型。

## 1. Prompt Engineering 第一招：注入 schema，并且注入「格式示例」

对 Text-to-SQL，一个高性价比 pro-tip 是**把 schema 和它的格式一起塞进 system prompt**。先看只给列名、不给示例的裸 schema：

```python
def get_schema():
    return """\
0|Team|TEXT
1|NAME|TEXT
2|Jersey|TEXT
3|POS|TEXT
4|AGE|INT
5|HT|TEXT
6|WT|TEXT
7|COLLEGE|TEXT
8|SALARY|TEXT eg.
"""

system = f"""You are an NBA analyst with 15 years of experience writing complex SQL queries. \
Consider the nba_roster table with the following schema:
{get_schema()}

Write a sqlite query to answer the following question. Follow instructions exactly"""
user = "Who is the highest paid NBA player?"
prompt = make_llama_3_prompt(user, system)
print(llm.generate(prompt, max_new_tokens=200))
```

system prompt 做了两件事：**给模型一个身份**（15 年经验的 NBA 分析师）+ **贴上 schema**。但裸 schema 下模型「不太遵守我们表里的实际格式」。

**为什么格式示例是关键**：以 `HT`（身高）为例——真实值是 `6' 7"`（带空格的英尺英寸），如果格式不同，模型该生成的 SQL 完全不同才能正确执行。于是升级 schema，给每列贴**真实样例值**：

```python
def get_updated_schema():
    return """\
0|Team|TEXT eg. "Toronto Raptors"
1|NAME|TEXT eg. "Otto Porter Jr."
2|Jersey|TEXT eg. "0" and when null has a value "NA"
3|POS|TEXT eg. "PF"
4|AGE|INT eg. "22" in years
5|HT|TEXT eg. `6' 7"` or `6' 10"`
6|WT|TEXT eg. "232 lbs"
7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"
8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"
"""
```

注意 `SALARY` 这行：`TEXT eg. "$9,945,830"`——**薪资是带 `$` 和逗号的文本、且 null 用 `"--"`**。这一条信息正是后面幻觉的震中。加了示例后模型明显变好（例如会正确 `WHERE salary != '--'` 过滤空值）。课程强调这是个**可迭代旋钮**：把示例删掉，模型立刻变差。

## 2. Prompt Engineering 第二招：Structured Output 强制只吐 SQL

裸生成的问题：模型除了 SQL 还吐一堆解释（"to answer this question we can use..."），**你没法直接拿去执行**，得再开一次模型调用或写 parser 去抽 SQL。解法是 **structured output**：

```python
# 只需加一个 output_type，声明返回一个 {"sqlite_query": str} 的字典
result = llm.generate(prompt, output_type={"sqlite_query": "str"}, max_new_tokens=200)
# result → {"sqlite_query": "SELECT ... FROM nba_roster ..."}

df = pd.read_sql(result['sqlite_query'], con=engine)   # 直接喂给数据库执行
```

两个要点：

1. **100% 格式准确**：`output_type` 把模型约束成只输出这个 schema 的字符串，格式层面强制保证，无需事后解析。
2. **key 本身会进 prompt、会影响输出**：`"sqlite_query"` 这个键名被当成「初始输出、强制以此开头」注入进模型，所以它会实打实影响后续 token。这也是一个可调参数——键名怎么起、值类型怎么定，都能拿来做幻觉诊断实验。

> **对比 5-observability-eval.md 里的结构化输出**：这里的 structured output 不只是「拿到干净 JSON」的工程便利——它把「格式正确」这个维度**从准确率里彻底剥离**。剥离后，剩下的错误就纯粹是**语义错误（malformed）**，evaluation 的信号更干净、更好归因。先用结构化约束把 100% 能保证的维度锁死，再去量化剩下真正难的那部分，是评估设计的通用手法。

## 3. 诊断幻觉：亲手复现 NBA 薪资的 malformed 幻觉

structured output 生成的查询**能跑、语法合法，但答案是错的**——这是 L1 讲的 **malformed SQL**（valid 但语义错）。

**错误查询**（把薪资当 REAL 直接排序）：

```sql
SELECT NAME, SALARY
FROM nba_roster
WHERE salary != '--'
ORDER BY CAST(SALARY AS REAL) DESC        -- ❌ 薪资是 "$9,945,830" 文本
LIMIT 1;
-- 执行结果：Saddiq Bey（约 450 万）—— 错的
```

问题根因：`SALARY` 是带 `$` 和逗号的**字符串**。`CAST(... AS REAL)` 遇到 `$` 无法正确转成数字，**字符串排序 ≠ 整数排序**，于是选出的根本不是薪水最高的人。

**正确查询**（先剥掉 `$` 和逗号再转 INTEGER）：

```sql
SELECT salary, name
FROM nba_roster
WHERE salary != '--'
ORDER BY CAST(REPLACE(REPLACE(salary, '$', ''), ',', '') AS INTEGER) DESC
LIMIT 1;
-- 执行结果：Steph Curry —— 对的
```

```python
df = pd.read_sql(correct_query, con=engine)   # → Steph Curry
```

对比一眼看清：

| | 错误查询 | 正确查询 |
|---|---|---|
| 处理薪资 | `CAST(SALARY AS REAL)` | 先 `REPLACE` 掉 `$` 和 `,` 再 `CAST ... AS INTEGER` |
| 能否执行 | 能（valid SQL） | 能 |
| 答案 | Saddiq Bey（~4.5M）❌ | Steph Curry ✅ |
| 幻觉类型 | malformed（语义错） | — |

## 4. 「诊断幻觉」是一项核心技能，不是一次性动作

Sharon 反复强调：**诊断幻觉是高度迭代的**——模型每改进一次，你就继续深挖新的幻觉、不断逼近「模型对/错的边界」。它的价值在于**给 LLM 一颗北极星**：

> LLM 极擅长优化，它只是需要你告诉它「优化什么」。你把幻觉的边界找出来、指出「这里要改」，它就会替你改好。

课程给的实操建议：**多问问题**（不止「谁薪水最高」），去发现更多幻觉、摸清这个 LLM 在当前 schema 上的能力边界；持续迭代 schema、迭代整个 prompt；拿 structured output 的 key 做实验。这一步做扎实，是后面做严格 evaluation 和生成微调数据的前提——**你得先知道错在哪，才能量化它、才能造数据去修它**。

> **架构师视角**：本课把「提准确率」拆成一条**成本递增的旋钮链**：schema 注入（几乎零成本）→ 格式示例（低）→ structured output（低、且顺手锁死格式维度）→ 之后才是 evaluation / fine-tune（高）。每拧一个旋钮都问一句「这一步的边际收益够不够我进下一个更贵的旋钮」。**Text-to-SQL 里最隐蔽的坑不是模型不会写 SQL，而是数据脏（薪资是带 `$` 的文本）**——脏数据的领域知识必须显式喂进 schema 示例，否则 prompt 再花哨也压不住 malformed 幻觉。

> **对比课程 21 Evaluating AI Agents**：那门课评估的是 agent 的**行为轨迹/工具调用**；本课诊断幻觉是评估的**前置采样**——先靠人肉「多问问题」找到失败模式、定位边界，才谈得上把它固化成 eval set 去量化。诊断（定性、找边界）在前，evaluation（定量、卡阀门）在后，L3 就把这套定性观察升级成系统化的评估框架。

> **记忆点（引出 L3）**：本课靠人肉「多问几个问题」发现幻觉——但这既不量化、也不可规模化，你无法回答「模型到底行不行、改进了没有」。L3 搭一套 **evaluation 框架**，把「模型是否真在进步」变成可依赖的**定量 yes/no**，并系统地定位「它在哪儿还在幻觉」，把 L2 的定性直觉升级成流水线里的控制阀。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 由简到繁 | 先 prompt engineering，因为它最容易迭代 |
| Schema 注入 | 把 schema + **真实格式示例**塞进 system prompt，删掉示例模型就变差 |
| Structured output | `output_type={"sqlite_query":"str"}` 强制只吐 SQL、100% 格式准确、key 会进 prompt |
| 幻觉复现 | 薪资是带 `$` 文本，`CAST AS REAL` 排序 → Saddiq Bey（错） |
| 正确解 | `REPLACE` 去 `$`/`,` 后 `CAST AS INTEGER` → Steph Curry（对） |
| 诊断是技能 | 高度迭代，给 LLM 北极星；定性找边界是量化评估的前置 |

## 与我的资产映射

- 观测与评估：`agent/skills/agent-selection/5-observability-eval.md`（structured output 剥离「格式维度」→ 让 evaluation 信号只剩语义错误；诊断幻觉作为评估的定性前置）
- 选型矩阵：`[[project_selection_matrix]]`（Text-to-SQL 的成本递增旋钮链：schema 注入 → 格式示例 → structured output → evaluation → fine-tune）
- 幻觉治理：脏数据的领域知识（薪资 `$` 文本）必须显式进 schema 示例，是「改分布前先改 prompt」的边界案例
