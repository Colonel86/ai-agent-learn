# 技能

- 安全可靠：使用 Guardrails AI、NLI 幻觉检测模型、Presidio 解决 AI Agent 输出不可控的问题——在运行时用 validator 拦截幻觉（回答不忠于检索原文）、话题跑偏、PII 泄露、竞品提及这四大失效模式，确保 LLM 应用行为始终落在预定义边界内。
- 红队测试：使用手动攻击手法（注入/越狱/prompt 探测等五种）、Giskard 自动化扫描、LLM 辅助红队解决 AI Agent 上线前漏洞未知的问题——站在攻击者视角主动打穿自己的应用，暴露偏见刻板印象、敏感信息泄露、服务中断、幻觉这四大漏洞并在事故发生前修掉。
- 治理：使用 Unity Catalog（三级命名空间 + 视图掩码 + UC Function 工具 + 服务主体身份 + AI Gateway/MLflow）解决 AI Agent 权限过宽、行为不可追溯的问题——把数据、工具（Function）、Agent 本身（Model）纳入同一套目录和 ACL，用统一的 grant/revoke 实现最小权限，用统一的审计与 lineage 实现全程可观测，避免"POC 两三周、上生产八个月"的治理补课。

## 精炼版

- 治理：Unity Catalog → 数据/工具/Agent 同目录同 ACL，最小权限 + 全程审计（管控方，平台层）
- 红队测试：手动攻击手法 + Giskard 自动化扫描 → 上线前打穿防线，暴露偏见/泄露/中断/幻觉四大漏洞（攻方，测试层）
- 安全可靠：Guardrails AI + NLI 幻觉检测 + Presidio → 运行时拦截幻觉/跑偏/PII/竞品四大失效模式（守方，输出层）

## 记忆

使用 LangGraph Store/Checkpointer、Letta（MemGPT）、Mem0、Zep/Graphiti、Hindsight 解决 AI Agent 上下文窗口有限、跨会话即忘的问题——短期用 checkpoint 持久化 Agent State（线程内多轮状态可恢复、可回放），长期把对话沉淀为语义/情景/程序三类记忆，写入时机分 hot path（对话中 Agent 主动调工具存，实时但加延迟）与 background（会话后异步抽取，不阻塞但有滞后）两条路径，运行时上下文按 system 分区组织（Letta 的 core/persona/human blocks 常驻 system prompt，archival/recall 按需分页调入），落库则用"记忆表（id/namespace/key/value/embedding 向量列）+ 按 user_id 命名空间隔离 + 相似度索引"的持久化表设计支撑跨会话检索与更新。
