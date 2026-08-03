# Automated Testing for LLMOps · 本地化

课程原版 (CircleCI + DeepLearning.AI, 2023): langchain 0.0.326 + openai 0.28 + gpt-3.5-turbo,
评估靠 push 到课程方 GitHub 仓库触发 CircleCI 流水线。

本地化 (2026-08):
- **栈**: langchain 1.3 + langchain-openai 1.4 + openai 2.x, 模型换 DeepSeek(`.env` 配置)
- **CI**: 课程方的 CircleCI/GitHub token 已不可用, 云端流水线改为**本地 pytest 模拟**
  (commit/release/full 三种 eval-mode 对应跑不同测试文件); CircleCI 配置文件原样保留, L5 做解析讲解
- 共享适配层 `local_stack.py`(DeepSeek ChatOpenAI 工厂 + pytest job 模拟器)

## 运行

```bash
cd code
uv venv --python 3.12 .venv
uv pip install -p .venv/bin/python -r requirements.txt

cd L2 && ../.venv/bin/python main.py   # 持续集成概述: 应用 + 第一批 per-commit 评估
cd L3 && ../.venv/bin/python main.py   # 规则评估 + 模型评分分层, 含「门禁必须会红」演示
cd L4 && ../.venv/bin/python main.py   # 幻觉检测 + 数据集回归(Italy 预期失败) + HTML 报告工件
cd L5 && ../.venv/bin/python main.py   # CircleCI 配置 6 版演进解析(不调 LLM)
```

## 迁移要点

| 课程原版 | 本地化 |
|---|---|
| `langchain.prompts` / `langchain.chat_models` / `langchain.schema.output_parser` | `langchain_core.prompts` / `langchain_openai` / `langchain_core.output_parsers`(LCEL 管道语法不变) |
| `ChatOpenAI(model="gpt-3.5-turbo")` | `local_stack.make_llm()`: DeepSeek + thinking disabled + temperature 0 |
| push_files + trigger_*_evals(CircleCI API) | `local_stack.run_pytest()` 本地跑同一批测试 |
| CI store_artifacts | L4 落盘 `quiz_eval_report.html` |

已知与原课不同的行为:
- L4 幻觉检测: 课程原版依赖 gpt-3.5 对 "books" 真的幻觉出一份 quiz 再被 judge 抓住;
  DeepSeek 按 prompt 规则直接拒答(第一道防线生效) → 反向设计为固定 fixture:
  正样本(真实 quiz)->Y / 负样本(手工构造的库外事实 quiz)->N, judge 行为可确定性验证
- L4 数据集里的 "Quiz me about Italy": quiz bank 无 Italy 主题, DeepSeek 严格遵循
  「类目须精确匹配」规则而拒答 → 该断言**按课程设计失败**(演示数据集应混入边界用例)
- judge 输出加了 "Output only the single letter" 约束并 `.strip()` 后比较, 提升 Y/N 稳定性
- 课程原版 L2 `evaluate_refusal` 把 assistant_chain 的位置参数传反(system/human 互换), 已修正
