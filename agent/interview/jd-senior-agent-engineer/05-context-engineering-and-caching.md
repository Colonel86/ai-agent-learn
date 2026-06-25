# 05 · Context 工程:Context Editing 与 Prompt Caching 降本

> **一句话定位**:把 context 窗口当成「稀缺、有质量曲线、按 token 收钱」的资源来经营——用 **Prompt Caching** 省重复前缀、用 **Context Editing** 砍膨胀历史、用 **Memory Tool** 把长期记忆搬出窗口,三者作用在窗口的不同部位协同降本提质。
> **对应 JD**:职责 3「接入 Context Editing、Memory Tool、Prompt Caching 降本」。
> **最后核对:2026-06**。⚠️ Anthropic 的具体折扣/TTL/最小可缓存 token/beta 字段名变化快,本章给**机制与布局原则**,精确数字标「现查官网」(查 `skills/claude-api` 或 platform.claude.com)。
> **边界**:记忆的**分层存储**归本系列 04(本章只谈「省窗口 / 省钱」角度的 Memory Tool);统一成本指标「每任务 $」引用 `../../roadmap/agent-selection/8-cost-economics.md`。

---

## 1. 技术原理(机制层,不是名词)

### 1.1 为什么 context 是稀缺资源:成本与质量双重压力

塞满 1M 窗口能跑,不代表该塞。长 context 同时受两种压力:

| 压力 | 机制 | 后果 |
|---|---|---|
| **成本** | 厂商按 input token **线性**计价;但 self-attention 计算是 **O(n²)**。你每多塞一段历史,每次请求都要为它重新付 prefill 的钱 | token 预算被历史吃光;`$/任务` 随对话变长**单调上升** |
| **质量(context rot)** | context 越长,模型对单个 token 的有效注意力被稀释;**lost-in-the-middle**:模型对 prompt **开头和结尾**召回好、**中间**召回差(U 形曲线,出处 Liu et al. 2023《Lost in the Middle》✅) | 关键信息埋在中段会被「看不见」;长 agent run 越往后越容易丢早期约束 |

> 架构师结论 ✅:**context 工程的第一性原理是「高信号密度」**——把窗口里每个 token 都用在刀刃上。RAG 收窄(→ `../../roadmap/agent-selection/3-retrieval.md`)、Context Editing 清理、Memory Tool 外移,本质都在对抗这两条曲线。

### 1.2 Prompt Caching:把 KV-cache 跨请求持久化

要讲透 Prompt Caching,得先讲 **KV-cache**:

- Transformer 自回归生成时,每个 token 的 attention 需要它**之前所有 token**的 Key/Value 向量(causal attention)。**prefill 阶段**把整个 prompt 跑一遍,算出每层每个位置的 KV,存在显存里(这就是 KV-cache),后续 decode 一个 token 只需算新 token 的 Q 去查这堆已存的 KV。
- **Prompt Caching = 把 prefill 出来的这堆 KV 在厂商侧持久化、跨请求复用。** 命中时,厂商**跳过对前缀的重新 prefill**,直接加载存好的 KV。省的是**计算(prefill FLOPs)**,不是网络——这就是为什么 `cache_read` 只收约 **0.1× input 价**(现查官网):重算 attention 的钱省了。

由这个机制,直接推出三条**铁律**:

1. **前缀必须逐字节一致才命中。** KV 是**位置相关**的:token N 的 KV 依赖 token 0..N-1 的全部内容。前缀里任何一个字节变了(一个时间戳、一个重排的 JSON key、多一个工具),**从那个位置往后的所有 KV 全部失效**,无法复用。这是「顺序错了就全 miss」的根因。
2. **渲染顺序固定为 `tools` → `system` → `messages`**(✅ Anthropic)。所以稳定的东西必须**物理上排在前面**:工具定义、冻结的 system prompt、长知识在前;变动的问题、时间戳在后。
3. **缓存是模型相关的**:KV 依赖模型权重,**切模型 = 全 miss**(见 §1.5 与级联的张力)。

**`cache_control` 断点**:你在某个 content block 上打 `{"type": "ephemeral"}`,等于声明「到这个 block 为止的前缀值得缓存」。每次请求最多 **4 个断点**(现查)。命中四要素:**前缀逐字节一致 + 同一模型 + 在 TTL 内 + 前缀长度 ≥ 最小可缓存 token**。

