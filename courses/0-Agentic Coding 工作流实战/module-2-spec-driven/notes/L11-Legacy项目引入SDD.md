# L11 把 SDD 引入遗留（Brownfield）项目

> 原始字幕：`subtitles/L11-eng.vtt`

---

## 一、反对一个常见偏见

> "People say SDD and even AI are only good for greenfield projects."

实际上 SDD 在遗留项目上**同样有效**——甚至更需要，因为 legacy 项目最容易漂移。

---

## 二、起点：从现有代码反推 Constitution

Legacy 项目的"输入"：
- `README.md`
- `TODO.md` / issue tracker / Word / 表格
- Git 历史
- 现有代码本身

Prompt：

```text
Generate the project Constitution from the existing codebase.
- Discover mission from @README.md
- Discover roadmap items from @TODO.md
- Reverse-engineer the tech stack from the codebase
```

Agent 大量 tool calls 扫代码 → 产出 `mission.md` / `tech-stack.md` / `roadmap.md`。

---

## 三、Constitution 在 Legacy 项目里的作用

- **对齐未来变更**：让 Agent 后续改动符合"既有代码已经做出的隐式决策"
- **沉淀隐性知识**：之前在前同事脑子里、Slack 记录里的决策，落到文档

> "The agent will discover and **reverse engineer** the SDD artifacts from the existing code base."

---

## 四、之后流程完全不变

从 Constitution 那一刻起，工作流和 greenfield 一模一样：

1. 取 roadmap 上的下一个 feature
2. 切分支
3. 写 feature spec（plan / requirements / validation）
4. Implement
5. Verify
6. Merge
7. Replan

---

## 五、Legacy 引入 SDD 后的特别动作

引入后**第一个 replan 阶段会特别长**。原因：
- 反推出来的 Constitution 不可能一次准确
- 真跑一遍 feature 才暴露漏洞
- 给团队磨合 SDD 工作流也需要时间

> 这段时间不省钱，但**这是 legacy 项目从"漂移积压"翻身的关键投资**。

---

## 六、要点速记

- SDD ≠ 只对新项目有用，**legacy 项目同样适用**
- Constitution 从现有 artifacts **反推**（README、TODO、commit、代码）
- 反推后流程与 greenfield 完全一致
- 引入后第一轮 replan 要慷慨给时间
