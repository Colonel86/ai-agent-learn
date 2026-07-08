"""nba_sql_tuner — 本地复现 DeepLearning.AI/Lamini《Improving Accuracy of LLM Applications》。

课程主线:一个 NBA SQL Agent,用「评估驱动的准确率提升阶梯」把幻觉逐级压下去:
baseline prompt → 改进 schema → few-shot/RAG → 标准 fine-tuning → memory tuning。

本包把课程依赖的 Lamini 托管服务换成本地 HF transformers 小模型(可插拔),
并用 LoRA 真跑「标准 fine-tuning vs memory tuning」的对比闭环。
"""

__all__ = ["config", "schema", "prompt", "db", "backend", "agent", "evaluate"]
