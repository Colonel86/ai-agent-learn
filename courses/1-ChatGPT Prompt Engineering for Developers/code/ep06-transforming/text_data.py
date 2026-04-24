"""
数据源 — 所有演示共用
"""

# ── 通用翻译器：多语言 IT 问题 ────────────────────────────────
user_messages = [
    "La performance du système est plus lente que d'habitude.",  # 法语：系统性能比平时慢
    "Mi monitor tiene píxeles que no se iluminan.",              # 西班牙语：我的显示器有像素不亮
    "Il mio mouse non funziona",                                 # 意大利语：我的鼠标不工作
    "Mój klawisz Ctrl jest zepsuty",                             # 波兰语：我的 Ctrl 键坏了
    "我的屏幕在闪烁",                                              # 中文：我的屏幕在闪烁
]

# ── 格式转换：餐厅员工 JSON ────────────────────────────────────
data_json = {
    "resturant employees": [
        {"name": "Shyam", "email": "shyamjaiswal@gmail.com"},
        {"name": "Bob",   "email": "bob32@gmail.com"},
        {"name": "Jai",   "email": "jai87@gmail.com"},
    ]
}

# ── 拼写/语法检查：含错误的句子列表 ──────────────────────────
grammar_texts = [
    "The girl with the black and white puppies have a ball.",           # 主谓不一致
    "Yolanda has her notebook.",                                        # 正确
    "Its going to be a long day. Does the car need it's oil changed?", # 同音异义词
    "Their goes my freedom. There going to bring they're suitcases.",  # 同音异义词
    "Your going to need you're notebook.",                              # 同音异义词
    "That medicine effects my ability to sleep. Have you heard of the butterfly affect?",  # 同音异义词
    "This phrase is to cherck chatGPT for speling abilitty",           # 拼写错误
]

# ── 熊猫毛绒玩具评论（用于校对 + APA 改写）─────────────────────
panda_review = """
Got this for my daughter for her birthday cuz she keeps taking \
mine from my room.  Yes, adults also like pandas too.  She takes \
it everywhere with her, and it's super soft and cute.  One of the \
ears is a bit lower than the other, and I don't think that was \
designed to be asymmetrical. It's a bit small for what I paid for it \
though. I think there might be other options that are bigger for \
the same price.  It arrived a day earlier than expected, so I got \
to play with it myself before I gave it to my daughter.
"""
