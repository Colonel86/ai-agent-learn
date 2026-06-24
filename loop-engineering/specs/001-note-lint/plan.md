# Plan

> spec-kit `specs/<feature>/plan.md` 的手搓版（真实项目由 `/speckit.plan` 生成）。

- **语言/运行**：Python 3.11+，纯标准库，无第三方依赖。
- **布局**：沙盒从简，扁平单文件 `notelint.py` + `test_notelint.py`。
- **门控**：`gate.sh` = `ruff check .` + `pytest --co`（硬门控）；任务验收用 `pytest -k <test>`。
- **循环**：`/loop /spec-iterate loop-engineering/specs/001-note-lint`，单步执行器见仓库根 `.claude/commands/spec-iterate.md`。
- **停点**：tasks 全部 `[x]` → DONE；接受率 < 0.5 → STOP 交人。
