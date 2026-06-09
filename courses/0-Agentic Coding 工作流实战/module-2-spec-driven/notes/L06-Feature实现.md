# L06 Feature 实现（Implementation）

> 原始字幕：`subtitles/L6-eng.vtt`

---

## 一、进入 Implementation 的标准动作

1. **重温 plan**：在 IDE 里打开 `plan.md` 扫一眼
2. **/clear 清空 context**：让 Agent 从 spec 重新加载，避免被对话历史污染
3. **Prompt**：明确告诉 Agent 实施哪些 task group

---

## 二、Prompt 模板

最简版：
```text
Implement all task groups in @specs/hello-hono/plan.md
```

需要更小步：
```text
Implement only Task Group 1 in @specs/hello-hono/plan.md
```

> **何时一组一组实施？** 当 task 涉及**安全 / 数据库迁移**等"小错误会复利成大问题"的领域时，建议一组一停一审。

---

## 三、Agent 跑起来后

- **看 console 实时输出**：感知它在做什么
- **看 IDE 的 commit 窗口/diff**：实时看文件变化
- **Agent 自带 validation**：每个 task group 跑完会自检

你的角色不是写代码，是 **architect / supervisor**：
- 确保 Agent 拿到了清晰的契约
- 早期就开始看 diff，发现走偏立刻打断

---

## 四、运行验证

实现完后：
1. 跑 `npm run dev` / `package.json` 里相应脚本
2. 浏览器开起来看效果

这一步是"代码层验证"。下一节会做"工程层验证"（人工 review + 测试）。

---

## 五、要点速记

- **/clear 是 implementation 前的必要动作**
- 高风险领域**一组一组**实施，不要一次性 implement-all
- 边跑边看 diff，避免 30 分钟跑完才发现走偏
- Agent 的自检 ≠ 你的验收，下一节才真正闭环
