"""
EP05 自由练习 — 换成你自己的评论 / 文章跑一遍

步骤：
  1. 把 MY_REVIEW 替换成你想分析的产品评论
  2. 把 MY_STORY 替换成你想分析的新闻文章（可以是中文）
  3. 按需修改 MY_TOPICS 监控话题列表
  4. python your_turn.py
"""
import json
from config import get_completion, print_section

# ── 在这里替换 ───────────────────────────────────────────────
MY_REVIEW = """
I bought this mechanical keyboard for gaming and coding.
The switches feel amazing and the RGB lighting is stunning.
However, the software to customize the lights is very buggy
and crashed my computer twice. Customer support was helpful
and guided me through a fix. Overall happy with the hardware
but the software needs serious improvement.
"""

MY_STORY = """
Apple announced record quarterly revenue of $120 billion,
driven by strong iPhone 15 sales and growing services income.
CEO Tim Cook highlighted the company's commitment to AI integration
across all product lines in the coming year. The stock rose 4%
following the announcement. Analysts praised the results but
noted increasing competition from Samsung in emerging markets.
"""

MY_TOPICS = ["apple", "iphone", "samsung", "ai", "stock market"]
# ─────────────────────────────────────────────────────────────

# Step 1: 情感 + 愤怒 + 实体（一次推断）
print_section("Step 1: 评论多属性推断（JSON）")

prompt_review = f"""
Identify the following items from the review text:
- Sentiment (positive or negative)
- Is the reviewer expressing anger? (true or false)
- Item purchased by reviewer
- Company that made the item

Format your response as a JSON object with
"Sentiment", "Anger", "Item" and "Brand" as the keys.
If the information isn't present, use "unknown" as the value.
Format the Anger value as a boolean.

Review text: '''{MY_REVIEW}'''
"""

result_review = get_completion(prompt_review)
print(result_review)

try:
    data = json.loads(result_review)
    if data.get("Anger") is True:
        print("\n🚨 告警：检测到愤怒情绪！")
    elif data.get("Sentiment") == "negative":
        print("\n⚠️  负面评论，建议跟进。")
    else:
        print("\n✅ 正面评论。")
except json.JSONDecodeError:
    pass

# Step 2: 情绪列表
print_section("Step 2: 情绪识别（≤5 个）")

prompt_emotions = f"""
Identify a list of emotions that the writer of the \
following review is expressing. Include no more than \
five items in the list. Format your answer as a list of \
lower-case words separated by commas.

Review text: '''{MY_REVIEW}'''
"""

result_emotions = get_completion(prompt_emotions)
print(result_emotions)

# Step 3: 话题推断
print_section("Step 3: 文章话题推断（5 个）")

prompt_topics = f"""
Determine five topics that are being discussed in the \
following text, which is delimited by triple backticks.
Make each item one or two words long.
Format your response as a list of items separated by commas.

Text sample: '''{MY_STORY}'''
"""

result_topics = get_completion(prompt_topics)
print(result_topics)

# Step 4: 话题命中检测 & 告警
print_section(f"Step 4: 话题命中检测（监控：{MY_TOPICS}）")

prompt_alert = f"""
Determine whether each item in the following list of \
topics is a topic in the text below, delimited by triple backticks.

Give your answer as follows:
item from the list: 0 or 1

List of topics: {", ".join(MY_TOPICS)}

Text sample: '''{MY_STORY}'''
"""

result_alert = get_completion(prompt_alert)
print(result_alert)

topic_dict = {}
for line in result_alert.strip().split("\n"):
    if ":" in line:
        key, val = line.rsplit(":", 1)
        try:
            topic_dict[key.strip().lower()] = int(val.strip())
        except ValueError:
            pass

print("\n触发告警：")
triggered = [t for t in MY_TOPICS if topic_dict.get(t) == 1]
if triggered:
    for t in triggered:
        print(f"  🔔 ALERT: '{t}' detected in article!")
else:
    print("  （无告警触发）")

print("\n✅ 练习完成！尝试修改 MY_REVIEW / MY_STORY / MY_TOPICS，观察结果变化。")
