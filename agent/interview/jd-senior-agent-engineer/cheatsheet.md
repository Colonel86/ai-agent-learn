# 资深 Agent 工程师 · 临考速记卡（20 分钟扫读版）

> 用法：考前过一遍每块的「电梯陈述」能脱口而出即可。数字标 ≈ 为量级感，标「(现查)」的别背死。
> 一条贯穿全卡的总纲：**L0 模型是概率底座、天生不可靠 → 一切硬约束（鉴权/预算/越权/幂等）放确定性边界，不写进 prompt 指望模型自觉。**

---

## 01 · Run Loop 与多 Agent 编排

**🎤 30 秒**：Agent 自主性在机制层就是一个被驯服的 `while not done` 循环，每圈四相——感知(装配 context+上一步 observation)→规划(决定下一动作)→执行(调工具)→**验证**(校验结果)。验证相最易漏却是命门：不验证错误就静默向上级联。单 agent + 好工具 + 扎实 verify 是 80% 场景正解；只有可并行分解/context 隔离/真专业化才上 Orchestrator-Workers。

**✅ 必答 3 要点**
- 四相 + 四道退出闸（done 信号且 final 也 verify / step 上限 / 循环检测 / token 预算）；触顶**别假装成功**，返回 `budget_exhausted`。
- 规划三范式：ReAct（逐步、带全量 history 重决策、调用随步数线性增长）/ Plan-and-Execute（规划集中 1 次、执行可用小模型，省的是贵 token 不是请求数）/ Reflexion（叠加层，失败写 episodic 重试）。生产默认**混合体**：先 plan，偏离即 re-plan。
- 多 agent 成本 ≈ 裸 chat 的 ~15x（Anthropic，现查）；但单 agent 工具循环本身已 ~4x chat，故多 agent 相对**单 agent 循环**只 ~3-4x。

**🔥 最可能追问：「15x 是比谁？」**
基线是 **chat 交互**，不是单 agent 循环 → 单 agent 工具循环已 ~4x chat → 多 agent 相对单 agent 循环约 3-4x、相对裸 chat 才 ~15x → 别让人以为「多 agent 比单 agent 循环贵 15 倍」。

**⚠️ 反模式**：无界 ReAct 跑到 done（绕圈、爆 token、没法 debug）；用拓扑复杂度掩盖 prompt/工具没做好。

---

## 02 · 工具调用网关 · 契约 · 端云协同

**🎤 30 秒**：在概率模型和确定性副作用之间插一层确定性边界。契约=数据（一半给模型看 name/desc/schema，一半给网关看 scopes/副作用/危险级），网关=执行点（authN→authZ→校验→策略闸→限流→幂等→执行→审计 的中间件链）。凭证绝不进 prompt，在执行阶段服务端注入。同一份契约端云两侧执行，靠幂等+对账保一致。

**✅ 必答 3 要点**
- 顺序约束：authN 必须最先、审计必须最外（短路也留痕）、execute 必须最后；限流常前移到 authZ 前省开销。
- 授权≠凭证：authZ 按 caller 身份算 scope 交集（不碰密钥）；凭证用 OAuth Token Exchange(RFC 8693) 换降权+限 audience+几分钟过期的下放 token。
- 非幂等工具 `max_retries=0`；幂等键既防重放也防并发（`INSERT...ON CONFLICT` 原子占位，挡 TOCTOU，Stripe 式语义）。

**🔥 最可能追问：「框架能调工具了，为什么还要网关？」**
框架解决「调得到」，网关解决「安全/可控/可审计/可复用」→ 鉴权/限流/危险拦截必须确定性代码不能写 prompt → 横切收口（否则 N 个工具漏 N 次）→ 但不是都要独立服务：单 agent 少量只读工具，in-process 中间件链就够，独立服务是为多 agent/多租户才付 ~1-5ms 一跳。

**⚠️ 反模式**：把安全策略写进 system prompt（「你只能调 A/B」一句注入就越权）；错误原样回喂（泄露内部拓扑成注入面）。

---

## 03 · MCP Gateway 与协议

**🎤 30 秒**：MCP 是 JSON-RPC 2.0 的 client–server 协议，把 N×M 集成降成 N+M，唯一解决**复用与互操作**（不是「能不能跑通」）。与框架正交可叠加，不是编排框架。三原语按控制方分：tools(模型控制,~POST) / resources(应用控制,有 URI,~GET) / prompts(用户控制,~slash command)。本地走 stdio，远程走 Streamable HTTP。Gateway 是治理层（聚合 N server + 单点鉴权 + 工具裁剪 + 审计），不是接入层。

