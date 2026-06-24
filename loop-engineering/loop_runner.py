#!/usr/bin/env python3
"""Loop Engineering 运行器 —— 用 Claude Agent SDK 把循环写成一个真程序。

确定性控制流（取任务 / 跑门控 / 验收 / 停点 / 记账 / commit）都在 Python 里；
每个任务调两次 agent：
  · 实现者 implement()：可读写 + 跑 bash，bypassPermissions 自主干活
  · 验收者 verify()：全新上下文、只读工具，独立判 PASS/FAIL（实现者不准自评）
这就是 Boris Cherny 说的“我写循环，循环来提示 Claude”。

前提：
  ../.venv/bin/python -m pip install claude-agent-sdk
  export ANTHROPIC_API_KEY=sk-ant-...
  （SDK 在底层驱动 Claude Code 运行时；你本机已装 Claude Code）

跑法：
  ../.venv/bin/python loop_runner.py
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    query,
)

SANDBOX = Path(__file__).resolve().parent
FEATURE = SANDBOX / "specs" / "001-note-lint"
TASKS = FEATURE / "tasks.md"
STATE = SANDBOX / "loop-state.json"
MODEL = "claude-opus-4-8"
MAX_FIX_RETRIES = 2

# - [ ] T1 实现 `count_words(...)`（AC1）｜验收: `pytest -k test_count_words`
TASK_RE = re.compile(
    r"^- \[(?P<mark>[ x!])\] (?P<id>T\d+) (?P<desc>.+?)"
    r"(?:｜验收: `(?P<test>[^`]+)`)?$"
)


def read_tasks() -> list[dict]:
    tasks = []
    for line in TASKS.read_text(encoding="utf-8").splitlines():
        m = TASK_RE.match(line.strip())
        if m:
            tasks.append(m.groupdict())
    return tasks


def set_mark(task_id: str, mark: str) -> None:
    out = []
    for line in TASKS.read_text(encoding="utf-8").splitlines():
        m = TASK_RE.match(line.strip())
        if m and m.group("id") == task_id:
            line = re.sub(r"^- \[[ x!]\]", f"- [{mark}]", line, count=1)
        out.append(line)
    TASKS.write_text("\n".join(out) + "\n", encoding="utf-8")


def bump_state(**deltas: int) -> dict:
    s = json.loads(STATE.read_text(encoding="utf-8"))
    for k, v in deltas.items():
        s[k] = s.get(k, 0) + v
    STATE.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return s


def run_gate() -> tuple[int, str]:
    p = subprocess.run(["bash", str(SANDBOX / "gate.sh")], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def git_commit(msg: str) -> None:
    subprocess.run(["git", "add", "-A", "."], cwd=SANDBOX, check=False)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=SANDBOX, check=False)


async def run_agent(prompt: str, *, allowed_tools, permission_mode, disallowed_tools=None):
    """跑一个 agent，返回 (最终文本, 花费USD)。每次调用都是全新上下文。"""
    text, cost = "", 0.0
    async for msg in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=allowed_tools,
            disallowed_tools=disallowed_tools or [],
            permission_mode=permission_mode,
            model=MODEL,
            cwd=str(SANDBOX),
            setting_sources=[],   # 不加载项目 CLAUDE.md / settings，保持沙盒隔离
            max_turns=30,
        ),
    ):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                t = getattr(block, "text", None)
                if isinstance(t, str):
                    text += t
        elif isinstance(msg, ResultMessage):
            cost = getattr(msg, "total_cost_usd", None) or 0.0
            if getattr(msg, "result", None):
                text = msg.result
    return text, cost


async def implement(task: dict):
    prompt = (
        f"在 notelint.py 里实现 {task['id']}：{task['desc']}。\n"
        f"把对应函数的 NotImplementedError 替换成真实实现。"
        f"只动这一个函数，不要改其它函数或文件。\n"
        f"改完跑 `bash gate.sh` 确认代码没坏。"
    )
    return await run_agent(
        prompt,
        allowed_tools=["Read", "Edit", "Write", "Bash"],
        permission_mode="bypassPermissions",
    )


async def verify(task: dict):
    """独立验收 agent：全新上下文 + 只读工具，实现者不参与打分。"""
    prompt = (
        f"你是独立验收员，不写代码。任务 {task['id']}：{task['desc']}。\n"
        f"用 `../.venv/bin/python -m {task['test']}` 跑这个任务的验收测试。\n"
        f"只看这一个测试是否变绿；其它任务的测试红是正常的。\n"
        f"最后一行只输出 `VERDICT: PASS` 或 `VERDICT: FAIL: <原因>`。"
    )
    text, cost = await run_agent(
        prompt,
        allowed_tools=["Read", "Bash", "Glob", "Grep"],
        permission_mode="bypassPermissions",
        disallowed_tools=["Write", "Edit"],   # 验收者不准改文件
    )
    return ("VERDICT: PASS" in text), text, cost


async def main() -> None:
    total = 0.0
    while True:
        task = next((t for t in read_tasks() if t["mark"] == " "), None)
        if task is None:
            print("✅ LOOP_DONE —— 所有任务已处理")
            break
        tid = task["id"]
        print(f"\n=== {tid}: {task['desc']} ===")

        # 1) 实现
        _, c = await implement(task); total += c

        # 2) 硬门控（确定性，Python 跑）
        code, out = run_gate()
        attempt = 1
        while code != 0 and attempt <= MAX_FIX_RETRIES:
            print(f"  ⚠ 硬门控失败，让 agent 修复（{attempt}/{MAX_FIX_RETRIES}）")
            _, c = await run_agent(
                f"`bash gate.sh` 失败，输出：\n{out[-1500:]}\n修好它，只动 {tid} 相关代码。",
                allowed_tools=["Read", "Edit", "Write", "Bash"],
                permission_mode="bypassPermissions",
            )
            total += c
            code, out = run_gate(); attempt += 1
        if code != 0:
            set_mark(tid, "!"); bump_state(attempted=1, blocked=1)
            print(f"  ✗ {tid} 阻塞：硬门控始终失败"); continue

        # 3) 独立验收
        passed, verdict, c = await verify(task); total += c

        # 4) 落状态 + 记账
        if passed:
            set_mark(tid, "x")
            git_commit(f"feat(note-lint): {tid} {task['desc']}")
            s = bump_state(attempted=1, accepted=1, commits=1)
            print(f"  ✓ {tid} 通过并提交")
        else:
            set_mark(tid, "!")
            s = bump_state(attempted=1, blocked=1)
            tail = verdict.strip().splitlines()[-1] if verdict.strip() else "?"
            print(f"  ✗ {tid} 验收未过：{tail}")

        # 5) 停点：唯一指标 = 接受率
        rate = s["accepted"] / max(s["attempted"], 1)
        print(f"  累计 ${total:.3f}｜接受率 {rate:.0%}")
        if s["attempted"] >= 4 and rate < 0.5:
            print("🛑 LOOP_STOP —— 接受率过低，需人工介入"); break

    print(f"\n总花费 ${total:.3f}")


if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("请先 export ANTHROPIC_API_KEY=sk-ant-...")
    asyncio.run(main())
