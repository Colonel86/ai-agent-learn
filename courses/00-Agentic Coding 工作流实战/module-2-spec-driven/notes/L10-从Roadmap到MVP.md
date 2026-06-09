# L10 从 Roadmap 一次性冲到 MVP

> 原始字幕：`subtitles/L10-eng.vtt`

---

## 一、何时一次实施一大批 feature

平时建议**一次一个 feature**。但有时管理层要 MVP，需要短期内实施 roadmap 后半段。

**前提条件**（缺一不可）：
1. Constitution 质量足够高
2. 已完成的 feature spec 质量足够高（说明你的写法稳定了）
3. 你能 hold 住后续 review + validation 的工作量

> 把 MVP 视作**对 Constitution + 已有 spec 的极限压力测试**——如果产出和预期不一致，说明 spec 还有漏洞，要回头 replan。

---

## 二、做法：复用 feature spec prompt，扩到全 roadmap

```text
Implement the rest of the roadmap.
Refer to existing feature specs as the reference style.
Use AskUserQuestion for any unclear points.
```

Agent 会：
- 问几个关键决策
- 写 spec 文件
- 大批量实现

中间穿插：
- 审 plan / requirements / validation
- 小步 commit

---

## 三、MVP 完成后的验证

不是逐行 review code（量太大），而是：

```text
Validate the implementation against all feature specs.
```

让 Agent 自检：MVP 暴露了 spec 里的哪些漏洞？

> 把 Agent 的自检结果带去和 stakeholder 评审——**这就是 MVP 的真正价值：找 spec 漏洞**。

---

## 四、判断分支去留

- MVP 反馈不错 → merge
- 发现 spec 重大漏洞 → archive 该分支，回到 replanning

---

## 五、要点速记

- "一次冲完 roadmap"是**例外，不是默认**
- 用 MVP 压测 spec 质量；预期不符 = spec 有洞
- 验证 MVP 的方式是**让 Agent 对照 spec 自检**，而非人逐行 review
- 决策点：merge 还是 archive，看 spec 漏洞大小
