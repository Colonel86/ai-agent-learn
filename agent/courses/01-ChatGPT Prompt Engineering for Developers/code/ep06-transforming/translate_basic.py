"""
EP06 Demo 1 — 基础翻译
演示：
  1a：英语 → 西班牙语
  1b：语言识别
  1c：同时翻译为多种语言（法语 / 西班牙语 / 英语海盗版）
  1d：正式 vs 非正式语气翻译
"""
from config import get_completion, print_section

# ── Demo 1a：英语 → 西班牙语 ──────────────────────────────────
print_section("Demo 1a: 英语 → 西班牙语")

prompt = """
Translate the following English text to Spanish:
```Hi, I would like to order a blender```
"""
print(get_completion(prompt))

# ── Demo 1b：语言识别 ─────────────────────────────────────────
print_section("Demo 1b: 语言识别")

prompt = """
Tell me which language this is:
```Combien coûte le lampadaire?```
"""
print(get_completion(prompt))

# ── Demo 1c：同时翻译为多种语言 ───────────────────────────────
print_section("Demo 1c: 同时翻译为法语 / 西班牙语 / 英语海盗版")

prompt = """
Translate the following text to French and Spanish \
and English pirate:
```I want to order a basketball```
"""
print(get_completion(prompt))

# ── Demo 1d：正式 vs 非正式语气 ───────────────────────────────
print_section("Demo 1d: 西班牙语 正式 vs 非正式")

prompt = """
Translate the following text to Spanish in both the \
formal and informal forms:
'Would you like to order a pillow?'
"""
print(get_completion(prompt))

print_section("💡 观察")
print(
    "• 语言模型掌握数百种语言，无需为每种语言单独训练\n"
    "• 正式/非正式区分：在 prompt 中明确说明即可\n"
    "• 海盗版英语 = 模型对语气/风格的迁移能力"
)