**计费与 TTL(⚠️ 2026-06 快照,现查官网)**:

| 项 | 倍率(相对 base input) | 说明 |
|---|---|---|
| `cache_write`(写入)5min TTL | 约 **1.25×** | 第一次写缓存付的溢价 |
| `cache_write` 1h TTL | 约 **2×** | 长 TTL 写更贵 |
| `cache_read`(命中) | 约 **0.1×** | 省 prefill 计算 |
| TTL | 默认 **5 分钟**,可选 **1 小时** | 命中后刷新存活时间(现查);需周期复用否则过期 |
| 最小可缓存前缀 | 约 **1024–4096 token**,**按模型不同**(现查) | 不够长时**静默不缓存**——`cache_creation_input_tokens: 0`,不报错 |

### 1.3 Context Editing:在长 agent run 中自动清理膨胀历史

Anthropic 的 **Context Editing**(beta header `context-management-2025-06-27`,走 `client.beta.messages.*`):在请求被模型看到**之前**,自动**删除(prune)**较旧、不再有用的内容,腾出窗口、控成本控质量。它**不是摘要**——内容是被清掉,不是被压缩。

策略类型(⚠️ 字段名现查官网):
- **`clear_tool_uses_20250919`**:清理较旧的 **tool_result**(工具调用返回的大块结果);可选 `clear_tool_inputs: true` 连 tool_use 的入参一起清。这是 agent run 里最大的膨胀源——几十次工具调用的原始结果大多用过一次就再不需要。
- **`clear_thinking_20251015`**:清理较旧的 thinking blocks。

触发是阈值驱动的(达到某个 input-token trigger 才清,具体阈值/字段现查官网);保留对话结构与关键信息,只砍 stale 的工具噪声。

> **必须区分:Context Editing ≠ Compaction**(高频考点)。
> - **Context Editing = 删除**(prune stale tool results / thinking)。
> - **Compaction**(beta `compact-2026-01-12`,策略 `compact_20260112`)= **摘要**:历史累计**达到触发阈值**(默认约 **150K token**,可配置;现查)就把早期历史**总结成一个 compaction block** 替换掉。注意阈值是个**固定 token 数,不等于「窗口上限」**——1M 窗口的模型在 150K 就会触发,远没到顶;只有 200K 档模型才接近上限。摘要会丢细节、有信息损失,但保留语义连续性。**关键约束:返回的 compaction block 必须原样回传到下一请求**(append 整个 `response.content`,不能只取 text),否则丢摘要状态。
> 二者可叠加:editing 先砍工具噪声,逼近上限再 compaction 摘要。

### 1.4 Memory Tool:把「该长期记的」搬出 context(只谈省窗口角度)

Memory Tool(类型 `memory_20250818`,**client-side** 执行):模型通过 `view/create/str_replace/insert/delete/rename` 读写一个 `/memories` 目录,**你实现存储后端**。从**省窗口/省钱**视角看它做的事:

- 把跨会话、跨任务该长期记住的东西(用户偏好、项目约定、踩过的坑)**写到 context 之外的文件**,而不是堆在对话历史里每轮重发。
- 需要时模型主动 `view` 把**相关那几条**拉回 context;不需要时它们不占一个 token。

> 与 04 章的边界:记忆**怎么分层存储/检索**(短期/工作/长期、向量库 vs KV vs 图)归 04。本章只用一句话:**Memory Tool 是「把长期记忆从 token 计费的窗口里搬到不计费的文件系统」的省钱杠杆。**

### 1.5 与 KV-cache / 模型档位级联的关系

- **Prompt Caching 就是 KV-cache 的跨请求持久化版**(§1.2)。理解了 KV-cache 的位置相关性,就理解了所有缓存失效规则。
- **与级联/降档(→ `../../roadmap/agent-selection/1-model.md` «模型路由/级联/网关»)有张力** ⚠️:级联想「简单请求用便宜模型」省钱,但**缓存是模型相关的,切模型 = 缓存全 miss**。两个降本杠杆会打架。治法(✅ Anthropic agent-design 实践):
  - **主循环固定一个模型**保住缓存;子任务要用便宜模型时,**spawn 一个子 agent** 单独跑(它有自己独立的缓存前缀),不在主对话里切模型。
  - 同理 **mid-session 别改 tools / system**(它们排在最前,一改全 miss)——要加运行时指令,用下面 §3.4 的 mid-conversation system message。

