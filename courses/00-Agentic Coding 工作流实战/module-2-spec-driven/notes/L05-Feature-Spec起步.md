# L05 Feature Spec：单个功能的规范

> 原始字幕：`subtitles/L5-eng.vtt`
> 实战：AgentClinic 第一个 feature —— "Hello Hono"

---

## 一、Feature 循环的起点：planning

**先别写代码。** Roadmap 上拿到一个 feature 后：

1. 切到**新分支**（如 `feature/hello-hono`）
2. 清掉 Agent context（`/clear`）—— 让它从 Constitution 重新加载
3. 用 prompt 启动 feature spec 对话

---

## 二、Feature Spec 三件套

每个 feature 都产出三个文件（放在 `specs/<feature-name>/`）：

| 文件 | 内容 |
|---|---|
| `plan.md` | 任务分组（task groups）、执行顺序 |
| `requirements.md` | 技术需求、约束（如 Hono 版本固定、strict TypeScript） |
| `validation.md` | 验证方式（如手动 curl、单元测试） |

这种三件套对应了：**做什么 → 怎么验** 的闭环。

---

## 三、典型起步 Prompt

```text
We're starting the first feature from @specs/roadmap.md.
We're on branch feature/hello-hono.

Please work with me to draft:
- specs/hello-hono/plan.md
- specs/hello-hono/requirements.md
- specs/hello-hono/validation.md

Use AskUserQuestion to clarify.
```

Agent 会针对：
- 范围确认（"phase 1 scope 完全按 roadmap 写的来吗？"）
- 关键约束（"Hono 版本固定？严格 TS？"）
- 验证方式（"手动 curl 还是自动测试？"）

---

## 四、Human-in-the-loop：审 Feature Spec

> "Don't speed through this, but don't state minor technical details like variable names here."

审三件套时关注：
- **plan**：步骤合理吗？少了/多了？
- **requirements**：技术约束写到了吗？（不要写变量名级别的细节）
- **validation**：Agent 能自己跑这套验证吗？

发现问题 → **让 Agent 改三个文件**，保持同步。

例：feature spec 写得太精简，**没要求一个像样的首页占位**——告诉 Agent 改 plan，连带 requirements 和 validation 也得更新。

---

## 五、关键观念

> "The changes you make here in the specs will expand downstream into hundreds of lines of code. So time spent here is well spent."

在 spec 阶段多花 10 分钟，比在 review code 时改 10 处都划算。

---

## 六、提交

Spec 三件套确认完 → **先 commit spec**，再进入 implementation。这一步保证 spec 和 code 的对应关系在 git 里清晰可追溯。
