# EP05: Chain-of-Thought Reasoning（链式推理 + 内心独白）

> 学习日期：2026-04-17
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI · Building Systems with the ChatGPT API（Isa Fulford）

---

## 本课概览

| 主题 | 核心内容 | 重要程度 |
|---|---|---|
| 为什么要 CoT | 让模型"慢慢想"，减少冲动式错误 | ⭐⭐⭐ |
| 5 步推理模板 | 澄清 → 对齐 → 提取假设 → 验证 → 作答 | ⭐⭐⭐ |
| Inner Monologue | 用分隔符把推理过程"藏起来"，只展示结论 | ⭐⭐⭐ |
| 结构化输出 | `Step 1:#### ... Response to user:####` | ⭐⭐ |
| try/except 兜底 | 模型格式异常时给出 fallback 回答 | ⭐⭐ |
| 与 GPT-4 的关系 | 高级模型可简化/省略部分步骤 | ⭐⭐ |

> **关键洞察**：**给模型"思考的时间"** 和**把"思考过程"与"对用户的回答"分开**是两个独立但配合使用的技巧。前者叫 Chain-of-Thought，后者叫 Inner Monologue——合起来就是：**既要让模型想清楚，又不要让用户看见它的思考过程**。

---

## 一、为什么要 Chain-of-Thought

### 1.1 问题：模型容易"冲动作答"

模型如果被要求直接给出结论，常常会走捷径 / 拍脑袋 / 被用户错误前提带偏。

**例子**（课程里的案例）：
- 用户问："BlueWave Chromebook 比 TechPro Desktop 贵多少？"
- 事实：Chromebook $249.99 < Desktop $999.99——用户的前提就是错的。
- 直接问 → 模型可能顺着用户前提胡乱算差价。
- 加 CoT → 模型会先提取用户的假设，再验证、再礼貌纠正。

### 1.2 解决思路

把"回答"改写为**一系列步骤**——强迫模型按顺序推理，相当于人类做题时的"打草稿"。

---

## 二、5 步推理模板（产品客服场景）

```
Step 1:#### 判断用户是否在问具体产品（类别不算）
Step 2:#### 如果是，核对产品是否在允许列表内
Step 3:#### 如果是，提取用户的假设
Step 4:#### 基于产品信息验证这些假设是否正确
Step 5:#### 礼貌纠正错误假设，只引用允许列表中的产品

输出格式：
Step 1:#### <reasoning>
Step 2:#### <reasoning>
Step 3:#### <reasoning>
Step 4:#### <reasoning>
Response to user:#### <最终回复>
```

### 2.1 为什么每步都用 `####`

**双重作用**：
1. 让模型**清晰标记**步骤边界
2. 便于后续用字符串操作**切出最终回复**

> GPT-4 这类高级模型对格式要求没那么死板——"pedantic instructions" 在它们身上可简化。

---

## 三、Inner Monologue（内心独白）

### 3.1 动机

**不是所有思考过程都适合给用户看**：
- 教育场景：模型如果直接秀出"学生解题错在哪"，就把答案告诉了学生
- 客服场景：中间推理暴露了商业逻辑 / 系统 Prompt / 品牌调性

### 3.2 实现：输出时切字符串

```python
try:
    final_response = response.split("####")[-1].strip()
except Exception:
    final_response = (
        "Sorry, I'm having trouble right now, "
        "please try asking another question."
    )
```

**三个要点**：
- `split("####")[-1]`：取最后一段（`Response to user:####` 后面的内容）
- `.strip()`：去掉首尾空白
- `try/except`：模型格式跑偏时给兜底回答，避免程序挂掉

### 3.3 完整流程

```
用户 → 模型（输出完整推理 5 步 + 最终回复）
                │
                ▼
         程序切分字符串
                │
         丢掉前 5 步推理
                │
                ▼
         只把最终回复展示给用户
```

---

## 四、两个实战例子

### 4.1 例子 1：前提错误的产品对比

**用户**：`by how much is the BlueWave Chromebook more expensive than the TechPro Desktop?`

**模型做了什么**：
1. Step 1：是的，用户问了具体产品
2. Step 2：两个都在列表里
3. Step 3：用户假设 Chromebook > Desktop
4. Step 4：事实相反，Chromebook $249.99 < Desktop $999.99
5. Response：礼貌纠正——其实 Chromebook 更便宜，Desktop $999.99 vs Chromebook $249.99

### 4.2 例子 2：不卖的品类

**用户**：`do you sell TVs?`

**模型做了什么**：
- Step 1 判定"用户问的是 TV"，但 TV 不在列表
- **直接跳到 Response**："Sorry, we do not sell TVs..."
- 模型**没有严格按格式**输出每一步——这是它做的**合理简化**

> **观察**：模型会自主判断"中间步骤是否必要"。严格控制格式需要更强的模型或更严格的 Prompt。

---

## 五、与第 3 课（分类）的对照

| 维度 | EP03 分类 | EP05 CoT |
|---|---|---|
| 目标 | 把查询归类 | 给具体问题找正确答案 |
| 输出 | 结构化 JSON | 多步骤文本 + 最终回复 |
| 模型"思考"| 基本不展开 | **显式展开**每一步 |
| 错误模式 | 类别选错 | 冲动回答错误前提 |
| 用户可见 | 通常不直接展示 | **Inner Monologue 隐藏** |

---

## 六、实践要点

### 6.1 何时适合用 CoT

- ✅ 答案涉及**多步推理**（对比、计算、验证假设）
- ✅ 用户问题里**可能含错误前提**
- ✅ 对答案**准确性要求高**
- ❌ 简单问答（"你们几点营业？"）——CoT 是浪费 token

### 6.2 何时启用 Inner Monologue

- ✅ 教学 / 辅导（不想让答案泄露）
- ✅ 客服 / 商业（不想暴露决策逻辑）
- ✅ 展示给最终用户的场景 → 默认隐藏推理
- ❌ 调试时反而要显示所有步骤

### 6.3 常见坑

| 坑 | 解决 |
|---|---|
| 模型不按步骤格式输出 | 加 Few-shot 示例 / 使用更强模型 / 明确 "Make sure to include ####" |
| Split 切错 | 始终用 `[-1]` 取最后一段 + `try/except` |
| 推理过多导致 token 爆 | 限制步骤数 / 用更简洁的 Prompt |
| 简单问题也走 5 步 | 在 system message 里允许模型 "skip 不必要的步骤" |

---

## 七、与 AI Agent 的关联

> **Chain-of-Thought 是 Agent 的"思维框架"的前身**。

- Agent 中的 **ReAct 模式**（Thought/Action/Observation 循环）就是 CoT 的扩展
- **Inner Monologue** 对应 Agent 里的 **Scratchpad / Reasoning Trace**
- 现代 Agent 通常会把"思考"包在 `<thinking>` 标签里对用户隐藏，或走工具调用链路

**本课的框架**：
```
User Input → [Thinking Steps] → User-facing Output
```

**进化到 Agent**：
```
User Input → [Thinking] → [Tool Call] → [Observation] → [Thinking] → ... → Output
```

CoT 是 **"只在一次调用里思考"**；Agent 是 **"跨多次调用地思考 + 行动"**——骨架完全一样。

---

## 八、预告：下一节

CoT 是**单次调用内**拆步骤。如果任务更复杂（状态多、工具多、需要外部信息），更好的做法是**把 Prompt 拆成多个 Prompt 串起来**——这就是下一课 **Chaining Prompts**。