**✅ 必答 3 要点**
- 握手三步：`initialize`(报版本+capabilities) → server 回 → `notifications/initialized`；能力按连接动态裁剪，运行时动态发现（`tools/list` 等）。
- 安全四攻击面：tool poisoning（描述埋注入）/ rug pull（授权后偷改定义→哈希 pin+变更告警）/ confused deputy / 工具结果即数据非指令。
- Gateway 用 token exchange(RFC 8693) 把广 token 换 per-server 窄 token（audience 绑定，server 拒错配）；spec 明令 server 不得接受非签发给自己的 token。

**🔥 最可能追问：「MCP 和 function calling 什么关系？」**
function calling = 模型如何表达调工具（模型层能力）；MCP = 工具如何被标准化暴露和发现（接入层协议）→ 正交叠加，MCP 暴露的工具最终还是经 function calling 选 → 没复用需求时 MCP 是过度工程。

**⚠️ 反模式**：为 2 个工具立 server（多个进程要部署/鉴权/监控，回不了本）；把 MCP 当编排框架。

---

## 04 · 多层 Memory

**🎤 30 秒**：记忆是三条正交轴叠出来的——作用域(工作/会话/跨会话,决定活多久) × 内容类型(semantic/episodic/procedural,决定怎么改行为) × 更新时机(hot path/background)。核心是讲清写入→巩固→召回注入→遗忘的生命周期，这正是和纯 RAG 的最大区别（RAG 没有写入和遗忘）。

**✅ 必答 3 要点**
- 三类写策略不同（关键区分点）：semantic 增删改+冲突解决；episodic **纯追加、只 embed observation**（不整条 embed，避免复盘文字污染匹配）；procedural 整体重写+version bump、`index=False` 按 key 取。
- semantic 召回 ≈ RAG 检索（代码可共用），区别全在写入侧的生命周期；冲突解决默认 recency-weighted（新覆盖，旧进 audit）。
- 更新时机默认 background（主路径快）；hot path 每写一次多一次 LLM 抽取 ≈ 几百 ms~数秒。记忆注入留 ≈1-2k token / top-k 3-8 条（现查）。

**🔥 最可能追问：「短期/长期 和 semantic/episodic/procedural 是一回事吗？」**
不是，两条正交轴 → 短期/长期是生命周期，semantic/episodic/procedural 是内容性质 → 短期里也能有 semantic（刚抽的实体放 working memory，会话结束即弃）→ 把两轴绑死的人会用一套 upsert 通吃，踩 episodic 被去重、procedural 没法回滚的坑。

**⚠️ 反模式**：一套 upsert 通吃三类；procedural 挂 user_id 下（应 per-agent `(app, agent_id)`，否则改一处不生效）。

---

## 05 · Context 工程：Context Editing + Prompt Caching 降本

**🎤 30 秒**：把 context 当稀缺资源经营——成本(input 线性收钱、attention O(n²)) + 质量(context rot / lost-in-the-middle U 形曲线)双重压力。三杠杆作用在窗口不同部位：Prompt Caching 省前缀、Context Editing 砍膨胀历史、Memory Tool 把长期记忆搬出窗口。布局铁律：稳定在前、变动在后。

**✅ 必答 3 要点**
- Prompt Caching = KV-cache 跨请求持久化，省 prefill 计算（cache_read ≈ 0.1x，write 5min ≈1.25x / 1h ≈2x，现查）。命中四要素：前缀逐字节一致 + 同模型 + TTL 内 + ≥ 最小可缓存 token。渲染顺序固定 tools→system→messages。
- break-even：5min TTL ≥2 次复用回本、1h ≥3 次。
- Editing ≠ Compaction（高频考点）：Editing=**删除** stale tool_result/thinking（`context-management-2025-06-27`）；Compaction=**摘要**（`compact-2026-01-12`，默认 ≈150K 触发，须回传 compaction block）。

**🔥 最可能追问：「重复同前缀请求 cache_read 恒为 0，怎么排查？」**
必有 silent invalidator 在前缀里 → 逐一审：① system 有 `datetime.now()`/uuid/user_id；② `json.dumps` 没 `sort_keys=True`；③ tools 列表顺序/集合每次变（排最前一变全废）；④ 前缀没过最小可缓存阈值；⑤ 中途切了模型 → 终极手段 diff 两次渲染出的 prompt 字节找第一个分叉点。

**⚠️ 反模式**：system 里插动态值（缓存永远 0 命中还白付 write）；Context Editing 清得太勤（每次改前缀触发 rewrite，溢价吃掉省的窗口）。

---

## 06 · 全链路 trace 落库与可观测

