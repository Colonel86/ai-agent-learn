# EP05 Inferring — 代码实战

对应课程：ChatGPT Prompt Engineering for Developers · 第 5 集

核心思想：**LLM 可以直接从文本中推断情感、情绪、实体和话题，替代传统 NLP 管道，且无需训练。**

---

## 项目结构

```
ep05-inferring/
├── config.py            # OpenAI 客户端 + get_completion 辅助函数
├── review_data.py       # 台灯评论 + 政府满意度调查文章（共用数据源）
├── infer_sentiment.py   # Demo 1：情感推断（自由描述 vs 单词输出）
├── infer_emotions.py    # Demo 2：情绪识别列表 + 愤怒检测
├── extract_entities.py  # Demo 3：提取商品名 & 品牌名 → JSON
├── multi_inference.py   # Demo 4：一次推断多个属性（⭐ 生产推荐模式）
├── infer_topics.py      # Demo 5：话题推断 + 新闻告警系统
├── run_all.py           # 一键运行全部或指定演示
├── your_turn.py         # 自由练习：换成你自己的评论 / 文章
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
python run_all.py        # 运行全部 5 个演示
python run_all.py 4      # 只运行 Demo 4（一次多属性推断）
python your_turn.py      # 用内置的键盘评论 + Apple 新闻练习
```

---

## 演示路径

| Demo | 文件 | 核心内容 | 关键技巧 |
|---|---|---|---|
| 1 | infer_sentiment.py | 情感推断：自由描述 vs 单词约束 | 输出格式约束 |
| 2 | infer_emotions.py | 情绪列表（≤5个）+ 愤怒检测 | 逗号分隔列表 + yes/no |
| 3 | extract_entities.py | 提取商品名 & 品牌名 → JSON | 指定 key 名称 |
| 4 | multi_inference.py | 4个属性一次推断，触发下游业务逻辑 | ⭐ 合并推断降低成本 |
| 5 | infer_topics.py | 话题推断 + 0/1 命中检测 + 自动告警 | 预设列表 + 解析告警 |

---

## 核心概念

```
传统 NLP 方案：训练分类模型 → 部署服务 → 维护更新
LLM 推断方案：写 prompt → 调用 API → 直接获得结构化结果

优势：
  ✅ 零训练数据
  ✅ 灵活更改推断维度（改 prompt 即可）
  ✅ 支持多语言、多领域
  ✅ 合并多个推断到单次调用（Demo 4）
```

---

## 自由练习

编辑 `your_turn.py` 中的 `MY_REVIEW`、`MY_STORY`、`MY_TOPICS`，替换成你真实想分析的内容（中英文均可），然后：

```bash
python your_turn.py
```

程序会自动跑完 4 个步骤：多属性推断 → 情绪识别 → 话题推断 → 告警触发。
