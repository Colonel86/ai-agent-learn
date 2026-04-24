# EP02 Guidelines — 代码实战

对应课程：ChatGPT Prompt Engineering for Developers · 第 2 集

---

## 项目结构

```
ep02-guidelines/
├── config.py                    # OpenAI 客户端 + get_completion 辅助函数
├── tactic1_delimiters.py        # 策略1：分隔符（含注入攻击对比）
├── tactic2_structured_output.py # 策略2：结构化输出（JSON / HTML）
├── tactic3_check_conditions.py  # 策略3：条件检查
├── tactic4_few_shot.py          # 策略4：少样本提示
├── tactic5_specify_steps.py     # 策略5：指定步骤 + 格式模板
├── tactic6_work_out_solution.py # 策略6：先自行推理（⭐ 最重要）
├── run_all.py                   # 一键运行全部或指定 tactic
├── requirements.txt
└── .env.example
```

---

## 快速开始

**1. 安装依赖**
```bash
pip install -r requirements.txt
```

**2. 配置 API Key**
```bash
cp .env.example .env
# 编辑 .env，填入你的 OPENAI_API_KEY
```

**3. 运行**
```bash
# 运行全部（按顺序）
python run_all.py

# 只运行某一个 tactic（推荐先跑 6，最有冲击感）
python run_all.py 6

# 或者单独运行某个文件
python tactic1_delimiters.py
```

---

## 各文件说明

| 文件 | 策略 | 核心演示 |
|---|---|---|
| tactic1 | 分隔符 | 正常使用 + 注入攻击被拦截 vs 未被拦截 对比 |
| tactic2 | 结构化输出 | JSON 生成并用 `json.loads()` 解析；HTML 表格 |
| tactic3 | 条件检查 | 有步骤 vs 无步骤文本，两种输出对比 |
| tactic4 | Few-shot | 祖父比喻风格；中文古诗词风格 |
| tactic5 | 指定步骤 | 无格式 vs 有格式模板，输出可预测性对比 |
| tactic6 | 先自行推理 | ⭐ 太阳能数学题：直接判断（被误导）vs 先解题（发现错误）|

---

## 自由练习

每个文件末尾都有 `your_turn()` 函数，里面有 `TODO` 注释，取消最后的 `# your_turn()` 注释即可运行。建议按顺序完成每个练习后再进入下一个 tactic。