**🎤 30 秒**：trace 不是日志，是带 `parent_span_id` 的 span 树——log 丢因果父子链、metric 丢单次内部结构，只有 trace 能定位「具体哪一步坏」。一次提问=一棵 trace。不只「看」，要落库做分析/回归/数据飞轮（只看是 20% 价值）。

**✅ 必答 3 要点**
- 缝树机制：进程内靠 OTel Context（Python `contextvars`）；跨进程/跨 agent 靠 W3C `traceparent` header（inject/extract），共享 trace_id。埋点走 OTel（OpenInference=Arize系 / OpenLLMetry=Traceloop系）→ 埋一次后端任意换；auto-instrument 拿 80% + 关键节点手标 20%。
- 落库按负载分库（Langfuse v3 四件套）：ClickHouse(列存,百万行写多读聚合) + Postgres(事务强一致 prompt 注册表) + Redis(摄取队列非阻塞) + S3(原始大 payload)。
- 采样反直觉：LLM 量小价值高 → 全采或 **tail**（留全 error/慢/高成本）；绝不 head 概率丢 error。脱敏在 Collector 入库前做（采样≠隐私手段）。

**🔥 最可能追问：「开了 Prompt Caching，token 成本怎么记才不算错账？」**
别只记一个 input_tokens 乘单价 → Anthropic `usage.input_tokens` 是「未命中缓存的剩余」，cache_read(~0.1x)/cache_creation(~1.25x) 分开，三者相加才是总输入，四档分别按单价加总 → **反向坑**：OpenAI `prompt_tokens` 已含 cached_tokens，直接加会重复计 → 缓存 token 在 span 里单列别提前合并。

**⚠️ 反模式**：手搓 OTel span 包 HITL 节点（interrupt 两次 invoke→切成两条断 trace、误标 ERROR）；用滚动 alias 不钉具体 model id（指标一动归因不到）。

---

## 07 · 安全护栏：重试/fallback · token 预算 · 越权 · 人审

**🎤 30 秒**：护栏是在确定性边界上设闸，把概率模型的不可控吸收在它溢出成真实事故之前。四闸串成网关中间件链：budget→policy→param→hitl→retry/breaker→audit。安全闸优先确定性，容错闸优先复用成熟件。

**✅ 必答 3 要点**
- 重试先分类：瞬时(429/5xx/529/超时)退避重试+jitter（无抖动会惊群）+尊重 Retry-After；4xx/内容拒绝不重试；schema 失败是另一类 **reask 重试**（带错误改写）。写操作必须先有幂等键。
- token 预算三件套：预估 gate(防单次爆) + 真值 ledger(防累计漂移,usage 四类分开) + 触顶 enforce；并发用 **reserve/settle 两段式**（Redis 原子预扣，异常必退预扣）。防 runaway 是 max_steps **且** token 双闸。
- 越权纵深防御四层：① 策略在网关 ② 危险工具 default-deny+HITL ③ 工具返回是数据非指令 ④ **最小权限 scoped 凭证**（兜底，把「判断对不对」降级成「根本做不到」）。

**🔥 最可能追问：「HITL 一直没人响应，默认拒还是默认放行？」**
**fail-closed：默认拒绝** → 高危动作 TTL 超时自动拒+通知，绝不 fail-open（没人理就执行高危=灾难）→ 扫 checkpointer 里 `updated_at` 超 TTL 的 thread 自动拒/重提醒 → 留不可变审计 `{approver, action, params_hash, decision, ts, trace_id}`。

**⚠️ 反模式**：跨模型 fallback 当 try/except 换 client（prompt/schema/停止语义不通用，会静默吐畸形；最稳是同模型多 provider）；安全闸全用 LLM 判（本身可被注入、误判、加延迟）。

---

## 08 · 基本功：Function Calling 与 RAG

**🎤 30 秒**：两条腿。Function calling 真相是「模型吐结构化意图 → 你执行 → 结果回填」的无状态循环，模型**从不执行你的代码**，靠 stop_reason 驱动。RAG 是八环管线（离线建库①-⑤ + 在线查询⑥-⑧），生产真正瓶颈在解析/切分/检索+重排/评估这四处。

**✅ 必答 3 要点**
- 并行工具调用：所有 tool_result 放**同一条 user 消息**回填（拆成多条会静默训得模型不再并行）；失败也回 `is_error:true`，少一条配对就 400。
- 两阶段检索：Bi-Encoder 双塔独立编码可离线建索引(~5ms 宽召回 50-200) → Cross-Encoder 拼接进同一 attention(~50-100ms 精排到 8-12)；后者无法预先索引，这是「reranker 总在第二阶段」的根因。
- 幻觉两源头（RAG Triad）：Context Relevance 低→修检索；Groundedness 低→修 prompt/约束引用。`strict:true` 放工具定义不放 tool_choice；数值区间/字符串长度 schema 兜不住，要应用层 Pydantic 校验。

