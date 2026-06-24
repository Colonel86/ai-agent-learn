"""验收测试 = 门控的客观依据。每个 test 对应 tasks.md 的一个任务。

初始全红（桩函数）。循环每完成一个任务，对应的 test 变绿。
全绿 = 整个 feature 完成。
"""
from notelint import check_heading, count_words, find_banned_words, lint_note


def test_count_words():  # 验收 T1
    assert count_words("hello world") == 2
    assert count_words("  a  b  c ") == 3
    assert count_words("") == 0


def test_find_banned_words():  # 验收 T2
    assert find_banned_words("众所周知，这很显然") == ["很显然", "众所周知"]
    assert find_banned_words("none here") == []
    assert find_banned_words("foo bar foo", ["foo"]) == ["foo"]


def test_check_heading():  # 验收 T3
    assert check_heading("# 标题\n正文") is True
    assert check_heading("\n\n# 标题") is True
    assert check_heading("正文没有标题") is False


def test_lint_note():  # 验收 T4
    assert lint_note("# 好标题\n正文内容") == []
    issues = lint_note("没有标题，但很显然")
    assert "缺少 H1 标题" in issues
    assert "禁用词: 很显然" in issues
