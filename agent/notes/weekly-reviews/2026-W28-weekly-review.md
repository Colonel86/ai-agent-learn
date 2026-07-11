# 2026-W28 周复盘（6/30 – 7/11，含补记 W27）

> 自动生成于 2026-07-11（复盘日）
> 上一篇：`2026-W26-weekly-review.md`（W27 复盘缺失，本篇合并补记 6/30–7/5）
> 说明：追踪表 `xlsx` 仍几乎全空，本复盘按 git 提交 + 实际文件产出统计（与 W24–W26 口径一致）。

---

## 一、完成了哪些任务

这两周的主题是 **「课程扫荡收官 + 首次跑通本地复现实验」**。约 58 次提交、315 个新笔记文件，roadmap 状态从「需要学习」清单基本清零（已学 34 门，待学降至 1 门）。

| 日期 | 产出 | 说明 |
| --- | --- | --- |
| 6/30 | course-08 面试速答总结 | W1 各节 + 反思/工具使用章追加「回答骨架」 |
| 7/2 | Agent Skills 课程笔记 L0-L9 | 另有选型资产重组入 skills、观测平台选型补硬判据 |
| 7/4 | 记忆三连课笔记 | 12a Agent Memory / 12b LLMs as OS（MemGPT）/ 结构化输出 + Function-calling 两门 |
| 7/5 | ⭐ **课程笔记批量收官日**（26 提交） | AutoGen / CrewAI 生产课 / A2A 协议 / E2B Coding Agents / Neo4j KG×2 / DSPy / NeMo / Semantic Caching / Guardrails / Red Teaming / Governing AI Agents / RAG 2025 / Document AI / Vector DB / Multi-vector / Agentic KG / Data Agents 等 **20+ 门**笔记与素材，并把课程库重组为 **11 个分类目录** |
| 7/6 | 全仓 ASCII 图转 Mermaid 第二批 | 约 **200 处 / 140+ 文件**，9 个分类目录全覆盖 |
| 7/7 | NeMo Agent Toolkit 课程总结 + FirstWorkflow 项目落地 | 补 instrumentation / telemetry sink 术语；GPA Venn 图转 mermaid |
| 7/8 | ⭐ **本地复现两连**：`climate_analyzer`（NeMo L3-L7）+ `nba_sql_tuner`（Improving Accuracy 课） | 从「抄课程」升级为「本地跑通 + 自设实验」 |
| 7/8 | ⭐ nba_sql_tuner **受控实验 + 泛化探针** | 用 `07_fairness_probe.py` 诚实修正了自己「finetune 学风格、memory 背事实」的错误结论：差异主要来自**容量**，loss→0 反而损泛化 |
| 7/9 | L4 笔记「Fine-tuning 与 Memory Tuning 训练层异同」+ Governing AI Agents 实操手册 | 治理章节入选型矩阵 + LoRA 补充笔记 |
| 7/10 | Governing AI Agents 课程总结 | 从 Databricks 学到的治理方法论 |

**一句话总结**：课程输入阶段正式收官（34 门），并且第一次出现了「本地复现 + 受控实验 + 推翻自己结论」的科研式闭环——nba_sql_tuner 的公平性探针是这两周最有含金量的产出。

---

## 二、耗时统计

追踪表 `耗时(h)` 列仍未填，按产出体量估算：

- 7/5 课程批量收官（20+ 门笔记生成与校对，量极大）：约 **8–10h**
- 7/8 两个本地复现项目 + 受控实验（需调环境、跑训练、写探针脚本）：约 **6–7h**
- 6/30–7/4 记忆/结构化输出等 5 门课 + roadmap 整理：约 **6h**
- 7/6 Mermaid 批量转换（200 处逐图核对）：约 **2–3h**
- 7/7 / 7/9 / 7/10 总结与手册：约 **4h**
- **两周合计：约 26–30h**（周均 13–15h，与 W25 相当，低于 W26 峰值属正常回落）

---

## 三、难点 / 待解决的问题

1. **微调对比结论翻车又扳回（亮点也是难点）**：最初把 finetune/memory 的差归因于「loss 平台 vs loss→0」，受控实验证明是容量（rank/层数）在起作用；且真正的 Lamini MoME「多专家 + 路由」架构**未复现**——这是项目自己标注的诚实边界，值得后续补。
2. **追踪表持续失联**：xlsx 仍只有 1 个任务标记完成，与实际进度严重脱节。建议要么每周复盘时顺手同步，要么放弃 xlsx 改用 git 口径（连续 4 周复盘都在绕开它了）。
3. **博客欠账扩大**：目标每两周一篇，唯一的草稿还停在 5/25（prompt-engineering-tips-draft），**已拖欠约 6–7 周 / 3 篇**。
4. **W27 复盘缺失**：上周六未生成周报，本篇已合并补记。

---

## 四、下周（W29）学习计划建议

课程输入已收官，下周应全面转向**输出与工程**：

1. **写博客（最高优先级）**：nba_sql_tuner 的受控实验是现成的高质量素材，先还一篇账。
2. **启动追踪表上的实战项目**：Phase 1 的项目 1（多模型问答 CLI）或直接跳 Phase 2 项目 3（LangGraph 个人助手 Agent）——课程知识已远超 Phase 1 要求，可考虑在表中标注跳级理由。
3. **补 MoME 复现**（可选）：给 nba_sql_tuner 加多适配器 + 路由的极简版，把「诚实边界」变成第二篇博客。
4. **同步 xlsx 追踪表**：把已完成课程/项目状态回填，或做出「弃用」决定。

### 建议博客主题（基于近两周所学）

- 《Fine-tuning vs Memory Tuning：一次受控实验如何推翻我自己的结论》（强烈推荐，有代码有数据有反转）
- 《从 NeMo Agent Toolkit 看 Agent 可靠性：instrumentation 与 telemetry 的工程实践》
- 《Governing AI Agents：Databricks 治理方法论笔记》
- 《34 门 Agent 课程刷完后，我整理出的 11 类知识地图》

---

## 五、提醒事项

- 📝 **该写博客了**：目标每两周一篇，目前拖欠约 3 篇，建议本周末先出一篇（素材见上）。
- 🗂️ **笔记整理**：课程笔记已按 11 类归档在 `agent/courses/`，结构良好；但 `agent/notes/` 下 daily 笔记停更于 5/23，blog-drafts 只有 1 篇草稿——建议把 7/8 实验心得沉淀成 draft 放入 `agent/notes/blog-drafts/`。
- 📊 追踪表同步或弃用，二选一，别再悬着。

继续保持！课程收官 + 第一次跑出「推翻自己结论」的实验，这两周的质量比数量更值得骄傲。💪