**🔥 最可能追问：「RAG vs 长 context vs 微调怎么选？」**
先分改的是知识还是行为/风格 → 行为/格式→微调(或先 few-shot)；知识→看量和变化：小且稳定直接塞 context(配 caching)、大/变/要溯源→RAG、量中等要全局推理且能接受贵→长 context → 生产常**组合**（RAG 供知识+微调定格式+caching 降本），别答二选一。

**⚠️ 反模式**：查询/入库 embedding 不一致（召回全乱且无报错；换 embedding=重建索引）；FAQ/单点事实上 GraphRAG（重武器打蚊子）。

---

## 09 · 评测驱动开发（Promptfoo · DeepEval）

**🎤 30 秒**：把 TDD 的红→绿→重构搬到 prompt/agent——先建评测集+定义「好」的可度量标准，再迭代，分数掉门槛 block 发布。LLM 输入定输出是分布，eval 不是 assert==，是在样本集上量化「好的比例」。团队通病是低估评测、高估模型。

**✅ 必答 3 要点**
- 两类×两节奏：rule-based(正则/schema/工具是否被调,快免费可复现)→每 commit；model-graded(LLM-as-Judge)→发布前/夜间。确定性优先，能 rule 判绝不上 judge。
- 4 层评估，**trajectory 是 agent 特有且最易缺的那层**：component→retrieval→**trajectory(路径/工具序列对不对,防瞎走对)**→task。需 trace 记 span 树才测得了。
- LLM-as-Judge 四要点：强评弱 / pairwise 比绝对打分稳 / 带 CoT reason / 校准(与人工 ≈70-85% 一致)；偏置=position/verbosity/self-enhancement。

**🔥 最可能追问：「eval 集会不会过拟合？」**
会，只对固定集调 prompt 等于背答案 → 治法：① 留 held-out 集（改 prompt 时不可见，只发布前验）② 持续从线上失败 trace 回流新分布 case（数据飞轮，打 `from_prod_trace` 标签）③ 定期人工抽检真实流量，别只信 eval 分。

**⚠️ 反模式**：每 commit 跑全量 model-graded（慢+烧钱+judge 方差导致门控 flaky）；eval 集 5-10 条就当 CI gate（一条翻转分数跳 20 点）。数据集不进 git 不绑 config_snapshot。

---

## 10 · Rust：端侧与实时链路（加分项）

**🎤 30 秒**：不是再学一门语言，是回答「agent 栈哪一段值得从 Python/TS 下沉 Rust」。Rust 赢的不是峰值吞吐（那是 GPU 的事），是①无 GC→尾延迟可预测 ②部署形态（小二进制+交叉编译+WASM，跑进手机/浏览器/边缘）③内存安全 without GC。位置「窄而深」：只占端侧+实时+库热点，编排永远 Python/TS。

**✅ 必答 3 要点**
- 实时看 p99/抖动不看均值；音频帧预算 ≈10-20ms，一次 GC 尖刺吃掉整帧。语音管线 ASR→LLM→TTS 三段流水线**重叠**而非串行，Rust+tokio 干编排+背压。
- 背压：有界 channel（`mpsc::channel(N)`）下游满→上游 `send().await` 挂起→背压回传；无界 buffer+下游慢=OOM（最常见生产事故）。
- 落地形态：PyO3 把单个 CPU 热点下沉成原生扩展（计算>>传参才回本，`allow_threads` 释放 GIL）；端侧推理优先 llama.cpp 绑定（蹭成熟 GGUF），candle 主打 WASM。

**🔥 最可能追问：「Python 调的不也是 C++/CUDA，瓶颈在 GPU，Rust 快在哪？」**
对，峰值吞吐看 GPU kernel 跟语言无关 → Rust 不赢吞吐，赢①延迟可预测性(无 GC 抖动)②部署形态(端侧/WASM)③把 CPU 侧热点(tokenize/采样/DSP/背压)做稳 → 瓶颈纯在 GPU 推理就不该碰 Rust（这恰说明我知道边界在哪）。

**⚠️ 反模式**：全栈 Rust 重写 agent（90% 时间在等 LLM 网络 I/O，瓶颈是模型不是语言，编排层高频迭代被借用检查器拖慢）；没 profiler 证据没端侧硬约束就提议「Rust 重写」。
