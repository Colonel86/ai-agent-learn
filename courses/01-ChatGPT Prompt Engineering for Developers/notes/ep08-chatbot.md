# EP08: Chatbot（构建聊天机器人）

> 学习日期：2026-04-15
> 所属阶段：Phase 1 · 基石构建
> 课程来源：DeepLearning.AI × OpenAI（Andrew Ng + Isa Fulford）

---

## Chat Completions 格式

ChatGPT 类模型的训练目标是**接收一系列消息作为输入，返回一条消息作为输出**。

消息列表中有三种角色：

| 角色 | 作用 |
|---|---|
| `system` | 设置助手的行为和人格（像"在耳边悄悄说话"），用户通常看不到 |
| `user` | 用户的输入 |
| `assistant` | 模型的回复 |

```python
messages = [
    {"role": "system", "content": "你是一个说话像莎士比亚的助手。"},
    {"role": "user", "content": "讲个笑话"},
    {"role": "assistant", "content": "为何鸡要过马路？"},
    {"role": "user", "content": "我不知道"},
]
response = get_completion_from_messages(messages)
```

---

## Context（上下文管理）

**关键点：每次 LLM 调用都是独立的——模型没有记忆！**

```python
# 如果不传历史记录，模型不知道之前说过什么
messages = [
    {"role": "system", "content": "你是一个友好的聊天机器人"},
    {"role": "user", "content": "你好，我叫 Isa"},
]
# 之后问"我叫什么名字"，如果不包含上面的历史，模型不知道！

# 正确做法：每次调用都把完整对话历史传进去
messages = [
    {"role": "system", "content": "你是一个友好的聊天机器人"},
    {"role": "user", "content": "你好，我叫 Isa"},
    {"role": "assistant", "content": "你好 Isa！很高兴认识你。有什么我可以帮你的？"},
    {"role": "user", "content": "我叫什么名字？"},
]
```

---

## OrderBot 实战案例

构建一个自动接单的披萨店聊天机器人：

**System Message（关键！）：**
```python
system_message = """
你是 OrderBot，一个为披萨餐厅自动收集订单的服务程序。
首先问候顾客，然后收集订单，询问是取餐还是外送。
等待收集完整订单后，对订单进行汇总，再次确认顾客是否需要添加其他内容。
如果是外送，请索取地址。最后收取付款。
请确认所有选项、附加项和尺寸，以便唯一确认菜单中的商品。
以简短、非常对话式、友好的风格回应。
菜单包含：
披萨：意大利辣香肠$12.95，芝士$10.00，茄子$11.50
...
"""
```

**Context 动态增长：**
```python
context = [{"role": "system", "content": system_message}]

def collect_messages(user_message):
    context.append({"role": "user", "content": user_message})
    response = get_completion_from_messages(context)
    context.append({"role": "assistant", "content": response})
    return response
```

**自动生成 JSON 订单：**
对话结束后，追加一条指令让模型输出结构化订单：

```python
messages = context.copy()
messages.append({
    "role": "user",
    "content": """生成之前食物订单的 JSON 摘要。
    对每个商品的价格进行逐项列出，字段包括：
    1. 披萨（包含尺寸）2. 配料列表 3. 饮料列表 4. 配菜列表 5. 总价"""
})
```

**Temperature 选择：**
- 对话生成：可用稍高 temperature（更友好自然）
- 最终订单 JSON：用低 temperature（保证准确）
