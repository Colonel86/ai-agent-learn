"""
数据源 — 三条不同情感的产品评论
（搅拌机负面评论来自课程原版 notebook）
"""

# ── 负面评论：搅拌机（价格上涨 + 品质下降 + 保修过期）──────────
review_blender = """
So, they still had the 17 piece system on seasonal \
sale for around $49 in the month of November, about \
half off, but for some reason (call it price gouging) \
around the second week of December the prices all went \
up to about anywhere from between $70-$89 for the same \
system. And the 11 piece system went up around $10 or \
so in price also from the earlier sale price of $29. \
So it looks okay, but if you look at the base, the part \
where the blade locks into place doesn't look as good \
as in previous editions from a few years ago, but I \
plan to be very gentle with it (example, I crush \
very hard items like beans, ice, rice, etc. in the \
blender first then pulverize them in the serving size \
I want in the blender then switch to the whipping \
blade for a finer flour, and use the cross cutting blade \
first when making smoothies, then use the flat blade \
if I need them finer/less pulpy). Special tip when making \
smoothies, finely cut and freeze the fruits and \
vegetables (if using spinach-lightly stew soften the \
spinach then freeze until ready for use-and if making \
sorbet, use a small to medium sized food processor) \
that you plan to use that way you can avoid adding so \
much ice if at all-when making your smoothie. \
After about a year, the motor was making a funny noise. \
I called customer service but the warranty expired \
already, so I had to buy another one. FYI: The overall \
quality has gone done in these types of products, so \
they are kind of counting on brand recognition and \
consumer loyalty to maintain sales. Got it in about \
two days.
"""
sentiment_blender = "negative"

# ── 正面评论：台灯（服务好 + 配件及时补发）────────────────────
review_lamp = """
Needed a nice lamp for my bedroom, and this one had \
additional storage and not too high of a price point. \
Got it fast. The string to our lamp broke during the \
transit and the company happily sent over a new one. \
Came within a few days as well. It was easy to put \
together. I had a missing part, so I contacted their \
support and they very quickly got me the missing piece! \
Lumina seems to me to be a great company that cares \
about their customers and products!!
"""
sentiment_lamp = "positive"

# ── 中性评论：电动牙刷（优缺点参半）──────────────────────────
review_toothbrush = """
My dental hygienist recommended an electric toothbrush, \
which is why I got this. The battery life seems to be \
pretty impressive so far. After initial charging and \
leaving the charger plugged in for the first week to \
condition the battery, I've unplugged the charger and \
been using it for twice daily brushing for the last \
3 weeks all on the same charge. But the toothbrush head \
is too small. I've seen baby toothbrushes bigger than \
this one. Overall if you can get this one around the \
$50 mark, it's a good deal. The manufacturer's \
replacement heads are pretty expensive, but you can \
get generic ones that're more reasonably priced.
"""
sentiment_toothbrush = "neutral"

# 全部打包，方便批量演示
ALL_REVIEWS = [
    ("搅拌机", review_blender,    sentiment_blender),
    ("台灯",   review_lamp,       sentiment_lamp),
    ("电动牙刷", review_toothbrush, sentiment_toothbrush),
]
