# L08 Replan：feature 间反思 + Skills 入门

> 原始字幕：`subtitles/L8-eng.vtt`

---

## 一、口号

> **You have to run slow to run fast.**

完成一个 feature 后**别冲下一个**。停下来做 replanning：
- 修订 Constitution
- 调整 Roadmap
- 改进工作流本身

---

## 二、Replan 的三类典型工作

### 2.1 补 Constitution 的漏洞

例：第一个 feature 没用上测试——因为 tech-stack 里没写测试策略。

```text
Update tech-stack.md to add our testing policy: [details].
Then update existing feature specs & code accordingly.
```

**用独立分支** `replanning/...` 提交。Constitution 是活文档，独立分支让"哪版 constitution 产生哪些 code"可追溯。

### 2.2 接受需求变更

例：PM 说"40% 用户在移动端"——要响应式。

```text
We need to emphasize responsive design.
Update product spec, feature specs, and existing code.
```

判断："小改"直接在 replan 里做；"大改" → 当成新 feature 进 roadmap。

### 2.3 调整 Roadmap

看后续 feature 还合理吗？比如发现 feature 2/3/4/5 内在耦合 → 合并成一阶段做。

---

## 三、Skills：把重复流程自动化

### 3.1 什么是 Skill

> "A package of instructions and resources providing the agent new capabilities and expertise."

适合**可定义、可重复、需要项目/组织特定 context 的工作流**。

### 3.2 用 Agent 写 Skill

```text
I want a skill that updates a CHANGELOG.md on each merge to main.
Use your skill creator to talk me through it.
```

Agent 会问你：
- Skill 是 per-project 还是 global？
- 触发时机？
- 输出格式？

### 3.3 SDD 中典型可 Skill 化的环节

- **Validation 流程**：lint + format + 测试 + readme 更新
- **Feature spec 起步**：每次都重复"创建分支 + 三件套 + commit"
- **Replan 起步**：固定的检查清单

> 每当你发现自己**第二次输入几乎一样的 prompt**，就是该写 Skill 了。

---

## 四、Skill 的归属判断

写 Skill 时灵魂拷问：
- **这个 Skill 只属于这个项目？** → per-project（仓库内）
- **它该是所有项目的标配？** → global（用户级）

例：CHANGELOG 这种通用工程实践 → global；和 AgentClinic 业务相关的 → per-project。

---

## 五、要点速记

- **Replan 是 feature 之间的反思节奏**，不要跳过
- Constitution 改动**用独立分支**，便于追溯
- "小改在 replan 里做，大改进 roadmap"——判断成本/收益
- 重复的 prompt → 写成 Skill，per-project vs global 看场景
- 你的工作正从"实施"转向"规划 + 验证"——给 replan 留时间
