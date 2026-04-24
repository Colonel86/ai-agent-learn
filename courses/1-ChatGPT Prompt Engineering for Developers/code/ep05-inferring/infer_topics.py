"""
EP05 Demo 5 — 话题推断 & 新闻告警
演示：
  5a：从新闻文章中推断 5 个话题（逗号分隔）
  5b：预设话题列表，检测文章是否涉及各话题（0/1 输出）
  5c：自动触发告警（如检测到 NASA 相关报道）
"""
from config import get_completion, print_section
from review_data import story

# ── Demo 5a：推断 5 个话题 ────────────────────────────────────
print_section("Demo 5a: 推断 5 个话题")

prompt_topics = f"""
Determine five topics that are being discussed in the \
following text, which is delimited by triple backticks.

Make each item one or two words long.

Format your response as a list of items separated by commas.

Text sample: '''{story}'''
"""

response_topics = get_completion(prompt_topics)
print("模型输出：")
print(response_topics)

topic_inferred = [t.strip() for t in response_topics.split(",")]
print(f"\n解析成列表：{topic_inferred}")

# ── Demo 5b：话题命中检测（0/1） ──────────────────────────────
print_section("Demo 5b: 话题命中检测（预设列表 vs 文章）")

topic_list = [
    "nasa", "local government", "engineering",
    "employee satisfaction", "federal government"
]

prompt_alert = f"""
Determine whether each item in the following list of \
topics is a topic in the text below, which
is delimited with triple backticks.

Give your answer as follows:
item from the list: 0 or 1

List of topics: {", ".join(topic_list)}

Text sample: '''{story}'''
"""

response_alert = get_completion(prompt_alert)
print("模型输出：")
print(response_alert)

# 解析 0/1 结果字典
topic_dict = {}
for line in response_alert.strip().split("\n"):
    if ":" in line:
        key, val = line.rsplit(":", 1)
        try:
            topic_dict[key.strip().lower()] = int(val.strip())
        except ValueError:
            pass

print(f"\n解析成字典：{topic_dict}")

# ── Demo 5c：自动告警 ─────────────────────────────────────────
print_section("Demo 5c: 自动告警触发")

alerts_triggered = []
if topic_dict.get("nasa") == 1:
    alerts_triggered.append("🚀 ALERT: New NASA story!")
if topic_dict.get("employee satisfaction") == 1:
    alerts_triggered.append("📊 ALERT: Employee satisfaction report detected!")
if topic_dict.get("federal government") == 1:
    alerts_triggered.append("🏛️  ALERT: Federal government topic detected!")

if alerts_triggered:
    for alert in alerts_triggered:
        print(alert)
else:
    print("（无告警触发）")

# ── 说明 ──────────────────────────────────────────────────────
print_section("💡 观察")
print(
    "应用场景：\n"
    "  • 媒体监控系统：订阅关键词，自动推送相关新闻\n"
    "  • 企业舆情告警：关注竞品、监管、品牌话题\n"
    "  • 内容分类流水线：自动为文章打标签\n"
    "\n"
    "⭐ 关键技巧：\n"
    "  '0 or 1' 格式约束 → 输出可直接被代码解析\n"
    "  无需 NLP 训练，prompt 即业务逻辑"
)
