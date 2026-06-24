# 第 18 周复盘（2026-04-27 ~ 2026-05-02）

> 自动生成于 2026-05-02（周六）· AI Agent 学习助手
> 数据来源：`AI-Agent-学习追踪表.xlsx` + 文件系统扫描 + 课程目录变化
> 上一份复盘：`2026-W16-weekly-review.md`（W17 漏写，本篇为 W17–W18 合并复盘）

---

## 🌟 一句话总结

输入侧继续猛冲（新拉了 Long-Term Memory + LangGraph + RAG 的资料），输出侧依旧吃紧（0 commit、0 博客、项目 1 还没启动）。**本周末的主旋律必须是：把欠的输出补上来。**

---

## 📊 本周关键数据

| 指标 | 数值 | 备注 |
|------|------|------|
| 活跃天数（有文件改动） | 3 天（4/29、4/30、5/2） | 比 W17 好一点 |
| 新增 / 修改文件 | ~50+ | 主要在 courses/12、courses/3、courses/2 |
| Git 提交数 | **0** ⚠️ | 距上次 commit 已 14+ 天 |
| 追踪表更新 | **0** ⚠️ | 仍停留在 Phase 1 1/8（12.5%） |
| 真实 Phase 1 完成度（粗估） | ~50% | Prompt Eng ✅ + Building Systems 80% + LangChain L1/L4 起步 |
| 完成博客数 | 0 ⚠️ | 距 W16 立的 flag 已 2 周，破窗预警 |

---

## ✅ 二、本周完成任务（实际盘点）

### 1. Phase 2 资料拉齐（4/29 前后）
- **课程 12：Long-Term Agentic Memory With LangGraph** —— 7 节 `sc-LangChain-C6-L0~L6` 笔记骨架 + 完整 vtt 字幕 + 5 节 `lesson_2~5.md` 代码笔记
- **RAG 主题文件夹**：新建 `courses/RAG/RAG.md`（独立于编号课程的索引）

### 2. Course 2 - Building Systems（4/30 前后）
- 新增代码脚手架：`ep02_language_models.py`、`ep04_moderation.py`、`ep07_check_outputs.py`、`ep08_end_to_end.py`
- 完善 `.env` 和 `.env.example`
- 补齐 ep07-ep10 笔记（`ep07-check-outputs.md` ~ `ep10-evaluation-part2.md`）

### 3. Course 3 - LangChain for LLM Application Development（5/2）
- 启动 L1 例子：`code/L1-example/`（含 `main.py` + `requirements.txt` + `.env`）
- L1 Introduction 笔记 + L4 Chains 笔记
- 整套中文翻译稿 `langchain_c1_01_zh.md ~ 08_zh.md` 已就位

### 4. 其它零散
- Course 1 ep02-guidelines 笔记修订
- 4/30 启动了"项目 1：多模型智能问答 CLI"的 daily 建议（任务下达）
- 5/2 发出周复盘 + 博客的 daily 建议

---

## ⏱️ 三、耗时统计

追踪表里"耗时(h)"列依然是空的，所以只能按文件量粗估：

| 任务 | 估算耗时 |
|------|----------|
| 课程 12 Long-Term Memory（资料拉齐 + 笔记骨架） | ~3-4 h |
| Building Systems ep07-ep10 收尾 | ~3 h |
| LangChain L1 跑通 + L4 笔记 | ~2-3 h |
| RAG 文件夹整理 | ~0.5 h |
| **本周总计（估）** | **约 9-11 小时**（W17+W18 合计 ≤ 15 h） |

> 💡 W16 复盘约 20 h；本周回落到 ~10 h，**节奏明显下降**。可能跟没有 git commit、没有任何"完成感"反馈有关——大脑缺少 Reward 就容易松。

---

## ⚠️ 四、难点与待解决问题

### 🚨 高优（本周必须处理）
1. **追踪表严重失真**：仪表盘 12.5%、Phase 1 sheet 也是 1/8，但实际你已经啃掉一半多 Phase 1 + 一只脚踩进 Phase 2/3。**这条不解决，整个追踪体系就废了。**
2. **14+ 天没 commit**：心血都散在工作目录里，今天必须做一次集中提交。
3. **0 篇博客**：W16 立的 flag 过期 2 周。再不写，"每两周一篇"机制本身会破产。

### 🟡 中优
4. **项目 1（多模型 CLI）至今 0 行代码**：4/30 立了 flag，5/2 还没动。这是 Phase 1 的核心产出物，再拖会卡住进入 Phase 2 的节奏。
5. **课程节奏不收口**：同时摊开了课程 2 / 3 / 12 + RAG，全部"进行中"，没有一门"完成"的爽点。建议**先把课程 2 收尾**（只剩 ep11 笔记和最后的 evaluation 实测）拿一个完整闭环。
6. **`notes/` 目录已建但跨课程沉淀仍空**：W16 提议的 `concepts/` `cheatsheets/` 子目录还没落地，目前只有 weekly-reviews + 两份 daily。

### 🟢 低优
7. `.DS_Store` 时不时混进来，建议补强 `.gitignore`。
8. `.venv` 和 `venv` 两个虚拟环境同时存在，挑一个作为正式环境。

