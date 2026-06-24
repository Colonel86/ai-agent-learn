# Tasks — 001-note-lint

> 循环的**状态文件**。`/spec-iterate` 每轮取第一个 `- [ ]`。
> 状态：`[ ]` 未做 · `[x]` 已验收 · `[!]` 阻塞/交人。

- [x] T1 实现 `count_words(text) -> int`（AC1）｜验收: `pytest -k test_count_words`
- [ ] T2 实现 `find_banned_words(text, banned=None) -> list[str]`（AC2）｜验收: `pytest -k test_find_banned_words`
- [ ] T3 实现 `check_heading(text) -> bool`（AC3）｜验收: `pytest -k test_check_heading`
- [ ] T4 实现 `lint_note(text, min_words=1) -> list[str]`（AC4，依赖 T1-T3）｜验收: `pytest -k test_lint_note`
