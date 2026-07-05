"""
EP05 Demo 2 — 情绪识别 & 愤怒检测
演示：
  2a：识别评论中表达的情绪列表（≤5 个，逗号分隔）
  2b：判断评论者是否在表达愤怒（yes / no）
"""
from config import get_completion, print_section
from review_data import lamp_review

# ── Demo 2a：情绪列表 ──────────────────────────────────────────
print_section("Demo 2a: 情绪识别（最多 5 个，逗号分隔）")

prompt_emotions = f"""
Identify a list of emotions that the writer of the \
following review is expressing. Include no more than \
five items in the list. Format your answer as a list of \
lower-case words separated by commas.

Review text: '''{lamp_review}'''
"""

response_emotions = get_completion(prompt_emotions)
print(response_emotions)

# 把结果解析成 Python list
emotion_list = [e.strip() for e in response_emotions.split(",")]
print(f"\n解析成列表：{emotion_list}")

# ── Demo 2b：愤怒检测 ──────────────────────────────────────────
print_section("Demo 2b: 愤怒检测（yes / no）")

prompt_anger = f"""
Is the writer of the following review expressing anger?\
The review is delimited with triple backticks. \
Give your answer as either yes or no.

Review text: '''{lamp_review}'''
"""

response_anger = get_completion(prompt_anger)
print(response_anger)

# ── 说明 ──────────────────────────────────────────────────────
print_section("💡 观察")
print(
    "情绪识别用途：\n"
    "  • 监控客服工单，自动标记高风险（愤怒/沮丧）工单\n"
    "  • 电商评论分析，统计各产品的情绪分布\n"
    "\n"
    "愤怒检测用途：\n"
    "  • 自动触发人工介入，优先响应不满用户\n"
    "  • 品牌舆情监控"
)