---

## 2. 应用场景(何时必须用 / 何时是过度工程)

| 技术 | **甜区(必须用)** | **过度工程 / 别用** |
|---|---|---|
| **Prompt Caching** | 大且稳定的前缀被多次复用:长 system prompt、几十个工具定义、长知识/few-shot、RAG 固定指令块;多轮对话(每轮复用整段历史前缀);批处理共享同一份文档 | 每次请求前缀都不同(无可复用前缀);前缀短于最小可缓存 token;单次一次性调用——只付 write 溢价收不回 |
| **Context Editing** | **长 agent run**(几十上百次工具调用,tool_result 把窗口撑爆);端云协同里工具结果体积大 | 短对话/单轮任务(历史根本不膨胀);需要保留**全部**工具原文做审计的场景(清理会丢原始结果——用 trace 落库另存) |
| **Memory Tool** | 跨会话要记住的稳定事实(用户偏好、项目规范);信息多到塞不进窗口且需按需召回 | 一次性会话内的临时状态(用对话历史/工作状态 dict 即可,→ 04);把什么都往 memory 写 = 又一层要维护的状态 + 安全面(见 §6) |

> 决策树:**要不要给这个 feature 上 Prompt Caching?**
> ```
> Q1. 有稳定大前缀(system+工具+长知识)在多次请求间复用吗?
> ├─ 没有(前缀每次都变) → 别上,纯付 write 溢价 → 反模式
> └─ 有 → Q2
>         │
> Q2. 前缀够大吗(≥ 最小可缓存 token,现查)?
> ├─ 不够 → 静默不缓存,白标 cache_control(usage 会暴露 creation=0)
> └─ 够 → Q3
>         │
> Q3. 同一前缀在 TTL 内会被复用 ≥ 2 次(5min)/ ≥ 3 次(1h)吗?(break-even,§4)
> ├─ 否 → 亏,write 溢价收不回
> └─ 是 → 上,断点放在稳定前缀末尾;变动部分排到尾部
> ```

---

## 3. 具体实现方案(布局原则 + 代码 + 最轻起步→升级)

### 3.1 核心布局原则:稳定在前、变动在后

这是整章最该背下来的一张图——**context 窗口从前到后,按变动频率分区**:

```
context 窗口(渲染顺序:tools → system → messages,从前到后)
┌──────────────────────────────────────────────────────────────┐
│ [tools 定义] [system prompt] [长知识 / few-shot]   ← 稳定前缀   │ ← Prompt Caching 命中
│                              ↑ cache_control 断点              │   cache_read ≈ 0.1×
├──────────────────────────────────────────────────────────────┤
│ [对话历史 / 一大堆 tool_result … 膨胀区]            ← 中段       │ ← Context Editing
│                                                                │   清理 stale tool_result
├──────────────────────────────────────────────────────────────┤
│ [本轮 user 输入 / 时间戳 / 变动部分]                ← 尾部       │ ← 永不缓存(每次都变)
└──────────────────────────────────────────────────────────────┘
        ↕ 跨会话长期记忆 → Memory Tool 搬到 /memories 文件,按需拉回
```

**为什么顺序错了全 miss**:KV 位置相关(§1.2)。只要你把一个会变的东西(`datetime.now()`、user_id、未排序的 `json.dumps`)放进了前缀,从它往后的 KV 每次都不同,**断点后面的缓存永远命中不了**。

### 3.2 Prompt Caching 布局 + 命中验证(Python,Anthropic SDK)

