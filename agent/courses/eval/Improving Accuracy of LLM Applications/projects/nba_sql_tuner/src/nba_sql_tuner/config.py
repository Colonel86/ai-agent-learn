"""集中路径与后端配置。所有脚本从这里取路径,避免 cwd 依赖。"""
from __future__ import annotations

import os
from pathlib import Path

# 项目根 = 本文件上溯三级 (src/nba_sql_tuner/config.py -> 项目根)
ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
TRAINING_DATA = DATA / "training_data"
RESULTS = DATA / "results"
ADAPTERS = ROOT / "adapters"  # LoRA 权重落这里

DB_PATH = DATA / "nba_roster.db"
ROSTER_CSV = DATA / "nba_roster.csv"
GOLD_TEST_SET = DATA / "gold-test-set.jsonl"

for d in (DATA, TRAINING_DATA, RESULTS, ADAPTERS):
    d.mkdir(parents=True, exist_ok=True)

# ---- 后端 ----------------------------------------------------------------
# 课程用 Lamini 托管 Llama-3-8B-Instruct;本地换成能在 M 系列 Mac 上跑训练的小模型。
#
# 默认 SmolLM2-360M:本机 HF 缓存里唯一「权重完整」的生成模型(见 README「踩坑」)。
# 它是 base(非 instruct)模型,backend.py 会给它注入 ChatML 模板。作为 baseline 它较弱,
# 但这恰好放大了 memory tuning 的「把弱模型的既有事实背进权重」效果 —— 对比更直观。
#
# 网络允许时,强烈建议换成同属课程 Llama-3 谱系或更强的 instruct 小模型:
#   export BASE_MODEL="Qwen/Qwen2.5-0.5B-Instruct"        # 更强、自带 chat 模板
#   export BASE_MODEL="meta-llama/Llama-3.2-1B-Instruct"  # 与课程最贴近(gated,需登录)
DEFAULT_BASE_MODEL = os.environ.get("BASE_MODEL", "HuggingFaceTB/SmolLM2-360M")

# 生成数据/评判用的「教师」模型。默认与被评模型同一个(课程也是用 8B 自评自生成),
# 但可以指向更强的模型(如本地 Ollama 或云 API)以提高合成数据质量。
TEACHER_MODEL = os.environ.get("TEACHER_MODEL", DEFAULT_BASE_MODEL)


def device() -> str:
    """推理/评估用的设备。这些都是短任务,MPS 很稳。"""
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


# 训练默认走 CPU!在 Apple Silicon 上,长时间重载的 LoRA 训练跑 MPS(float32)会触发
# GPU 命令缓冲错误(kIOGPUCommandBufferCallbackErrorSubmissionsIgnored),严重时把整机
# 拖到内核 panic → 重启(踩坑记录里有)。CPU 慢一些但绝对稳,不碰那个会崩的 GPU 路径。
# 有 CUDA 的机器可以 `export TRAIN_DEVICE=cuda`;确实想用 MPS 冒险 `export TRAIN_DEVICE=mps`。
def train_device() -> str:
    import torch

    env = os.environ.get("TRAIN_DEVICE")
    if env:
        return env
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"
