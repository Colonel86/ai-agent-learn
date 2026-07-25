# mem0 —— 纸面研究 + 本课实测(12c)

> **定位**:12c 动手课的纸面档案。原 `Memory框架/框架现状.md` 的 mem0 部分迁入此处,并逐步用本课实测(标 ✅ 实测)替换纸面判断。
> **结论分级**:✅ 稳定/实测 / ⚠️ 快照或厂商口径 / ❓ 待验证。

## 一、定位与 API 面 ✅

**mem0** = LLM 应用/Agent 的记忆层,开源库 `mem0ai`(Apache 2.0)+ 托管版 Mem0 Platform。API 极小:`add` / `search` / `get_all` / `update` / `delete`;底座全可插拔(任意 LLM / 向量库 / embedder)。

**最被低估的卖点:不绑编排框架。** LangMem 绑 LangGraph、Letta 自己就是运行时,mem0 是纯 sidecar——保留你的 agent loop,两个调用接进去。

⚠️ **mem0 不是存储后端,是存储之上的一层**——库模式默认 Qdrant,自托管 server 默认 pgvector;选了它仍要给它挑底座。

## 二、写路径 `add()`(面试重点)⭐

不存原始对话,两阶段 LLM 处理:**抽取**(对话→候选事实)→ **更新决策**(检索相似旧记忆,判 ADD/UPDATE/DELETE/NOOP)。

> 👉 这个决策步骤是它区别于朴素 RAG 的关键宣传点——朴素 RAG 只会往里堆。

### ✅ 实测(L2,mem0ai 2.0.12 + deepseek-chat,temperature=0):宣传与现实的落差

| 实验组 | 结果 |
|---|---|
| 状态演化型矛盾 ×10(搬家/换工作/偏好反转) | **0/10 消解,全部矛盾并存** |
| 纠正型矛盾 ×2(说错了改口) | **0/2——错误事实原样留存** |
| 对照:重复 ×2 / 无关 ×1 | 3/3(NOOP/ADD 全对) |

**机制**(详见 `code/L2/README.md`):抽取阶段把新信息改写成事件叙述("corrected from X to Y"),决策阶段看不到同一属性的两个冲突值,于是永远 ADD。去重正常、从不误改,但也**从不消解**。

**三个推论:**

1. **风险方向和纸面相反**:不是"事实可能被静默改错",是**从不改**——staleness 比宣传严重;
2. **消解质量不是框架承诺的属性**,是"底座 LLM × 内置 prompt"的涌现行为,换底座必须重测;
3. **写入不可复现**(L1 实测):同一对话两次运行抽出的事实条数、措辞都不同,temperature=0 挡不住。

## 三、读路径 `search()` ⭐

纸面说法:打分层按相关性/重要性/时近性加权,融合语义+BM25+实体匹配(⚠️ 厂商自跑数字:时序 +29.6/多跳 +23.1)。

### ✅ 实测(L3,读了源码 + explain=True 验证):纸面与实装的三处落差

1. **实装公式** = `(semantic + bm25 + entity_boost) / max_possible`——**"重要性/时近性"不在 2.x 评分公式里**;
2. **混合打分是"配置涌现"的**:Chroma 无 BM25、不装 spaCy 无实体 boost → 本栈静默退化为**纯语义单信号**(`final ≡ semantic`);要吃满三信号需 qdrant/pgvector + `mem0ai[nlp]`(L6);
3. **时序推理是付费闸门**:`add(timestamp=...)` OSS 版直接 raise 要求 Mem0 平台 API key("Platform-only. Not supported in OSS")——**feature wall 亲手撞实**。

其它实测:threshold 是绝对值闸门,而同一意图换问法分数能从 0.63 掉到 0.49(问法敏感)→ 阈值要按自己语料标定;同语言条目优先命中(记忆存储语言影响排序);自定义 metadata 字段可直接进 `filters`(分域检索好用);`expiration_date` TTL 可用(到期隐身,但过期时间须写入时预知,救不了 staleness);`rerank=True`(llm_reranker)实测:真实调用了 LLM(2.3–2.6s,rerank_score 字段),但其 prompt 是通用相关性判断——对"还能跑步吗?"给"每周跑三次"1.0、给答案所在的"受伤禁跑"0.0,**通用相关性重排修不了"像 vs 答"的错位**。另:读路径全程无 LLM(infer=False 时),输出逐位可复现——mem0 的不可复现全部来自写路径。

## 四、其它工程事实

- **记忆存英文**:内部 prompt 是英文,中文对话进英文事实出(✅ L1 实测;对照:Hindsight 有 `OUTPUT_LANGUAGE` 官方开关,Graphiti 中文保真);
- **API 变化(2.x)**:`get_all`/`search` 必须 `filters={"user_id": ...}`,顶层参数废弃;`update()` 用 `text=` 不用 `data=`;
- **三级 scope**:`user_id` / `agent_id` / `run_id`,组合实现多租户隔离(L4 主题);
- **history 表**(SQLite)记录每条记忆的事件流——写路径的显微镜,但注意向量库里只有最新值,时间轴只在这张旁路表里;
- **代价**:每次 `add()` 烧 1–2 次 LLM 调用,✅ 实测单次 2–5s;托管版有数据出境问题。

## 五、控制权定位(四派光谱)

mem0 = **确定性触发(代码显式 add)+ 非确定性内容(LLM 两阶段)**。对比:Letta 触发和内容都是 LLM;Oracle 26ai 路线触发和内容都偏代码;LangMem 居中。这正是 §二 风险的结构性来源。

## 六、面试速答

- **标准架构答案**:LangGraph checkpointer 管线程内短期状态,Store 或 Mem0 管跨线程长期记忆;Mem0 相比裸 Store 的增值 = 自动抽取 + 冲突消解 + 混合检索;代价 = 每次 add 1–2 次 LLM 调用。**追问消解质量时,给 L2 实测数据(0/12)——这一段是别人背不出来的。**
- **"什么时候不该上记忆框架?"** → 该记哪些字段事先说得清(窄领域)时,结构化 profile 表 + 代码显式写入几乎总是更优;自动抽取的价值只在开放域兑现。
- **"UPDATE 判错了怎么办?"** → 实测是"从不 UPDATE"(L2);缓解 = 写入分流:关键事实走确定性写入(update API),体验型记忆才交给自动抽取。
- **四层记忆映射**:working ❌(checkpointer 的事)/ semantic ✅ 主攻 / episodic 🔶 部分 / procedural ❌。

## 七、未解问题(全行业共享)

1. **高相关记忆的 staleness**:decay 只处理低相关记忆,高相关的陈旧事实恰因相关被优先召回,"自信地错着"——✅ L2 证明 mem0 在这个维度上比纸面更糟;系统性解法见 Zep/Graphiti 的 temporal edge(12d)。
2. **跨交互身份归并**:同一人多渠道出现怎么认,无成熟方案。

> **最后核对:2026-07**(实测部分基于 mem0ai 2.0.12)
