# L12 自动化工作流：Skills / Plugins / Spec Kit / MCP 取舍

> 原始字幕：`subtitles/L12-eng.vtt`

---

## 一、用 Skill 把重复 prompt 固化

每次起 feature spec 都输入几乎一样的 prompt——是该写 Skill 了。

让 Agent **帮你写 Skill**：

```text
Use your skill creator to help me write a "feature spec" skill.
```

> 社区已经有大量"skill of skills"——别从零写，先搜一遍。

---

## 二、Skill 的三种触发方式

| 方式 | 何时用 |
|---|---|
| Prompt 自然语言里**暗示**任务 | Agent 自己判断要不要调（progressive disclosure） |
| Prompt 里**直接命名 skill** | 明确知道要用时，省 token、省 thinking |
| **Skill 调用另一个 skill** | 复合工作流，比如 spec → implementation skill chain |

> Heuristic：和 `@file` 标记同理——**知道要用就直接说**，别让 Agent 猜。

---

## 三、`/commands` vs Skills

Agent 都有内置 `/clear` 之类的 commands。
**趋势**：很多 Agent 正在把自定义 `/commands` 迁移到 Skills。

原因：Skills 更结构化、可携带资源、跨 Agent 标准化（详见 L13）。

---

## 四、MCP vs CLI + Skills

### 4.1 MCP 是什么

> "Until now the universal way to extend an agent has been MCP, Model Context Protocol."

例：Context7 = MCP server，提供最新版包的文档（避免 LLM 用过期 API）。

### 4.2 趋势：MCP 正被 "CLI + Skill" 替代

理由：
- **MCP server 要起进程、要安装、要持续吃 context**
- **CLI 工具**：调用时才执行、无常驻进程、context 消耗低
- Skill 配套 CLI 调用，做的事**和 MCP server 一样**，但更轻

Context7 现在已经推荐 **"Skill + CLI"** 而不是 MCP server。

### 4.3 何时还用 MCP

- 长生命周期 / 需要持续连接的服务（如交互式数据库）
- 已有成熟 MCP 实现且无 CLI 替代

---

## 五、共享和分发：Plugins

把你的 Skill / config 打包：
- 自己跨机器同步
- 团队共享
- 公开发布

> Claude Code 等 Agent 已有 plugin 体系；**Plugin 还不是跨 Agent 标准**（L13 会展望）。

⚠️ 安全：Plugin 能跑代码，安装/更新前**审一遍**——和 npm package 一样的心态。

---

## 六、现成的 SDD 框架

| 工具 | 提供的 / commands |
|---|---|
| **GitHub Spec Kit** | `/specify`、`/plan`、`/tasks`、`/implement` |
| **OpenSpec**（Fission AI） | propose / explore / apply / archive |

两者都附带：
- 分支管理
- 验证脚本
- 有主张的 spec 文档格式

> 不必从零搭——拿一个现成框架试一周，再按自己习惯定制。

---

## 七、Backlog 模式：保存"想法但不进 roadmap"

Feature 做着做着冒出一个新想法（如换数据库）。**别中断 feature**，但也别忘掉。

```text
We had this idea: [...]. Write a research report to specs/backlog/<topic>.md.
Don't put it on the roadmap yet.
```

之后可写一个 Skill 自动把 backlog 整理排进 roadmap。

---

## 八、要点速记

- Skill 是**重复 prompt 的容器**——重复两次就该写
- 趋势：`/commands` → Skills；MCP server → CLI + Skill
- Spec Kit / OpenSpec 是现成的 SDD 框架，直接拿来改
- 想法 → backlog 文件，不打断 feature 节奏
