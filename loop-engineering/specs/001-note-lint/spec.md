# Spec: 极简笔记检查器（note-lint）

> spec-kit `specs/<feature>/spec.md` 的手搓版（真实项目由 `/speckit.specify` 生成）。

## 为什么
给「写作流水线闭环」提供一个客观门控：机械判断一篇笔记是否达标，命中即打回。
（正是 Loop Engineering 文章作者自己跑的那个写作闭环里的 gate。）

## 做什么
一个零依赖纯函数模块 `notelint.py`，提供 4 个函数。

## 验收标准（= 验收 subagent 的 rubric）
- **AC1 `count_words(text)`**：按空白分词计数；空串 = 0。验收：`pytest -k test_count_words`
- **AC2 `find_banned_words(text, banned=None)`**：返回出现的禁用词（默认表：很显然/众所周知/不言而喻），按禁用表顺序去重。验收：`pytest -k test_find_banned_words`
- **AC3 `check_heading(text)`**：首个非空行以 `# ` 开头返回 True，否则 False。验收：`pytest -k test_check_heading`
- **AC4 `lint_note(text, min_words=1)`**：聚合 AC1-3，返回问题列表（含「缺少 H1 标题」「禁用词: X」「字数过少」），无问题返回 `[]`。验收：`pytest -k test_lint_note`

全部以 `test_notelint.py` 断言为准。
