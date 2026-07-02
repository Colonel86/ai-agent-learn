# projects/ · 真实项目落地目录

> 本仓的**学习资产**(课程/笔记/决策包/skill)在 `agent/` 下;**真实项目**孵化在这里,每个项目一个子目录。
> 流程入口:`agent/skills/agent-selection/spec-kit-workflow.md`(全流程总纲),或调 `sdd-architect` skill 按阶段驱动。

## 约定

1. **一个项目一个目录**:`projects/<name>/`(如 `projects/argus/`)。
2. **用官方 Spec-Kit 初始化**,不手搓产物结构(`loop-engineering/` 沙盒是学机制用的例外):

   ```bash
   cd projects/<name>
   specify init . --ai claude    # 生成 .specify/ 与 specs/,后续用 /speckit.* 命令
   ```

3. **项目级 ADR** 放 `projects/<name>/docs/adr/`(用 `agent/skills/sdd/adr-writer` 生成);跨项目决策的 ADR 放 `agent/roadmap/adr/`。
4. **选型必留痕**:feature 级选型写进该 feature 的 `plan.md`「技术选型」小节;项目宪法用总纲 §三 的条款块起步。
5. 项目长大到需要独立仓时迁出(先例:`nfr-standard` → github.com/Colonel86/nfr-standard),此处留一个指针 README。

## 项目清单

| 项目 | 状态 | 说明 |
|---|---|---|
| argus(规划中) | 未初始化 | DeFi 分析系统,`loop-engineering/` 沙盒摸熟后的 `/spec-iterate` 迁移目标 |
