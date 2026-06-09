# EP06 Transforming — 代码实战

对应课程：ChatGPT Prompt Engineering for Developers · 第 6 集

核心思想：**用 Prompt 进行文本转换——翻译、语气调整、格式转换、拼写语法修正。**

---

## 项目结构

```
ep06-transforming/
├── config.py               # OpenAI 客户端 + get_completion 辅助函数
├── text_data.py            # 所有演示共用的数据源
├── translate_basic.py      # Demo 1：基础翻译（EN→ES、语言识别、多语言、正式/非正式）
├── translate_universal.py  # Demo 2：通用翻译器（5种语言 IT 问题 → 英语+韩语）
├── transform_tone.py       # Demo 3：语气转换（俚语 → 商务信函）
├── convert_format.py       # Demo 4：格式转换（JSON → HTML 表格，生成 output.html）
├── spellcheck.py           # Demo 5：拼写语法检查 + redlines 差异对比 + APA 改写
├── run_all.py              # 一键运行全部或指定演示
├── your_turn.py            # 自由练习（翻译 / 语气转换 / 语法检查 / APA 改写）
├── requirements.txt
└── .env.example
```

运行 Demo 4 会生成 `output.html`（格式转换结果）
运行 Demo 5 会生成 `diff_output.html`（差异对比）和 `apa_output.md`（APA 改写）

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
python run_all.py 4      # 只运行 Demo 4（JSON → HTML）
python run_all.py 5      # 只运行 Demo 5（拼写检查 + APA）
python your_turn.py      # 换成你自己的文本练习
```

---

## 演示路径

| Demo | 文件 | 核心内容 | 关键技巧 |
|---|---|---|---|
| 1 | translate_basic.py | EN→ES、语言识别、多语言翻译、正式/非正式 | 多种翻译指令格式 |
| 2 | translate_universal.py | 5种语言 IT 问题批量翻译 | for 循环 + 语言识别 |
| 3 | transform_tone.py | 俚语 → 商务信函 | 在 prompt 中指定源/目标风格 |
| 4 | convert_format.py | JSON → HTML 表格，保存 output.html | 同时描述输入/输出格式 |
| 5 | spellcheck.py | 批量校对 + redlines 差异 + APA 改写 | 多重指令叠加 |

---

## 特色依赖

- **`redlines`**：可视化展示文本差异（Demo 5），安装后自动启用
  ```bash
  pip install redlines --break-system-packages
  ```
  未安装时 Demo 5 会跳过差异对比，其他功能正常运行

---

## 自由练习

编辑 `your_turn.py` 中的 `MY_TEXT`、`MY_CASUAL_TEXT`、`MY_DRAFT`，然后：

```bash
python your_turn.py
```

运行完成后会自动生成 `your_turn_apa.md`。
