# EP03 Iterative Prompt Development — 代码实战

对应课程：ChatGPT Prompt Engineering for Developers · 第 3 集

核心思想：**没有完美的第一次 Prompt，关键是迭代过程。**

---

## 项目结构

```
ep03-iterative/
├── config.py           # OpenAI 客户端 + get_completion 辅助函数
├── fact_sheet.py       # 椅子产品规格表（所有版本共用的输入数据）
├── v1_too_long.py      # 第1版：原始 prompt，问题：输出太长
├── v2_word_limit.py    # 第2版：加字数/句数限制
├── v3_target_audience.py  # 第3版：指定受众（家具零售商）+ 聚焦材料
├── v4_add_product_ids.py  # 第4版：末尾附加产品 ID
├── v5_html_with_table.py  # 第5版（终极）：HTML 格式 + 产品尺寸表格
├── run_all.py          # 一键运行全部或指定版本
├── your_turn.py        # 自由练习：换成你自己的产品规格跑一遍
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
python run_all.py        # 运行全部 5 个版本（观察迭代过程）
python run_all.py 5      # 只运行终极版（生成 output.html）
python your_turn.py      # 用内置的耳机规格表练习
```

---

## 迭代路径

| 版本 | 文件 | 新增内容 | 解决的问题 |
|---|---|---|---|
| V1 | v1_too_long.py | 基础 prompt | — |
| V2 | v2_word_limit.py | `Use at most 50 words` | 输出太长 |
| V3 | v3_target_audience.py | 指定受众 + 聚焦材料 | 内容方向不对 |
| V4 | v4_add_product_ids.py | 末尾附加产品 ID | 缺少关键信息 |
| V5 | v5_html_with_table.py | HTML 格式 + 尺寸表格 | 格式不适合网页 |

运行 V5 后会生成 `output.html`，用浏览器打开可直接预览渲染效果。

---

## 自由练习

编辑 `your_turn.py` 中的 `MY_FACT_SHEET`，替换成任意产品的规格描述，然后：

```bash
python your_turn.py
```

程序会自动跑完 5 个迭代步骤并生成 `your_turn_output.html`。