```python
import anthropic
client = anthropic.Anthropic()

# 稳定前缀:system + 长知识,断点打在前缀末尾的 block 上
SYSTEM = [
    {"type": "text", "text": FROZEN_SYSTEM_PROMPT},            # 冻结,不插时间戳/user_id
    {
        "type": "text",
        "text": LONG_KNOWLEDGE_BASE,                            # 长知识/few-shot
        "cache_control": {"type": "ephemeral"},                # ← 断点:缓存 tools+system 整段
        # 默认 5min;高频跨分钟复用可用 {"type":"ephemeral","ttl":"1h"}(现查)
    },
]

resp = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=2048,
    tools=TOOLS,                 # 工具定义排在最前;确定性序列化(按 name 排序),别每次顺序变
    system=SYSTEM,
    messages=[{"role": "user", "content": user_question}],     # 变动部分在尾部,不打断点
)

# 验证缓存是否真命中(四类 token 分开看 → 对齐 8-cost-economics「四类 token 分开打点」)
u = resp.usage
print(u.cache_creation_input_tokens)  # 写入缓存的 token(付 ~1.25× 溢价)
print(u.cache_read_input_tokens)      # 命中读出的 token(付 ~0.1×)
print(u.input_tokens)                 # 未缓存、全价处理的剩余 token
# 排查口诀:重复同前缀请求若 cache_read 恒为 0 → 前缀里有 silent invalidator(见 §6)
```

> ⚠️ **`input_tokens` 只是「未缓存的零头」**。总 prompt 大小 = `input_tokens + cache_creation + cache_read`。agent 跑了几小时但 `input_tokens` 只有 4K,别惊讶——大头从缓存读了。算 `$/任务` 要看三者之和,别只看一个字段。

### 3.3 Context Editing(清理 stale 工具结果,beta)

```python
# 长 agent run:让 API 在前缀逼近阈值时自动清理较旧的 tool_result
resp = client.beta.messages.create(
    model="claude-opus-4-8",
    max_tokens=4096,
    betas=["context-management-2025-06-27"],               # ⚠️ beta header,现查
    context_management={
        "edits": [
            {"type": "clear_tool_uses_20250919"},          # 清旧 tool_result;
            # 可选 "clear_tool_inputs": true 连入参一起清
            # {"type": "clear_thinking_20251015"},          # 也可清 thinking blocks
        ]
        # 触发阈值(input-token trigger)/保留多少最近结果 → 字段与默认值现查官网
    },
    tools=TOOLS,
    messages=conversation,
)
# ⚠️ 别用 compact_20260112 / beta compact-2026-01-12 —— 那是 Compaction(摘要),不是 Editing(删除)
```

### 3.4 升级位:mid-session 注入运行时指令而不破坏缓存

运行时要给 agent 加一条操作指令(模式切换、注入状态),**别去改最前面的 system**(一改前缀全 miss)。Opus 4.8 起可把 `{"role":"system",...}` **追加到 `messages` 尾部**(✅ 无需 beta;模型当作 operator 权限指令,且**比把指令塞进 user turn 更抗 prompt injection**):

```python
resp = client.messages.create(
    model="claude-opus-4-8", max_tokens=2048,
    system=[{"type":"text","text":STABLE_SYSTEM,"cache_control":{"type":"ephemeral"}}],  # 前缀不动
    messages=history + [
        {"role": "user", "content": user_msg},
        {"role": "system", "content": "Terse mode:回答控制在 40 字内。"},  # 排在缓存历史之后
    ],
)  # 缓存前缀完好;新指令在尾部 → 不触发全量重算
```

### 3.5 最轻起步 → 升级路径

```
⓪ 裸跑量基线   先不优化,跑一版量真实 $/任务 与 token 构成(→ 8-cost-economics 阶梯⓪)
   │ 有稳定大前缀 + 重复复用
① Prompt Caching ⭐  断点放稳定前缀末尾;盯 cache_read 验证命中 ← 几乎零质量损失,最先做
   │ 长 agent run,tool_result 撑爆窗口
② Context Editing    自动清旧 tool_result;注意它会改前缀→触发一次 cache rewrite(见 §6)
   │ 接近窗口上限还停不下来
③ Compaction         摘要早期历史(有信息损失,谨慎)
   │ 跨会话要长期记忆
④ Memory Tool        把长期事实搬到 /memories,按需召回(省窗口;实现存储+路径校验)
```

> 口诀:**先量化、再优化;缓存几乎零损先做,删除/摘要有损后做,外移(memory)是结构性手术最后做。**

---

## 4. 架构师取舍判断(主选 vs 备选 vs 代价)

### 4.1 Prompt Caching 的 break-even(必须会算)

