"""极简笔记检查器：Loop Engineering 学习沙盒的门控目标。

四个纯函数，初始都是桩（raise NotImplementedError），由闭环循环逐个补全。
实现一个 → 它对应的验收测试由红变绿 → /spec-iterate 勾掉一个任务。
"""
from __future__ import annotations

BANNED_DEFAULT = ["很显然", "众所周知", "不言而喻"]


def count_words(text: str) -> int:
    """T1 / AC1：按空白分词计数，空串返回 0。"""
    return len(text.split())


def find_banned_words(text: str, banned: list[str] | None = None) -> list[str]:
    """T2 / AC2：返回 text 中出现的禁用词，按禁用表顺序去重。"""
    raise NotImplementedError("T2")


def check_heading(text: str) -> bool:
    """T3 / AC3：首个非空行以 '# ' 开头返回 True，否则 False。"""
    raise NotImplementedError("T3")


def lint_note(text: str, min_words: int = 1) -> list[str]:
    """T4 / AC4：聚合 T1-T3，返回问题列表；无问题返回空列表。"""
    raise NotImplementedError("T4")
