# L09 对抗 AI 疲劳 + 第二个 Feature

> 原始字幕：`subtitles/L9-eng.vtt`

---

## 一、AI Fatigue 是真问题

Agent 一次生成大量代码 → 人 review 时**疲惫不堪**。这是 SDD 实践中的最大隐性成本。

---

## 二、抗疲劳的核心：feature 之间的"清场"

进入下一个 feature 前的 checklist：

- [ ] 还有未完成的工作吗？
- [ ] 上个 feature 分支已经 merge 到 main 了吗？
- [ ] roadmap 下一项还合理吗？
- [ ] Agent 的 context 清掉了吗（`/clear`）？

> Context 不清 → spec 不再是单一事实来源；Agent 凭"对话记忆"做事，spec 失去意义。

---

## 三、Feature 2 走全流程：Agents and Ailments

走的是 L05–L07 的同一个循环，再次强调几个细节：

### 3.1 Agent 会自然提问

- 这个 feature 范围是否合并？
- 数据库迁移用 SQL 原文还是 ORM 工具？
- validation 选哪几条？

你的回答**就是 spec 的核心来源**。

### 3.2 Review 时聚焦"业务级"问题

例：Agent 把 prop 类型写成 inline，你想要独立 type。
**这是 spec 没说清的疏漏，不是 Agent 的失败。**

> "An omission such as extracted prop types isn't a failure. You are evolving the spec as you discover new details."

**对策**：让 Agent 在整个项目里都改成独立 type，并把这个规则写进 spec。

### 3.3 Deep Review：派遣子 Agent

```text
Spawn several sub-agents to do a deep review of the entire project
with this feature change.
```

收益：
- 多 agent 视角 → 更容易抓住"独立 review 才能发现"的问题
- **保护主 agent 的 context window**——子 agent 跑 review 不占主线 context

> 这是 SDD 中"对抗 cognitive debt"的实用技巧。

---

## 四、应用 Skill

L08 写的 CHANGELOG skill 这里直接用上：

```text
Use the changelog skill to document this feature's changes.
```

Skill = SDD 节奏中**省脑力**的固化工具。

---

## 五、Replan 的轻量版

每个 feature 结束后**至少瞄一眼 roadmap**：下一个还对吗？需要重排吗？
不一定每次都改 Constitution——但**这个"瞄一眼"动作不能省**。

---

## 六、要点速记

- **AI 疲劳 = SDD 的最大隐性成本**，靠节奏管理对抗
- Feature 间 checklist 五条，**逐条问自己**
- Review 抓业务级、忽略低层（变量名等）
- 用 **sub-agent 做 deep review**，省主线 context
- 已有 Skill 主动用上，进一步省脑力
