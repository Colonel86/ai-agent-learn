#!/usr/bin/env bash
# 一键跑完整条准确率提升阶梯。假设已 `pip install -e .`(或用项目 .venv)。
set -e
cd "$(dirname "$0")/.."
PY="${PY:-.venv/bin/python}"

echo "### 0. 重建数据资产(nba_roster.db + gold-test-set)"
$PY scripts/00_build_data.py
echo "### 1. SQL Agent + 幻觉诊断(L1/L2)"
$PY scripts/01_agent_demo.py
echo "### 2. baseline 评估(L3)"
$PY scripts/02_baseline_eval.py
echo "### 3. 生成微调数据(L5)"
$PY scripts/03_generate_data.py
echo "### 4. 真跑两种微调:标准 fine-tuning + memory tuning(L5 核心)"
$PY scripts/04_finetune.py both
echo "### 5. 三方对比(baseline vs finetune vs memory)"
$PY scripts/05_compare.py
echo "### 6. ASCII 曲线图"
$PY scripts/06_plot.py
echo "全部完成。结果见 data/results/comparison.md"