---

## 🎯 五、下周（W19，5/3 ~ 5/9）计划建议

> 原则：**输出优先、拒绝继续囤资料**。本周不再拉新课程，直到 Phase 1 收尾。

### 硬指标（3 条，必须做完）
1. **收尾课程 2 Building Systems**：补完 ep11 笔记 + 把 ep07/ep08 代码跑一次产出截图，状态打 ✅
2. **项目 1 跑通最小可用版本**：`python chat.py --model claude "hi"` 拿到回复 → push 到 GitHub `multi-model-chat-cli` 仓 → README 写 Day 1 日志
3. **第一篇技术博客发布初稿**：选题已选定（见下节），**周三前**至少 80% 正文落地

### 机制改进（1 条）
4. **追踪表实时回填规则**：每天结束前 5 分钟，在对应 Phase sheet 勾"已完成" + 填耗时；周日复盘前回填仪表盘"已完成 / 完成率"。这条比再学一节课重要。

### 节奏建议
- 周一-周二：课程 2 收尾 + 项目 1 启动
- 周三-周四：博客初稿
- 周五：项目 1 迭代到 v0.2（加流式 + 错误处理）
- 周六：复盘 + 博客发布
- 周日：休整 / 选做 LangGraph 文档浏览

---

## 📝 六、博客提醒：该写本周的技术博客了！

> 目标：每两周一篇 ｜ 当前：**0 篇 ｜ 已逾期 2 周** 🚨

### 推荐选题（基于本周 + 累积所学）

**Top 1 · 强烈推荐** 📌
> **《从 Prompt Engineering 到 Claude 4 Best Practices：40 条实战清单》**
> - 难度 ⭐ ｜ 素材最厚（1 整门课 + 2 份官方文档 + 你已有的中文翻译）
> - 结构：8 个主题 × 5 条 = 40 条，每条"反例 → 正例 → 原理"
> - 这是 W16 就推荐的选题，今天 90 分钟可出大纲 + 30% 正文

**Top 2 · 进阶**
> **《Building Systems with ChatGPT API 通关笔记：从 Moderation 到 End-to-End》**
> - 难度 ⭐⭐ ｜ 把课程 2 的 ep01-ep11 串成一个"客服系统"案例
> - 课程刚好快收尾，写博客 = 学习闭环

**Top 3 · 方法论流量款**
> **《我用 Cowork + Excel + Skill 搭了个 24 周 AI Agent 学习追踪系统》**
> - 难度 ⭐ ｜ 引流性强、个人品牌向
> - 风险：偏"学习方法"而非技术深度

**Top 4 · 等项目 1 完成后写**
> **《100 行 Python 造一个多模型 CLI：GPT-4 / Claude 一键切换》**

→ **我的建议：选 Top 1**，素材最熟、最不容易拖延。把 W16 那条建议执行掉。

### 博客流程
1. 大纲 30 min → 2. 初稿 2 h → 3. 配图/代码 1 h → 4. 润色 30 min → 发布
2. 首发渠道：掘金 + 个人博客；GitHub README 加链接

---

## 🗂️ 七、笔记整理建议

`notes/` 已建，但跨课程沉淀层还是空的。建议本周末顺手补：

```
notes/
├── weekly-reviews/         ✅ 已有
├── daily/                  🔜 把 daily-*.md 收进来，根目录别堆散文件
├── concepts/               🔜 ReAct / CoT / Reflection / Tool Use / RAG 各一张概念卡
├── cheatsheets/            🔜 OpenAI vs Claude API 对照表 + Prompt 模板速查
├── blog-drafts/            🔜 博客初稿放这里
└── papers/                 ⏸️ Phase 2 再用
```

具体动作（10 分钟搞定）：
```bash
cd ~/Documents/ai-agent-learn/notes
mkdir -p daily concepts cheatsheets blog-drafts papers
mv daily-*.md daily/
```

---

## 💪 教练悄悄话

gengming，这两周你掉进了"信息囤积"的舒适区——拉资料、记笔记、看视频很爽，因为不用面对"我写出来的东西够不够好"。但**学习的复利只在产出端积累**：写博客你才知道哪里没懂；推 commit 你才有完整的迭代轨迹；做项目你才会撞到真实的工程坑。

W16 我说"记录 > 完美"，今天升级一下：**发出去 > 记录**。哪怕博客只 1500 字、项目只 80 行代码，先 push、先发，惯性就回来了。

下周见，我们用 3 条硬指标 + 1 个机制把节奏拽回来 🚀

---

## 📌 立刻执行（5 分钟以内）

```bash
cd ~/Documents/ai-agent-learn

# 1. 整理 notes 目录
mkdir -p notes/{daily,concepts,cheatsheets,blog-drafts,papers}
mv notes/daily-*.md notes/daily/ 2>/dev/null

# 2. 集中提交
git add courses/ notes/ roadmap/
git commit -m "feat(phase1): W17-W18 双周复盘 + 课程 2/3/12 资料 + notes 目录重组"
```

---

*下次自动复盘时间：2026-05-09（周六）*