cache write 比正常 input **贵**,不是无脑上就赚。⚠️ 按快照倍率(现查官网)算:

| TTL | 写溢价 | 读折扣 | 第 N 次的累计 vs 不缓存 | 回本点 |
|---|---|---|---|---|
| 5min | 1.25× | 0.1× | 2 次:`1.25 + 0.1 = 1.35×` < `2×` | **≥ 2 次复用即赚** |
| 1h | 2× | 0.1× | 3 次:`2 + 0.2 = 2.2×` < `3×` | **≥ 3 次复用才赚** |

- **TTL 选型**:连续流量(请求间隔 < 5min)→ 默认 5min,真实请求自己保温,**不用额外 pre-warm**;突发+长空档 → 1h TTL(写更贵但跨空档存活)或在 TTL 内 pre-warm(`max_tokens:0` 预热请求,现查)。
- **代价**:① 前缀一字节漂移就全失效(脆);② 短前缀静默不缓存(白标);③ 并发 fan-out 时,缓存只在**第一个响应开始 streaming 后**才可读——N 个并行请求会同时各付一次 write(治法:先发 1 个、等它吐第一个 token,再 fan-out 其余 N-1)。

### 4.2 三杠杆 × 选型轴

| 杠杆 | 主选场景 | 备选/退路 | 代价 |
|---|---|---|---|
| **Prompt Caching** | 稳定大前缀高频复用 | 无前缀就别上 | 脆(逐字节);多 4 个断点上限;并发 write |
| **Context Editing** | 长 run 工具噪声膨胀 | 短对话用滑动窗口/不处理 | **改前缀→触发 cache rewrite**;丢工具原文(审计另存 trace) |
| **Compaction** | 逼近窗口上限 | 优先 Editing,Compaction 兜底 | 摘要**有信息损失**;必须回传 compaction block 否则丢状态 |
| **Memory Tool** | 跨会话长期事实 | 会话内用工作状态 dict(→04) | 多一层存储 + **路径穿越/PII 安全面**(§6) |

### 4.3 关键张力:降本杠杆之间会打架

- **缓存 × 级联**:切便宜模型省了单价、却丢了缓存(§1.5)。量化:`级联省的单价差` vs `丢缓存多付的 prefill`,简单请求占比不高时,**保模型保缓存可能更划算**。
- **Context Editing × 缓存**:清理动作**修改了中段前缀**,会让那一段及之后的缓存失效、触发一次 rewrite。所以**清理频率要克制**——清得太勤,省下的窗口被反复 rewrite 的溢价吃掉。✅ 取舍:让清理在较高阈值才触发,一次清一大批,均摊 rewrite 成本。
- 统一裁决标准只有一个:**`$/任务`**(→ `../../roadmap/agent-selection/8-cost-economics.md`)。任何 context 优化,先量化对 `$/任务` 和质量 eval 的影响,再决定。

---

## 5. 面试高频问答(重中之重)

**Q1. Prompt Caching 命中的条件是什么?为什么「顺序错了就全 miss」?**
- 四要素:**前缀逐字节一致 + 同一模型 + 在 TTL 内 + 前缀 ≥ 最小可缓存 token**。
- 根因是 **KV-cache 位置相关**:token N 的 KV 依赖它之前所有 token(causal attention)。前缀任一字节变了,从该位置往后 KV 全失效。渲染顺序固定 `tools→system→messages`,所以稳定内容必须物理排前面。
- *(面试官可能追问:few-shot 放 system 还是 messages?动态时间戳塞哪?)* → few-shot 属稳定前缀,放 **system**(或 messages 的共享前缀段)并在其末尾打断点;**绝不**把 `datetime.now()`/UUID/user_id 插进前缀——放到**最后一个断点之后**的尾部 block,或干脆不放。判断标准:**变动频率**——never-change 进前缀,per-request 进尾部。

**Q2. cache write 比正常 input 贵,什么情况下用 Prompt Caching 反而亏?**
- 单次/低频复用就亏:write 约 1.25×(5min)/2×(1h)(现查),read 约 0.1×。**5min TTL 要 ≥2 次复用、1h TTL 要 ≥3 次复用才回本**(算式见 §4.1)。前缀每次都变、或短于最小可缓存 token,也是纯亏(后者还静默不报错)。
- *(面试官可能追问:5min vs 1h 怎么选?)* → 连续流量用 5min,真实请求自我保温;突发+长空档用 1h(或在 TTL 内 `max_tokens:0` 预热)。1h 写更贵,需要更多次读才回本,别默认上。

