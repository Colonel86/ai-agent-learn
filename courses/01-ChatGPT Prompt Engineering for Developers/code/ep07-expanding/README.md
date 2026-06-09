# EP07 Expanding — 代码实战

对应课程：ChatGPT Prompt Engineering for Developers · 第 7 集

核心思想：**用 Prompt 将短输入"扩展"为长输出，并用 temperature 参数控制输出的多样性。**

---

## 项目结构

```
ep07-expanding/
├── config.py            # OpenAI 客户端 + get_completion 辅助函数
├── review_data.py       # 3 条不同情感的产品评论（搅拌机/台灯/电动牙刷）
├── email_reply.py       # Demo 1：自动邮件回复（negative/positive/neutral 三种情感）
├── temperature_demo.py  # Demo 2：temperature=0 vs 0.7，连续 3 次对比（⭐核心概念）
├── run_all.py           # 一键运行全部或指定演示
├── your_turn.py         # 自由练习：换成自己的评论 + 调整 temperature
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
python run_all.py        # 运行全部 2 个演示
python run_all.py 1      # Demo 1 — 3 种情感的邮件回复
python run_all.py 2      # Demo 2 — temperature 对比（调用 6 次 API）
python your_turn.py      # 换成自己的评论练习
```

---

## 演示路径

| Demo | 文件 | 核心内容 | 关键点 |
|---|---|---|---|
| 1 | email_reply.py | 根据情感自动生成客服邮件，使用评论具体细节 | `Review sentiment: {sentiment}` 作为上下文 |
| 2 | temperature_demo.py | temperature=0 每次相同；0.7 每次不同 | ⭐ 理解随机性 vs 可预测性的权衡 |

---

## 核心概念：Temperature

```
temperature = 0    → 总是选最高概率词 → 输出稳定可复现
                      ✅ 推荐：提取、分类、结构化任务、生产环境

temperature = 0.7  → 引入随机性，偶尔选概率较低的词 → 输出有变化
                      ✅ 推荐：邮件写作、内容改写、创意生成

temperature = 1.0  → 最大随机性
                      ✅ 推荐：头脑风暴、故事创作
```

---

## 自由练习

编辑 `your_turn.py` 中的 `MY_REVIEW`、`MY_SENTIMENT`、`MY_TEMPERATURE`，然后：

```bash
python your_turn.py
```

程序会同时输出指定 temperature 和 temperature=0 的两个版本供对比。
