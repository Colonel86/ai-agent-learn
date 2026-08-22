#!/usr/bin/env bash
# agent-arch-kit · thin non-destructive installer
# 用法: bash install.sh [target-repo-path]  （默认当前目录）
# 原则: 只做投影(拷贝), 从不覆盖已有文件; source of truth 永远是 template/ 下的可读文件

set -euo pipefail

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$(pwd)}"
MATRIX_SOURCE="${MATRIX_SOURCE:-}"   # 可选: 选型矩阵源目录(vendored 模式), 如 .../agent/skills/agent-selection

if [[ ! -d "$TARGET" ]]; then
  echo "✗ 目标目录不存在: $TARGET" >&2; exit 1
fi

copied=0; skipped=0

project() {
  local rel="$1"
  local src="$KIT_DIR/template/$rel"
  local dst="$TARGET/$rel"
  if [[ -e "$dst" ]]; then
    echo "  skip (已存在): $rel"; skipped=$((skipped+1))
  else
    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    echo "  copy: $rel"; copied=$((copied+1))
  fi
}

echo "agent-arch-kit → $TARGET"

# 1) 治理核心与模板
project ".specify/memory/constitution.md"
project ".specify/memory/adr/README.md"
project ".specify/memory/adr/_TEMPLATE.md"
project ".specify/memory/adr/EXAMPLE-adr-v2-dual-mode-routing.md"
project ".specify/memory/selection/README.md"
project ".specify/memory/design/README.md"
project ".specify/memory/design/_TEMPLATE.md"
project ".specify/memory/postmortem/README.md"
project ".specify/memory/postmortem/_TEMPLATE.md"
project ".claude/skills/selection-matrix/SKILL.md"
project ".claude/skills/eval-strategy/SKILL.md"
project ".claude/skills/retrospective/SKILL.md"
project "snippets/plan-template-selection-hook.snippet.md"
project "snippets/plan-template-test-strategy.snippet.md"

# 2) 选型矩阵 vendored 挂载(可选)
if [[ -n "$MATRIX_SOURCE" && -d "$MATRIX_SOURCE" ]]; then
  MATRIX_DST="$TARGET/.claude/skills/selection-matrix/matrix"
  if [[ -e "$MATRIX_DST" ]]; then
    echo "  skip (已存在): .claude/skills/selection-matrix/matrix/"
  else
    mkdir -p "$MATRIX_DST"
    cp -R "$MATRIX_SOURCE/." "$MATRIX_DST/"
    echo "  vendor: 选型矩阵 ← $MATRIX_SOURCE"
  fi
else
  echo "  note: 未设 MATRIX_SOURCE, 矩阵未挂载(referenced 模式或稍后手动 vendor, 见 selection/README.md)"
fi

# 3) 依赖与后续步骤提示
echo ""
echo "完成: $copied 个文件已投影, $skipped 个已存在跳过"
[[ -d "$TARGET/.specify/memory/nfr" ]] || \
  echo "⚠ 未检测到 .specify/memory/nfr/ — 请先安装 nfr-standard (constitution §3 依赖其 playbooks)"
echo ""
echo "下一步(手动):"
echo "  1. 把 snippets/ 下两个 plan 钩子合并进 .specify/templates/plan-template.md"
echo "     (顺序: Selection Check → Test Strategy → Constitution Check)"
echo "  2. 运行 /speckit.constitution 重新同步模板"
echo "  3. 确认 .gitignore 未忽略 .specify/ 与 .claude/, 然后提交"