**Q3. Context Editing 和 Compaction 区别?各自何时用?**
- **Editing = 删除** stale tool_result/thinking(`clear_tool_uses_20250919`,beta `context-management-2025-06-27`);**Compaction = 摘要**早期历史成一个 block(`compact_20260112`,beta `compact-2026-01-12`,默认约 150K 触发,现查)。
- 先 Editing 砍工具噪声(无损语义,只删用过的原文);逼近窗口上限还停不下来再 Compaction 摘要(有信息损失)。二者可叠加。

**Q4. Context Editing 会不会破坏 Prompt Caching?怎么协调?**(深点)
- 会。清理动作**修改了中段前缀**,使该段及之后缓存失效、触发一次 rewrite。治法:**抬高触发阈值、一次清一大批**,把 rewrite 溢价均摊到更多后续命中上;别清得太勤。本质是「省窗口」与「保缓存」的权衡,用 `$/任务` 裁决。

**Q5. 长 context 为什么质量会下降?lost-in-the-middle 是什么?怎么缓解?**
- context rot:越长,单 token 有效注意力越被稀释。**lost-in-the-middle**(Liu 2023):召回呈 U 形,开头结尾好、中间差。
- 缓解:RAG 收窄到高信号 token(→ `../../roadmap/agent-selection/3-retrieval.md`)、把关键约束放**开头或结尾**而非中段、Context Editing 砍中段噪声、Memory Tool 外移长期事实。一句话:**别拿 1M 窗口硬塞,信号密度比绝对长度重要**。

**Q6. Caching / Context Editing / Memory Tool 三者怎么组合降本?举个长 agent 的例子。**
- 三者作用在窗口**不同部位**(§3.1 图):前缀用 Caching、中段膨胀用 Editing、跨会话长期记忆用 Memory 外移。
- 例:一个跑几十轮工具调用的 research agent——system+工具+检索指令打缓存断点(每轮 read 0.1×);跑到一定轮数 Context Editing 自动清掉早期 tool_result 腾窗口;用户偏好/项目约定写进 Memory `/memories`,不在每轮历史里重发。`$/任务` 估算就按 `8-cost-economics` 的四类 token 分开记,看 cache_read 占比是否上去了。

**Q7. 怎么验证缓存真命中了?线上发现命中率为 0 怎么排查?**
- 看 `usage`:`cache_read_input_tokens` 是命中读、`cache_creation_input_tokens` 是写入、`input_tokens` 是未缓存零头。命中率 = `cache_read /(三者之和)`。
- *(面试官可能追问:重复同前缀请求 cache_read 恒为 0,怎么查?)* → 必有 **silent invalidator** 在前缀里。逐一审:① system 里有没有 `datetime.now()/uuid/请求 ID`;② `json.dumps` 没 `sort_keys=True` 或在序列化 `set`(顺序不稳);③ tools 列表每次顺序/集合不同(排在最前,一变全废);④ 前缀长度没过最小可缓存阈值(creation 也是 0);⑤ 中途切了模型。终极手段:diff 两次请求渲染出的 prompt 字节,找第一个分叉点。

**Q8. KV-cache 和 Prompt Caching 是什么关系?模型级联和缓存有什么张力?**
- Prompt Caching 就是把 prefill 出的 KV-cache **跨请求持久化复用**,省的是 prefill 计算,故 read 只 0.1×。
- 张力:缓存模型相关,**切模型全 miss**。级联想用便宜模型省单价,却丢缓存。治法:主循环固定一个模型保缓存,子任务用便宜模型就 **spawn 独立子 agent**(自带独立前缀),不在主对话里换模型;同理 mid-session 别改 tools/system。

---

## 6. 踩坑 / 反模式

