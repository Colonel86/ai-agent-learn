# EP09: Evaluation Part I（评估 — 有标准答案时如何量化 Prompt 质量）

> 学习日期：2026-04-21
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI · Building Systems with the ChatGPT API（Andrew Ng）

---

## 本课概览

| 主题 | 核心内容 | 重要程度 |
|---|---|---|
| LLM 评估 vs 传统 ML 评估 | 不再需要先收集大量测试集 | ⭐⭐⭐ |
| 渐进式 Dev Set 构建 | 从 1-3 例到 10 例再到 100+ 例的迭代路径 | ⭐⭐⭐ |
| Few-shot Prompting | 用 user/assistant 消息对给模型示例 | ⭐⭐⭐ |
| Prompt v1 → v2 修复 | 发现问题 → 加约束 → 验证修复 → 回归测试 | ⭐⭐⭐ |
| 自动化评估函数 | `eval_response_with_ideal` 精确匹配打分 | ⭐⭐⭐ |
| 安全关键应用的额外责任 | 高风险场景必须用更大测试集 | ⭐⭐ |

> **关键洞察**：传统 ML 要先收集 10,000 条标注数据才能开始，而 Prompt 开发可以**从 0 个训练样本启动**，测试集是**随着发现问题而渐进累积**的。这种"先跑起来，再补样本"的节奏，是 LLM 应用开发区别于传统 ML 的核心范式差异。

---

## 一、LLM 评估 vs 传统 ML 评估

| 维度 | 传统监督学习 | LLM Prompt 开发 |
|---|---|---|
| 启动成本 | 需要 10,000+ 标注样本 | **0 个训练样本即可启动** |
| 测试集收集时机 | 开发前预先收集 | **发现问题后渐进添加** |
| 迭代速度 | 月级别 | **分钟/小时级别** |
| 典型测试集规模 | 1,000+ 条 hold-out set | **10~100 条 dev set 往往够用** |

---

## 二、渐进式 Dev Set 构建路径

```
阶段 1: 手工调试（1~5 例）
    └── 选 1-3 个有代表性的用户输入
    └── 肉眼看输出，调整 prompt 直到通过
    └── ✅ 很多内部工具到这里就够了

阶段 2: 发现 tricky case，主动累积
    └── 上线或内测时遇到失败例子
    └── 把失败例子加入 dev set
    └── 修 prompt，重跑所有 dev set 例子（回归测试）

阶段 3: Dev Set 达到 10+ 条 → 自动化评估
    └── 手动跑 10 个例子已经很痛苦
    └── 写 eval 函数，批量打分，输出 fraction_correct
    └── ✅ 大多数应用到这里即可

阶段 4（可选）: 随机采样 100+ 条
    └── 需要更高置信度时
    └── 继续作为 dev set（还会继续调 prompt）

阶段 5（可选）: Hold-out Test Set
    └── 需要无偏估计最终系统性能时
    └── 调 prompt 时不能看这个集合
    └── ⚠️ 安全关键应用必须做到这一步
```

---

## 三、Few-shot Prompting（一次性/少样本示例）

在 system message 后面用 `user`/`assistant` 消息对给模型**演示期望的输出格式**：

```python
few_shot_user_1 = "I want the most expensive computer."
few_shot_assistant_1 = """
[{'category': 'Computers and Laptops',
  'products': ['TechPro Ultrabook', 'BlueWave Gaming Laptop', ...]}]
"""

messages = [
    {'role': 'system',    'content': system_message},
    {'role': 'user',      'content': f"####{few_shot_user_1}####"},
    {'role': 'assistant', 'content': few_shot_assistant_1},   # 示范输出
    {'role': 'user',      'content': f"####{user_input}####"},
]
```

- 1 个示例 = **one-shot prompting**
- 2 个示例 = **two-shot / few-shot prompting**
- 示例的核心价值：**约束输出格式**，让模型"看到"正确答案长什么样

---

## 四、Prompt v1 → v2：问题发现与修复

### 发现的问题

`customer_msg_3`（多产品 + 多类别查询）让 v1 prompt 在正确 JSON 后面**输出了大量多余文字**，导致 `json.loads()` 解析失败。

### 修复策略

**v2 的两处改动：**

```
改动 1：在 system_message 中新增约束
    "Do not output any additional text that is not in JSON format."
    "Do not write any explanatory text after outputting the requested JSON."

改动 2：从 1-shot 升级为 2-shot
    新增 few_shot_user_2 / few_shot_assistant_2
    （cheapest computer 示例，进一步强化"只输出 JSON"的行为）
```

