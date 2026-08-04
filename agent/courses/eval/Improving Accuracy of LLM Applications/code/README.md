# Improving Accuracy of LLM Applications · 本地化

课程原版 (Lamini + DeepLearning.AI): NBA SQL Agent 为主线, 用「评估驱动的准确率
提升阶梯」逐级压幻觉, 跑在 Lamini 托管 Llama-3-8B 上, 微调经 `llm.train()` 派发服务端。

本地化 (2026-08): 推理全换 DeepSeek (`local_stack.py`), 结构化输出 output_type ->
json_object 模式; **微调环节衔接仓库既有项目 `../projects/nba_sql_tuner`**
(本地 LoRA 真跑 finetune vs memory tuning, 本课 L5 生成的数据可直接喂入)。

## 运行

```bash
cd code
uv venv --python 3.12 .venv
uv pip install -p .venv/bin/python -r requirements.txt

cd L1 && ../.venv/bin/python main.py   # 概率分布视角看幻觉 + llama3 prompt 模板
cd L2 && ../.venv/bin/python main.py   # SQL Agent: 贫/富 schema 对照, silently wrong 现场
cd L3 && ../.venv/bin/python main.py   # gold set 20 条批量评估: 有效% / 正确%
cd L5 && ../.venv/bin/python main.py   # working backwards 造数据 + 可执行过滤 -> LoRA 衔接
```

(L4 为纯理论课无代码, 见 notes/L4*.md)

## 实测结果与课程叙事的对照

- L2: deepseek 在贫乏 schema 下只 REPLACE 掉 `$` 忘了逗号 —— CAST 在逗号处截断,
  等于按"百万位"排序, **这题碰巧对**; 比课程原版(字符串排序)更隐蔽的 silently wrong
- L3 基线: 有效 SQL 90% / 正确 SQL 30% —— percentile/median 类(脏字符串列上的
  分位数计算)全错, 与课程"看起来能跑 ≠ 对"的叙事一致, 失败清单即 L5 的靶子
- L5: 6 条 gold 生成 12 条新 (question, sql), 可执行过滤全通过

## 与课程的结构差异

| 课程 | 本地化 |
|---|---|
| lamini.Lamini().generate(prompt, output_type={...}) | `local_stack.ds_json` (json_object + 解析) |
| GenerationPipeline (异步 QueryStage/ScoreStage) | L3 main.py 普通循环, 指标一致 |
| llm.train() 派发 Lamini | `../projects/nba_sql_tuner` 本地 LoRA (真跑两种 tuning) |
| make_llama_3_prompt 手工拼模板 | 保留作教学(L1①), 实际调用走 chat messages |
