# L03 Plan 模式 · 文件引用 · MCP Playwright

> 原始字幕：`subtitles/L3-eng.vtt`
> 实战目标：给 RAG Chatbot 加"可点击的引用链接" + "新建对话"按钮 + 新增后端工具

---

## 一、两个核心实践：精准引用文件 + Plan 模式

### 1.1 `@文件 / @文件夹` 引用

```text
> implement source citations in @frontend/script.js and @backend/api.py
```

- `@` 触发 tab 补全
- "Claude Code is only as good as the context you give it" —— 能直接给文件，就别让 Claude 自己猜。

### 1.2 Plan 模式（**关键**）

```text
shift + tab × 2     # 进入 Plan 模式
shift + tab × 1     # 进入 auto-accept edits
```

Plan 模式下：
- Claude **只读不写**，分析完后给出完整 plan
- 你审阅 → Approve / 让它改 plan / 直接拒绝
- 同意后才会真正动代码

> 适用：**任何稍微复杂的改动**。直接放 Claude 去改 → 经常发散；先 plan → 早期发现误解。

---

## 二、典型的"建特性"循环

```
@相关文件 → Plan 模式 → 审阅 plan → Auto-accept edits
→ Claude 写代码（边写边在 VS Code 可视化）
→ 浏览器测试 → 用截图/反馈继续迭代
```

### 用截图迭代视觉问题

```text
[paste screenshot]
> these links are hard to read. Make this more visually appealing.
```

- 直接粘截图给 Claude
- Claude 看图 → 定位前端代码 → 改样式

> 视觉问题靠"截图 + 自然语言"比写长 prompt 高效得多。

---

## 三、用 MCP Playwright 让 Claude 自己截图

手动截图毕竟麻烦。安装 Playwright MCP：

```bash
claude mcp add playwright npx @playwright/mcp@latest
```

进 Claude 后用 `/mcp` 验证连接。

之后 Claude 自己会：
- 用 Playwright 打开浏览器
- 导航到 localhost
- 截图
- 分析截图
- 改前端 → 再截图验证

> **架构意义**：把"视觉验证"从人类手动闭环升级为 Agent 自动闭环。前端开发的反馈循环大幅缩短。

---

## 四、其它实操技巧

### 4.1 换 feature 前先 `/clear`
避免上下文窗口被旧任务塞满，导致 Claude 被无关信息误导。

### 4.2 多行 prompt
反斜杠 `\` + Enter 换行；或在编辑器里写好 prompt 文件再粘进来。

### 4.3 用 `CLAUDE.md` 沉淀"反复说的话"
如果你每次都要告诉它"服务器我自己启"，写进 `CLAUDE.local.md`。

---

## 五、后端特性：新增工具

实战：在 RAG 系统加一个工具——按课程取每节课的详细 outline。

工作流和前端完全一样：
1. `@search_tools.py` `@rag_system.py` `@ai_generator.py`
2. Plan 模式描述需求
3. 审阅 plan（注意 plan 里有"更新系统 prompt"、"注册工具"等关键步骤）
4. Approve → Claude 实现 → 浏览器验证

---

## 六、架构师视角的几条心法

- **Plan 模式是"对齐意图"的硬抓手**。复杂改动不 plan 而直接动手，本质上是把验证成本拖到 PR 阶段。
- **MCP 是工具能力的扩展接口**——Playwright 是验证视觉的工具；之后还会用 Figma MCP 接设计、用 GitHub 集成接 PR。理解 MCP = 理解 Claude Code 的可扩展性。
- **HITL 是渐进的**：从"每次询问"→ "auto-accept edits" → "完全无人值守"，按对 Claude 的信任与任务风险动态调节。

---

## 七、要点速记

- `@文件` + Plan 模式 = 复杂改动的标准起手式。
- `shift+tab` 切换三档：Normal / Auto-accept / Plan。
- 视觉问题用截图（人手粘 or Playwright MCP 自动截）反馈最快。
- 换任务 → `/clear`；反复指令 → `CLAUDE.md`；中断走偏 → `Esc`。
