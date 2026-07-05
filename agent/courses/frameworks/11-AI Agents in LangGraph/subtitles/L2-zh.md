本节从零开始手写一个基于 **ReAct 模式**的智能体。

---

**ReAct 模式**

ReAct = Reasoning（推理）+ Acting（行动）。循环流程：

1. LLM **思考**（Thought）：分析当前问题
2. LLM 决定**行动**（Action）：选择要调用的工具
3. 输出 **Pause**：信号告知外部代码执行工具
4. 返回**观察结果**（Observation）：工具执行结果
5. 重复，直到输出最终答案（Answer）

---

**Agent 类实现**

```python
class Agent:
    def __init__(self, system=""):
        self.system = system
        self.messages = []
        if system:
            self.messages.append({"role": "system", "content": system})
    
    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result
    
    def execute(self):
        response = client.chat.completions.create(
            model="gpt-4",
            temperature=0,
            messages=self.messages
        )
        return response.choices[0].message.content
```

---

**系统提示词**

提示词告诉 LLM 以 `Thought → Action → PAUSE → Observation → Answer` 的格式循环输出，并提供可用工具列表和示例轨迹，帮助模型理解期望格式。

**两个工具（玩具示例）**：
- `calculate(expression)`：用 `eval()` 执行数学计算
- `average_dog_weight(breed)`：返回犬种的平均体重（硬编码模拟数据）

---

**手动演示**

问题："我有一只边境牧羊犬和一只苏格兰梗，它们的总体重是多少？"

执行过程（手动逐步）：
1. 调用智能体 → 输出：查询边境牧羊犬体重
2. 调用 `average_dog_weight("Border Collie")` → 返回 37 磅
3. 传入观察结果 → 输出：查询苏格兰梗体重
4. 调用 `average_dog_weight("Scottish Terrier")` → 返回 20 磅
5. 传入观察结果 → 输出：计算 37 + 20
6. 调用 `calculate("37 + 20")` → 返回 57
7. 传入观察结果 → 最终答案："两只狗的总体重是 57 磅"

---

**自动化：封装成循环**

```python
def query(question, max_turns=5):
    agent = Agent(prompt)
    next_prompt = question
    i = 0
    while i < max_turns:
        i += 1
        result = agent(next_prompt)
        # 用正则解析是否有 Action
        actions = action_re.findall(result)
        if actions:
            action, action_input = actions[0]
            observation = known_actions[action](action_input)
            next_prompt = f"Observation: {observation}"
        else:
            return  # 输出了 Answer，结束循环
```

运行效果：自动完成三次工具调用，输出正确答案。

---

**关键洞察**

构建这个智能体只需要：
- LLM API（负责推理和决策）
- Python 代码（负责解析输出、调用工具、管理消息历史）

LLM 做推理，运行时代码做执行——这是智能体架构的核心分工。

下一节将用 LangGraph 重构这个智能体，展示框架带来的便利。我们下节课见。