### 修复验证 + 回归测试

```python
# 验证 tricky case 已修复
print(find_category_and_product_v2(customer_msg_3, products_and_category))

# 回归测试：确认原来能过的例子没被破坏
print(find_category_and_product_v2(customer_msg_0, products_and_category))
```

> **经验法则**：每次改 prompt 之后，都要跑**全量 dev set**，防止修了新 bug 却引入旧 bug（回归）。

---

## 五、自动化评估函数 `eval_response_with_ideal`

### Dev Set 结构

每条测试用例是一个字典，包含用户输入和**标准答案（ideal answer）**：

```python
msg_ideal_pairs_set = [
    {
        'customer_msg': "Which TV can I buy if I'm on a budget?",
        'ideal_answer': {
            'Televisions and Home Theater Systems': set([
                'CineView 4K TV', 'SoundMax Home Theater',
                'CineView 8K TV', 'SoundMax Soundbar', 'CineView OLED TV'
            ])
        }
    },
    # ... 共 10 条，index 0~9
    {
        'customer_msg': "I would like a hot tub time machine.",
        'ideal_answer': []  # 无相关产品 → 期望输出空列表
    }
]
```

### 评估函数核心逻辑

```python
def eval_response_with_ideal(response, ideal, debug=False):
    # 1. 单引号 → 双引号，让 json.loads 能解析
    json_like_str = response.replace("'", '"')
    l_of_d = json.loads(json_like_str)

    # 2. 特殊情况：双方都是空列表 → 满分
    if l_of_d == [] and ideal == []:
        return 1

    # 3. 一方为空、一方不为空 → 0 分
    elif l_of_d == [] or ideal == []:
        return 0

    correct = 0
    for d in l_of_d:
        cat = d.get('category')
        prod_l = d.get('products')
        if cat and prod_l:
            prod_set = set(prod_l)
            ideal_cat = ideal.get(cat)
            if ideal_cat:
                # 4. 集合精确匹配
                if prod_set == set(ideal_cat):
                    correct += 1
                else:
                    # 输出 subset / superset 诊断信息
                    ...

    return correct / len(l_of_d)   # 按类别数量平均
```

**评分语义**：
- `1.0` = 该条测试完全正确（所有类别的产品集合精确匹配）
- `0.0` = 完全错误
- 中间值 = 部分类别正确（多类别查询时）

### 批量运行

```python
score_accum = 0
for i, pair in enumerate(msg_ideal_pairs_set):
    response = find_category_and_product_v2(pair['customer_msg'], products_and_category)
    score = eval_response_with_ideal(response, pair['ideal_answer'])
    score_accum += score

fraction_correct = score_accum / len(msg_ideal_pairs_set)
print(f"Fraction correct out of {len(msg_ideal_pairs_set)}: {fraction_correct}")
# 示例输出：Fraction correct out of 10: 0.9
```

---

## 六、调试案例：Example 7 失败分析

- **用户问题**：`"What Gaming consoles would be good for my friend who is into racing games?"`
- **理想答案**：Gaming Consoles 分类下 5 款产品（全集）
- **v2 实际输出**：只返回了其中 3 款（是理想答案的子集 subset）
- **诊断**：eval 函数打印 `"response is a subset of the ideal answer"`
- **处置**：加入 dev set，下一轮调 prompt 时针对性修复

---

## 七、什么时候停止迭代

| 系统状态 | 建议行动 |
|---|---|
| 几个手工例子都过了，够用 | 直接上线，无需更多测试 |
| Dev set 10 条，90% correct | 上线 + 监控，持续收集 tricky case |
| 需要 91% → 93% 的精度提升 | 扩大到 100+ 条随机样本，量化差异 |
| 安全关键应用（医疗、金融、法律）| **必须**建立 hold-out test set，严格评估后才上线 |

---

## 八、本课 vs 下一课

| | EP09（本课）| EP10（下课）|
|---|---|---|
| 评估场景 | **有标准答案**（产品列表精确匹配）| **无唯一标准答案**（开放式问答）|
| 评分方式 | 集合精确匹配，返回 0/1/中间值 | 用另一个 LLM 做主观质量评判 |
| 典型任务 | 分类、提取、检索 | 生成、摘要、对话 |
