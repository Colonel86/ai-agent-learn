#!/usr/bin/env bash
# 硬门控（build 层）：代码能 lint、能导入、测试能被收集（无语法/导入错误）。
# 返回 0 = 通过。
#
# 注意两层门控的区别（重要，是这个沙盒要教的核心之一）：
#   - 硬门控（本脚本）：只保证“代码没坏”。即使功能没实现，桩函数能导入，所以它从一开始就是绿的。
#   - 任务验收：单个任务是否达标，由 /spec-iterate 跑该任务专属测试（pytest -k ...）+ 独立 subagent 判定。
set -euo pipefail
cd "$(dirname "$0")"

PY="../.venv/bin/python"
[ -x "$PY" ] || PY="python3"

echo "▶ lint (ruff)"
if command -v ruff >/dev/null 2>&1; then
  ruff check .
else
  echo "  (ruff 未安装，跳过；装：uv pip install ruff)"
fi

echo "▶ import & collect (pytest --co)"
"$PY" -m pytest --co -q >/dev/null

echo "✅ hard gate passed（代码可构建）"
