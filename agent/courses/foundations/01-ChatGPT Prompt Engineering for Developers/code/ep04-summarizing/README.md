# EP04 Summarizing — 代码实战

对应课程：ChatGPT Prompt Engineering for Developers · 第 4 集

核心思想：**用 Prompt 控制摘要的长度、方向和精度，以及 summarize vs extract 的本质区别。**

---

## 项目结构

```
ep04-summarizing/
├── config.py                 # OpenAI 客户端 + get_completion 辅助函数
├── reviews.py                # 4 条产品评论（所有演示共用数据源）
├── summarize_basic.py        # Demo 1：基础摘要（词数 / 句数 / 字符数限制）
├── summarize_focused.py      # Demo 2：定向摘要（运输部门 / 定价部门）
├── extract_vs_summarize.py   # Demo 3：提取 vs 摘要的精准度对比
├── batch_summarize.py        # Demo 4：批量摘要（遍历 4 条评论，20 词以内）
├── run_all.py                # 一键运行全部或指定演示
├── your_turn.py              # 自由练习：换成你自己的评论跑一遍
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
python run_all.py        # 运行全部 4 个演示
python run_all.py 1      # 只运行 Demo 1（基础摘要）
python run_all.py 3      # 只运行 Demo 3（提取 vs 摘要）
python your_turn.py      # 用内置的键盘 / 咖啡机评论练习
```

---

## 演示路径

| Demo | 文件 | 核心内容 | 关键 Prompt 技巧 |
|---|---|---|---|
| 1 | summarize_basic.py | 30 词 / 2 句 / 100 字符 三种限制 | `in at most N words/sentences/characters` |
| 2 | summarize_focused.py | 运输部门摘要 vs 定价部门摘要 | `focusing on any aspects that mention X` |
| 3 | extract_vs_summarize.py | summarize（完整） vs extract（精准） | `extract` vs `summarize` 关键词差异 |
| 4 | batch_summarize.py | 遍历 4 条评论批量生成摘要 | for 循环 + f-string 动态 prompt |

---

## 核心概念：summarize vs extract

```
summarize → 保留整体语义，可能混入无关信息
              适合：快速了解评论全貌
              
extract   → 只返回与主题直接相关的片段
              适合：结构化数据提取、定向反馈报告
```

---

## 自由练习

编辑 `your_turn.py` 中的 `MY_REVIEWS` 和 `FOCUS_TOPIC`，替换成你真实想分析的评论，然后：

```bash
python your_turn.py
```

程序会自动跑完 4 个步骤（基础摘要 → 定向摘要 → 信息提取 → 情感判断）。

> 💡 Step 4 的情感判断是 EP05 Inferring 的预热内容！