| 反模式 / 选错信号 | 为什么坑 | 治法 |
|---|---|---|
| **system 里插 `datetime.now()` / UUID / user_id** | 前缀每次都变,断点后缓存**永远 0 命中**,还白付 write | 冻结 system;动态值放尾部或用 mid-conversation system message(§3.4) |
| **`cache_read` 恒为 0 却没察觉** | 没盯 usage,以为省了实则没省 | 把四类 token 分开打 trace(→ `8-cost-economics`「四类 token 分开」);命中率纳入监控 |
| **前缀太短还硬标 `cache_control`** | 低于最小可缓存 token **静默不缓存**,不报错 | `count_tokens` 量前缀长度;不够长就别标(现查阈值) |
| **mid-session 改 tools / 切模型** | 排最前的东西一动,**整条缓存全 miss** | 工具集稳定+确定性排序;要换便宜模型走子 agent;运行时指令走尾部 system message |
| **并发 fan-out 同前缀** | 缓存第一个响应开始 streaming 后才可读,N 个并行各付一次 write | 先发 1 个等首 token,再 fan-out 其余 N-1 |
| **Context Editing 清得太勤** | 每次清都改前缀触发 rewrite,溢价吃掉省下的窗口 | 抬高触发阈值,一次清一大批,均摊 rewrite |
| **把 Editing 当 Compaction(或反之)** | 用错 beta/策略类型,要么没摘要要么误删 | 记死:Editing=删(`context-management-2025-06-27`)、Compaction=摘要(`compact-2026-01-12`) |
| **需要审计却让 Editing 删了工具原文** | 工具结果被清,事后追不回 | 工具结果**另存全链路 trace 落库**(职责 3),context 里清无妨 |
| **Memory Tool 不校验模型给的路径** | client-side 实现,模型给的 `path` 可 `../` 穿越读写任意文件;还可能把密钥/PII 写进 memory | 把路径 resolve 成绝对路径并校验在 `/memories` 根内(拒 `..`/符号链接);**绝不**往 memory 写密钥;多用户做 per-user 目录隔离 |
| **拿 1M 窗口硬塞全部上下文** | token 吃满预算 + lost-in-the-middle 掉质 | RAG 收窄高信号 token(→ `3-retrieval.md`);该外移的进 Memory |
| **没量 `$/任务` 就堆三层 context 优化** | 过度工程,维护成本 > 省下的钱 | 先裸跑量基线(→ `8-cost-economics` 阶梯⓪),有数再针对性上 |

---

## 7. 回链已有资产 / 课程

- **成本统一标尺**:`../../roadmap/agent-selection/8-cost-economics.md` —— 「`$/任务`」公式、**四类 token 分开记**(`input/output/cache_read/cache_write`)、压降阶梯(① 三级缓存最先做,几乎零损)、缓存与级联的成本账。本章所有降本动作都用它的 `$/任务` 裁决。
- **模型层 / 级联张力**:`../../roadmap/agent-selection/1-model.md` —— «模型路由/级联/网关»;缓存模型相关 → 切模型全 miss,与降档/级联的张力治法(子 agent 保缓存)。
- **检索收窄 token**:`../../roadmap/agent-selection/3-retrieval.md` —— 对抗 lost-in-the-middle 的主手段(把上下文收窄到高信号 token,别硬塞 1M)。
- **可观测 / eval**:`../../roadmap/agent-selection/5-observability-eval.md` —— 缓存命中率、四类 token、context 优化前后的质量回归门控。
- **心智模型**:`../1.md` —— «成本/单位经济学横切线»(L3 控 token+缓存)、「先量化再优化」、「确定性优先 / 有界状态机」(给 agent 步数上限防膨胀失控)。
- **本系列相邻章**:**04 · 多层 Memory + 全链路 trace**(记忆的分层存储/检索归 04,本章只谈 Memory Tool 的省窗口角度);职责 3 的另一半「全链路 trace 落库」与本章「工具结果另存 trace、context 里可清」呼应。
- **精确数字/字段权威源**:`skills/claude-api`(`prompt-caching` / `context-editing` / 内存工具 / `count_tokens`)或 platform.claude.com —— 所有标「现查官网」的 TTL、折扣倍率、最小可缓存 token、beta header 与策略类型名,以当下查到的为准,**不固化本快照**。

> 最后核对:2026-06。沉淀:在某 feature 定下 context 优化方案(断点布局 / 清理阈值 / TTL)后,用 `agent/skills/adr-writer` 写 ADR 记录取舍。
