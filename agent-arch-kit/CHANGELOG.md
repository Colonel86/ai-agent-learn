# Changelog

## 0.4.0 (2026-08-21)

闭环收口 + 首个 worked example：

- `retrospective` skill：constitution §4 回写义务的半自动执行器——六步检查单
  （W1 矩阵回写 / W2 ADR 复审 / 留债与 N/A 门禁核对 / design doc 校对 / golden set 回流 /
  W3 门禁进化），每步必须给结论或"无 + 理由"，输出 RETRO-YYYYMMDD 记录；
  纪律：消灭静默跳过、单 feature retro 30 分钟内
- `EXAMPLE-adr-v2-dual-mode-routing.md`：首份 ADR worked example（量化研究 Agent V2
  双模式路由 + Skill 配置驱动 vs 修补 V1 vs harness 单循环），带真实数字
  （token ↓43.8% / 核心代码 ↓70% / 246/246）、触发条款标注（A1+A4）与可检验的 Revisit Triggers
- install.sh 同步新增 2 文件

至此 0.1 规划的四个待办完成三个（retrospective / tasks 钩子未做 → 0.5）；
剩余方向：tasks 模板钩子（Selection/Test 偏离项自动转任务）、矩阵源仓同步脚本。

## 0.3.0 (2026-08-21)

新增两个记忆层资产（design doc + postmortem），补齐"系统长什么样"与"出事变升级输入"两块：

- `design/`：轻量架构描述——C4 前两层（系统上下文 + 容器视图，信任边界用 subgraph 标出、
  跨边界连线标认证方式）+ Agent 特有视图（编排拓扑 / 工具面权限表 / 上下文与记忆构成）+
  关键数据流；README 定腐化防线（最后校对日期 + retrospective 检查）
- `postmortem/`：无责复盘模板——核心字段**「哪个门禁本应拦住它、为什么没拦住」**
  （三类失守 → 三种动作：W3 门禁进化 / 检讨 N/A / golden set 回流），
  知识回写小节直接对接 constitution §4 W1/W2；含 TTD/TTM 时间线与"运气"检讨
- install.sh 同步新增 4 文件

## 0.2.0 (2026-08-21)

新增测试/评估维度（知识层 + 流程钩子，法律层零新增——约束仍由 G6 承载）：

- `eval-strategy` skill：Agent 测试金字塔六层（单元/组件/轨迹/端到端/对抗/生产）、
  判分器决策树（能用规则绝不上模型；LLM-Judge 三条纪律：先校准/防偏差/版本化）、
  golden set 管理（双通道来源/holdout 防过拟合/禁止前视偏差）、CI 门禁配置（硬/软/实验对比）、五反模式
- plan 模板测试策略钩子：六层 Test Strategy 表 + golden set 增量 + G6 对齐检查 + 测试留债登记
- install.sh 同步新增两文件；插入顺序改为 Selection Check → Test Strategy → Constitution Check

## 0.1.0 (2026-08-21)

骨架首版——四资产装配的最小闭环：

- `constitution.md` 合并点：核心原则(§1) + 选型红线 R1–R6 与矩阵咨询义务(§2) +
  ADR 升格规则 A1–A4(§2.3) + NFR 门禁摘要(§3, 本体依赖 nfr-standard) + 回写义务 W1–W3(§4)
- plan 模板选型钩子 snippet：六层 Selection Check 表 + 红线自查 + ADR 升格检查 + 回写预埋
- ADR 目录：模板(_TEMPLATE.md, 含 AI Agent 特有维度与触发条款字段) + 编号/生命周期规则
- selection-matrix skill 路由入口(渐进披露, vendored/referenced 两种挂载)
- install.sh 非破坏投影器(支持 MATRIX_SOURCE 环境变量 vendor 矩阵)

已知待办(0.2 方向):

- [ ] retrospective 命令/skill: 收尾时半自动执行 W1(矩阵回写)与 W2(ADR Revisit 检查)
- [ ] tasks 模板钩子: 把 Selection Check 的偏离项与未满足门禁自动转任务
- [ ] 首批 ADR 实例(V2 双模式路由、Phoenix vs LangSmith)作为 worked example
- [ ] 矩阵源仓同步脚本(vendored 模式的更新通道)
