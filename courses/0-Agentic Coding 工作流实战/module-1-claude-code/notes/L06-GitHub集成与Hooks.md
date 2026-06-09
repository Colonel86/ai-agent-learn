# L06 GitHub 集成 + Hooks

> 原始字幕：`subtitles/L6-eng.vtt`
> 把 Claude 从终端扩展到 PR / Issue，并通过 hooks 在工具调用周期里注入自定义逻辑

---

## 一、GitHub 集成：让 Claude 在 PR/Issue 里工作

### 1.1 安装

```text
/install-github-app
```

按提示在浏览器授权安装 Anthropic 提供的 GitHub App，可选择仓库范围。

底层基于 **Claude Code SDK**——即"Claude Code 不只是 CLI，也是个 SDK，可以跑在 GitHub Actions 等其他环境里"。

### 1.2 安装后得到什么

两个 GitHub Actions workflow（`.github/workflows/*.yml`）：

| Workflow | 触发 | 作用 |
|---|---|---|
| **Claude in issues/PRs** | 在 issue/PR 里 `@claude` | 让 Claude 修 bug、写测试、改代码 |
| **Auto code review** | PR 创建/更新 | 自动 review 代码 |

两个 YAML 都是 Git 跟踪的——**可以编辑 prompt** 来定制 review 风格、过滤作者、改触发条件。

### 1.3 三种典型用法

#### A. 自动 PR Review
PR 一开，Claude 自动读、分析、点评——找漏洞、性能问题、风格不一致。

> 即使 Claude 自己写的代码，也由另一个 Claude review——"另一双眼睛"原则。

#### B. Issue 里 `@claude` 让它修
新建 issue 描述问题（如"去掉这个 header"），评论 `@claude can you fix this?`
→ Claude 启动 Action → 分析 + 改代码 + 开一个 PR

#### C. PR 里 `@claude` 让它改
在 review 评论里直接 `@claude please address this` → 推新 commit。

---

## 二、Hooks：在工具调用周期注入代码

### 2.1 什么是 hooks

类比传统软件的 hook：在 Agent 操作的特定**生命周期事件**触发一段你写的 shell 命令。

可挂的事件：

| 事件 | 触发时机 |
|---|---|
| `PreToolUse` | 工具执行**前**（可阻止执行） |
| `PostToolUse` | 工具执行**后** |
| `Notification` | 系统通知时 |
| `UserPromptSubmit` | 用户提交 prompt 时 |
| `Stop` | 流程停止时 |
| `SubagentStop` | 子 Agent 完成时 |

### 2.2 配置入口

```text
/hooks
```

或直接编辑 `.claude/settings.local.json`：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Read|Grep",
        "command": "say 'All done!'"
      }
    ]
  }
}
```

`matcher` 用工具名（支持正则/或）—— 留空 = 匹配所有工具。

### 2.3 真实用途（不只是 say 'All done'）

- **PreToolUse 阻断**：禁止 Bash 跑 `rm -rf`、禁止往 prod 写
- **PostToolUse 自动化**：写文件后自动 format、跑相关测试、跑 lint
- **UserPromptSubmit**：日志记录、敏感词过滤、自动补 context
- **Stop**：发通知 / 触发 CI / 同步 status

### 2.4 安全警告

`hooks` 会**执行任意 shell**，你写错或被人改了 settings 文件就有风险。审 settings 文件像审代码一样审。

---

## 三、架构师视角

- **GitHub 集成 = Claude Code SDK 的具象产品形态**。理解这点比记 workflow 配置更重要——它意味着你也可以把 Claude Code 嵌进自己的 CI、IDE、内部工具。
- **Hooks = 在 Agent 决策环里插钩子**。它把"用户对 Agent 行为的约束"从 prompt 工程（软约束）升级为代码护栏（硬约束）。安全/合规场景必备。
- **两层 Claude（写代码 + Review 代码）** 是一个轻量但有效的可靠性模式——不止于 Claude，任何 Agent 体系都可以用。

---

## 四、要点速记

- `/install-github-app` 一键把 Claude 接进 GitHub PR/Issue 循环。
- 自动 code review + `@claude` 修 issue/PR 是两个高 ROI 默认用法。
- Hooks 在工具调用生命周期注入 shell——PreToolUse 是硬约束，PostToolUse 是自动化。
- Hooks 跑任意 shell → 审 `settings.local.json` 像审代码。
- "另一个 Claude review Claude 写的代码"是简单可靠的二次校验。
