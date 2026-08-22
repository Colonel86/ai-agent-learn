"""演示 2: 评估结果回写 — 发明一个课程里没有的评估 'Answer Brevity Demo'

流程 = L7 的通用三步:
  ① SpanQuery 导出目标 span (拿到以 span_id 为索引的 DataFrame)
  ② 打标签 (这里用纯代码: 回答字数 < 800 算 concise, 否则 verbose)
  ③ log_span_annotations_dataframe 回写 (靠 DataFrame 索引里的 span_id 对号入座)
"""
import pandas as pd
from phoenix.client import Client
from phoenix.client.types.spans import SpanQuery

client = Client(base_url="http://localhost:6006")
PROJECT = "evaluating-agent"

# ① 导出: 所有 AGENT span 的最终回答
q = SpanQuery().where("span_kind == 'AGENT'").select("output.value")
df = client.spans.get_spans_dataframe(query=q, project_name=PROJECT, timeout=120)
df = df.rename(columns={"output.value": "response"}).dropna(subset=["response"])
print(f"① 导出 {len(df)} 个 AGENT span, 索引 = {df.index.name}")

# ② 打标签: 纯 pandas, 不涉及任何 LLM
df["chars"] = df["response"].str.len()
df["label"] = df["chars"].map(lambda n: "concise" if n < 800 else "verbose")
df["score"] = (df["label"] == "concise").astype(int)
print("② 打完标签的评估表 (前 5 行):")
print(df[["chars", "label", "score"]].head(5).to_string())
print(f"   简洁率: {df['score'].mean():.2f}")

# ③ 回写: 只需要 label/score 两列, span_id 在索引里
client.spans.log_span_annotations_dataframe(
    dataframe=df[["label", "score"]],
    annotation_name="Answer Brevity Demo",
    annotator_kind="CODE",
)
print(f"③ 已把 {len(df)} 条 'Answer Brevity Demo' 注解回写到 Phoenix — 去 UI 刷新看新徽章")
