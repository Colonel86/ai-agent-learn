# EP08 Chatbot — 代码实战

对应课程：ChatGPT Prompt Engineering for Developers · 第 8 集

核心思想：**Chat Completions 的消息结构（system/user/assistant）+ 上下文管理 + 自定义聊天机器人。**

---

## 项目结构

```
ep08-chatbot/
├── config.py               # 两个辅助函数：get_completion + get_completion_from_messages
├── chat_basics.py          # Demo 1：多轮对话基础（莎士比亚 / 无上下文 / 有上下文）
├── orderbot.py             # Demo 2：⭐ OrderBot 交互式披萨点单机器人（终端版）
├── orderbot_summary.py     # Demo 3：模拟对话 + 生成 JSON 订单摘要
├── run_all.py              # 自动运行 Demo 1 + Demo 3（Demo 2 需单独运行）
├── your_turn.py            # 自由练习：自定义聊天机器人（PyBot 编程助手）
├── requirements.txt
└── .env.example
```

---

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY

# 3. 运行
python run_all.py          # Demo 1 + Demo 3（非交互式，自动运行）
python orderbot.py         # ⭐ Demo 2 — 完整交互点单体验
python your_turn.py        # 自定义 PyBot 编程助手（交互式）
```

---

## 演示路径

| Demo | 文件 | 核心内容 | 关键点 |
|---|---|---|---|
| 1 | chat_basics.py | 莎士比亚风格 / 无上下文忘名字 / 有上下文记名字 | ⭐ context 的本质 |
| 2 | orderbot.py | 完整交互式披萨点单（终端版） | system message 设定角色 + context 滚动增长 |
| 3 | orderbot_summary.py | 模拟对话 → JSON 订单摘要 | 对话末尾追加新 system 指令 |

---

## 核心概念：消息结构

```python
messages = [
    {"role": "system",    "content": "你是一个友好的助手"},   # 系统指令（开发者设定）
    {"role": "user",      "content": "你好，我叫 Isa"},       # 用户输入
    {"role": "assistant", "content": "你好 Isa！很高兴认识你"}, # 助手历史回复
    {"role": "user",      "content": "我叫什么名字？"},        # 当前问题
]
```

**关键规则：** 模型没有内置记忆，必须把历史对话全部传入 `messages` 列表，这叫做"上下文（context）"。

---

## Demo 2 使用方法（OrderBot）

```bash
python orderbot.py
```

进入交互模式后：
- 正常对话点餐
- 输入 `summary` → 生成 JSON 订单摘要
- 输入 `quit` → 退出

---

## 自由练习（your_turn.py）

修改 `BOT_PERSONA` 和 `BOT_NAME`，创建任何类型的聊天机器人：

```python
BOT_NAME = "HealthBot"
BOT_PERSONA = """
You are HealthBot, a wellness advisor...
"""
```

```bash
python your_turn.py
```
