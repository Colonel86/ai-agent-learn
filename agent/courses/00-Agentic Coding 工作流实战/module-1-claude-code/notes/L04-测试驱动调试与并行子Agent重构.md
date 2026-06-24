# L04 测试驱动的调试 + 思考模式 + 并行子 Agent 重构

> 原始字幕：`subtitles/L4-eng.vtt`
> 实战：RAG Chatbot 报错时，**先写测试 → 找 root cause → 修复 → 重构成多轮工具调用**

---

## 一、反直觉的调试方法：不要立刻让 Claude 修

错误来了，**最容易踩的坑**：

```text
× [复制错误 + 截图] → "fix this for me"
```

→ Claude 经常带你"猜方向"，最后绕一大圈。

**正确做法**：

```text
1. 不要急着修
2. 让 Claude 给指定文件先写测试
3. 让 Claude 运行测试，定位根因
4. 再修
```

> **架构师视角**：调试本质是"建立可重复验证的失败现场"。先有测试，bug 就从一次性事故变成可以反复触发的信号；这一步做完，修不修都是次要的。

---

## 二、Extended Thinking（思考模式）

```text
> ... think hard about ...
```

触发词（"think"、"think hard"、"think harder"、"ultrathink"）→ 分配更多 thinking tokens。

适用：架构判断、debug 根因分析、设计取舍——任何"答案不容易直接写出来"的任务。

可以**和 Plan 模式叠加**：thinking + plan = 复杂任务的最高质量起手。

---

## 三、典型 debug 流程示范

```text
shift+tab×2  (Plan)
> Think hard about why we're getting this error.
  Write tests for @ai_generator.py @rag_system.py @search_tools.py
  using pytest. Mock ChromaDB where needed.
  Then run them, find the root cause, and propose a fix.
```

Claude 干的事：

1. 读三个文件 + 关联文件 → 推断"可能的失败点"
2. 列 plan：建 `tests/`、加 pytest 依赖（UV）、写单测+集成测、跑测试
  1. 通过测试发现 `MAX_RESULTS = 0` —— 配置 bug！
3. 改配置 → 测试绿 → 浏览器验证

收益：

- 修了 bug
- 顺手给项目**建了测试基础设施**
- 之后所有改动都有回归保障

---

## 四、复杂重构：用并行子 Agent 拿多方案

需求：`ai_generator.py` 当前只支持单轮工具调用，要改成多轮（用于"比较两门课纲领"这类问题）。

### 4.1 把长 prompt 写成 markdown 文件

```text
backend-tool-refactor.md
├── Current behavior
├── Desired behavior
├── Example flow（具体场景）
├── Requirements
└── Notes（测试外部行为而非内部状态）
```

这是 Claude Code 推荐做法——复杂需求**别在 chat 里堆**，写文件 → `@该文件`。

### 4.2 关键 prompt：派遣两个 subagent 并行 brainstorm

```text
Don't implement any code, but dispatch two subagents to
brainstorm potential options. Compare and recommend.
```

Claude 用 **Task 工具**派出两个独立子 Agent → 并行读文件 → 各提一套方案：

- Approach A：迭代式（简单）
- Approach B：多轮逻辑 + 辅助方法（更彻底）

> **架构师视角**：**让 Agent 自己开多个并行的"虚拟工程师"**比单线决策更接近团队设计评审。代价是 token 多花一点，收益是早期看到方案空间。

### 4.3 选定方案后再进 Plan 模式

```text
> Implement Approach A.
shift+tab×2  (Plan)
```

Plan → 审阅 → Auto-accept → 实施 + 写测试 + 跑测试 + 浏览器验证。

---

## 五、CLAUDE.md 沉淀偏好的二次案例

发现 Claude 总爱自己起服务器，每次都要拦住它。直接：

```text
# don't run the server using ./run.sh — I'll start it myself
```

让 `#` 把这条写进 `CLAUDE.local.md`（个人偏好，别强加给团队）。

---

## 六、要点速记

- **遇错先写测试，再修**——测试是 bug 的容器，也是回归的护栏。
- **Extended Thinking + Plan 模式**叠加，适合复杂任务的高质量起手。
- 长复杂 prompt → 写成 markdown → `@文件` 引用，比聊天里堆字符高效。
- **派遣并行 subagent brainstorm 多方案**是 Claude Code 的杀手锏之一。
- 重复唠叨 Claude 的话 → `#` 写进 `CLAUDE.md` 一劳永逸。

