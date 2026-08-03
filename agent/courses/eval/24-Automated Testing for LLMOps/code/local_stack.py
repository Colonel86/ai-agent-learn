"""本地化适配层：DeepSeek 兼容 API + 本地 pytest 模拟 CircleCI 评估流水线。

课程原版: gpt-3.5-turbo + langchain 0.0.326, 评估跑在 CircleCI 云端
(push 到课程方 GitHub repo -> 触发 pipeline, 依赖课程托管的 CIRCLE_TOKEN/GH_TOKEN)。
本地化:
- 模型: DeepSeek (langchain-openai 1.x 的 ChatOpenAI + base_url)
- CI: 本地 pytest 直接跑同一批评估, 按课程的 eval-mode 概念分组
  (commit=快的规则/单点评估, release=模型评分, full=全量+报告)
- CircleCI 配置文件原样保留, L5 做本地解析讲解
"""

import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

_CODE_DIR = Path(__file__).resolve().parent
load_dotenv(_CODE_DIR / ".env")

MODEL = os.getenv("MODEL", "deepseek-v4-flash")
DEEPSEEK_API_KEY = os.environ["DEEPSEEK_API_KEY"]
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")


def make_llm(temperature: float = 0):
    """DeepSeek 版 ChatOpenAI。thinking disabled: v4-flash 默认开 thinking,
    评估类 demo 需要确定性输出。"""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=MODEL,
        temperature=temperature,
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        extra_body={"thinking": {"type": "disabled"}},
    )


def banner(step: str, title: str):
    line = "=" * 64
    print(f"\n{line}\n{step} {title}\n{line}")


def run_pytest(test_target: str, label: str, expect_fail: bool = False) -> bool:
    """本地模拟一个 CI job: 对指定测试文件跑 pytest, 打印结果。

    expect_fail=True 用于课程的「演示 CI 抓住坏用例」环节。
    """
    print(f"\n>>> [CI 模拟] job: {label} -> pytest {test_target}")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", test_target, "-v", "--no-header", "-rN"],
        capture_output=True,
        text=True,
    )
    tail = "\n".join(result.stdout.strip().splitlines()[-15:])
    print(tail)
    passed = result.returncode == 0
    if expect_fail:
        print(f"    [预期失败{'√ 确实失败了 - CI 门禁生效' if not passed else '×! 竟然通过了'}]")
    else:
        print(f"    [job {'通过 ✅' if passed else '失败 ❌'}]")
    return passed
