#!/usr/bin/env python3
"""1-3-7-21 复习清单生成器。

用法（每天跑一次，或学完新课后跑）:
    python3 agent/review/update.py

原理:
- 每篇笔记的"学习日期" = 该文件在 git 里首次出现的提交日期
- 近 21 天的笔记按「课程 × 学习日」聚合为一个 session，排 +1/+3/+7/+21 四次自测
- 21 天前的存量课程：每门课排一次「一页纸重建」巩固复习，每周 3 门
- 复习完成 = 在 复习清单.md 里勾选 checkbox；下次运行时自动归档进 state.json
"""

import json
import re
import subprocess
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REVIEW_DIR = Path(__file__).resolve().parent
STATE_FILE = REVIEW_DIR / "state.json"
LIST_FILE = REVIEW_DIR / "复习清单.md"
NOTES_GLOB = "agent/courses"

INTERVALS = [1, 3, 7, 21]
BACKLOG_WEEKDAYS = [0, 2, 4]  # 存量巩固排在周一/三/五,每天 1 门
BULK_THRESHOLD = 20           # 单日新增笔记超过此数视为"批量整理日",不算真实学习 session


def note_learn_dates():
    """返回 {note_path: 学习日期}。

    学习日期 = 文件首次以 A(新增)出现在 git 的日期；
    之后的 R(重命名/移动)沿链传递该日期，D(删除)剔除。
    """
    out = subprocess.run(
        ["git", "-c", "core.quotepath=false", "log", "--reverse", "--date=short",
         "--format=@%ad", "--name-status", "--", NOTES_GLOB],
        cwd=REPO, capture_output=True, text=True, check=True,
    ).stdout
    dates, cur = {}, None
    for line in out.splitlines():
        if line.startswith("@"):
            cur = date.fromisoformat(line[1:])
            continue
        parts = line.split("\t")
        status = parts[0][:1]
        if status == "A":
            dates.setdefault(parts[1], cur)
        elif status in ("R", "C") and len(parts) == 3:
            dates[parts[2]] = dates.pop(parts[1], cur) if status == "R" else dates.get(parts[1], cur)
        elif status == "D":
            dates.pop(parts[1], None)
    return {
        p: d for p, d in dates.items()
        if "/notes/" in p and p.endswith(".md") and (REPO / p).exists()
    }


def course_of(path):
    """agent/courses/<分类>/<课程名>/notes/xxx.md -> 课程名"""
    return path.split("/notes/")[0].split("/")[-1]


def load_state():
    if STATE_FILE.exists():
        return set(json.loads(STATE_FILE.read_text())["done"])
    return set()


def harvest_checked(done):
    """把清单里已勾选的项归档进 state。"""
    if not LIST_FILE.exists():
        return done
    for m in re.finditer(r"- \[[xX]\].*?<!--id:(.*?)-->", LIST_FILE.read_text()):
        done.add(m.group(1))
    return done


def build_items(dates, done, today):
    items = []      # (due_date, id, label)
    auto_done = set()  # 被更晚复习取代的逾期项,自动归档
    day_totals = Counter(dates.values())

    # --- 真实学习 session(近 21 天、非批量整理日):+1/+3/+7/+21 ---
    sessions = defaultdict(list)
    for p, d in dates.items():
        if (today - d).days <= 21 and day_totals[d] <= BULK_THRESHOLD:
            sessions[(course_of(p), d)].append(p)
    for (course, d), paths in sessions.items():
        lessons = "、".join(sorted(Path(p).stem.split("-")[0] for p in paths))
        pending = [n for n in INTERVALS if f"s|{course}|{d}|{n}" not in done]
        overdue = [n for n in pending if d + timedelta(days=n) <= today]
        # 多次逾期只补做最晚一次,更早的自动归档
        for n in overdue[:-1]:
            auto_done.add(f"s|{course}|{d}|{n}")
        for n in overdue[-1:] + [n for n in pending if n not in overdue]:
            due = d + timedelta(days=n)
            if due > today + timedelta(days=14):
                continue
            items.append((due, f"s|{course}|{d}|{n}",
                          f"D+{n} 自测:《{course}》{lessons}(学于 {d})"))

    # --- 存量课程:一页纸重建,周一/三/五各 1 门 ---
    recent = {c for (c, _) in sessions}
    backlog_courses = {}
    for p, d in dates.items():
        c = course_of(p)
        if c not in recent:
            backlog_courses[c] = max(d, backlog_courses.get(c, d))
    pending = sorted(
        (c for c in backlog_courses if f"c|{c}" not in done),
        key=lambda c: backlog_courses[c], reverse=True,  # 最近学的先复习
    )
    slot = today
    for c in pending:
        while slot.weekday() not in BACKLOG_WEEKDAYS:
            slot += timedelta(days=1)
        items.append((slot, f"c|{c}", f"一页纸重建:《{c}》(最后学于 {backlog_courses[c]})"))
        slot += timedelta(days=1)

    return sorted(items), auto_done


def render(items, today):
    due_now = [(d, i, l) for d, i, l in items if d <= today]
    week = [(d, i, l) for d, i, l in items if today < d <= today + timedelta(days=7)]
    later = [(d, i, l) for d, i, l in items if d > today + timedelta(days=7)]

    lines = [
        "# 1-3-7-21 复习清单",
        "",
        f"> 生成于 {today} · 每天运行 `python3 agent/review/update.py` 刷新",
        "> ",
        "> **自测** = 合上笔记，口头回答要点/画出架构，再翻笔记核对漏了什么",
        "> **一页纸重建** = 不看笔记，凭记忆写 10 行要点 + mermaid 图，再对照原笔记补漏",
        "> 完成后勾选 checkbox，下次运行自动归档。",
        "",
        f"## 今日到期({len(due_now)})",
        "",
    ]
    for d, iid, label in due_now:
        tag = f"⚠️逾期{(today - d).days}天 " if d < today else ""
        lines.append(f"- [ ] {tag}{label} <!--id:{iid}-->")
    lines += ["", f"## 未来 7 天({len(week)})", ""]
    for d, iid, label in week:
        lines.append(f"- [ ] {d} · {label} <!--id:{iid}-->")
    lines += ["", f"## 更远排期({len(later)} 项，仅示前 10)", ""]
    for d, iid, label in later[:10]:
        lines.append(f"- [ ] {d} · {label} <!--id:{iid}-->")
    lines.append("")
    return "\n".join(lines)


def main():
    today = date.today()
    done = harvest_checked(load_state())
    dates = note_learn_dates()
    items, auto_done = build_items(dates, done, today)
    done |= auto_done
    STATE_FILE.write_text(json.dumps({"done": sorted(done)}, ensure_ascii=False, indent=1))
    LIST_FILE.write_text(render(items, today))
    due = sum(1 for d, *_ in items if d <= today)
    print(f"✅ 已更新 {LIST_FILE.relative_to(REPO)}:今日到期 {due} 项,总排期 {len(items)} 项,已归档 {len(done)} 项")


if __name__ == "__main__":
    main()
