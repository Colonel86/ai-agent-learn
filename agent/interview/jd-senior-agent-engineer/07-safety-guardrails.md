# 07 · 安全护栏:重试/fallback · token 预算硬限 · 越权拦截 · 人审闸口

> 一句话定位:**护栏是"在确定性边界上设闸",把概率模型的不可控性吸收在它溢出成真实事故之前**——四个闸分别管"调用失败别雪崩""花钱别失控""动作别越权""高危动作过人手"。
> 对应 JD:**职责 4**(实现安全护栏:失败重试与 fallback、token 预算硬限、越权工具拦截、人审闸口)。是这条职责的**主页**;工具网关本体见本系列 02,HITL 的 trace 表现见本系列 06,本章只讲"在网关执行点上挂什么安全策略"。
>
> 结论分级:✅ 稳定经验 / ⚠️ 2026-06 快照(易变)/ ❓ 待验证。具体状态码/价格/SDK 字段变化快,事实性论断就近标 **(现查官网)**。

---

## 1. 技术原理(四个闸 + 一条中间件链)

先给统一视图:**这四件事不是四个孤立功能,而是工具调用路径上串起来的一条护栏中间件链**,落在工具网关(02)的执行点上。

```
模型发起 tool_call
   │
   ▼
┌──────────────────────── 护栏中间件链(网关执行点)────────────────────────┐
│ ① budget_check   token/$ 预算够不够 → 触顶即拒/降级                        │
│ ② policy_check   工具在 allowlist? RBAC 角色有权? → 越权即拒              │
│ ③ param_policy   参数级策略(rm -rf? amount>阈值? DROP without WHERE?)   │
│ ④ hitl_gate      命中高危分级 → interrupt 暂停,等人审(默认拒绝)          │
│ ⑤ exec_wrapper   重试/退避/抖动 + circuit breaker,区分可重试/不可重试      │
│ ⑥ audit_log      谁、何时、改了什么、批没批 → 审计留痕                      │
└──────────────────────────────────────────────────────────────────────────┘
   │
   ▼
真正执行(scoped 凭证 / 沙箱)
```

> 核心心智(对齐 `../1.md` L5「自主性 vs 可控性」):**①~④ 是"不信任模型自律"的确定性闸**,放在网关而不是 system prompt 里;⑤ 是"不信任下游可用性"的容错闸;⑥ 让前五个可追溯。下面逐闸讲机制。

### A. 失败重试 & fallback(不信任下游可用性)

**第一性问题:这个错误到底该不该重试。** 盲目重试既烧 token 又放大故障,所以先分类:

| 类别 | 典型 | 该重试? | 处理 |
|---|---|---|---|
| 瞬时可重试 | 429(限流)、500/502/503/504、**529 overloaded**(Anthropic 过载,现查)、408 超时、连接重置 | ✅ 退避重试 | 指数退避 + 抖动;**429/503 尊重 `Retry-After` 头** |
| 客户端错误 | 400 参数错、401 鉴权、403 越权、404 | ❌ 不可重试 | 重试也一样,直接失败/告警,修请求 |
| 内容/语义拒绝 | content filter、模型 refusal、context length exceeded | ❌ 不是"瞬时"故障 | 同输入→同结果;要变就改输入(属"reask",见下) |
| schema 校验失败 | 输出不符合 Pydantic/JSON Schema | ⚠️ **reask 重试**(另一类) | 把校验错误回喂模型改写(instructor/trustcall 套路),≠ 退避重试 |

> ✅ 两类"重试"别混:**瞬时退避重试**(网络/限流,换个时间再打同一份请求)和 **reask 重试**(输出不合格,带错误改写后再生成)。前者幂等、后者每次 prompt 都变。

**退避算法机制.** `delay = min(cap, base * 2^attempt)` 再叠**抖动 jitter**。抖动不是可选项——没有抖动时,一批请求被同一次限流打回,会在同一时刻一起重试(thundering herd 惊群),把刚恢复的 provider 再打垮。常用 **full jitter**(`random(0, base*2^n)`)或 decorrelated jitter(AWS 架构经验,✅ 稳定)。配 `max_attempts` + retry budget,别无限重。

**幂等是重试的前提.** ⚠️ 这是最容易翻车的点:**对有副作用的动作(转账、写库、发消息)重试,会重复执行**。两道保险:
- **工具侧幂等键**:写操作带 `idempotency_key`(任务 id + 动作指纹),下游用它去重,重复请求返回首次结果而非再执行一次。
- **provider 侧幂等**:OpenAI 支持 `Idempotency-Key` 头防网络重传导致的重复计费;Anthropic 现查。
- 经验法则:**读操作随便重试,写操作必须先有幂等键再谈重试**。这条直接接 `../1.md` L1「副作用管理」与 HITL「节点从头重跑」坑。

**模型/provider fallback(降级保命).** 区分两个方向,别混:
- **fallback = 可用性降级**:主模型/主 provider 5xx 挂了 → 切备用(同模型多通道:Anthropic API ↔ Bedrock ↔ Vertex;或跨模型:Claude → GPT)。目的是**别让一家挂了整条链就死**。
- **cascade = 成本级联**(方向相反,属成本经济学):便宜模型先行,低置信再升级(FrugalGPT,见 `8-cost-economics.md` 阶梯③)。fallback 往"更稳/更贵"走,cascade 往"够用/更便宜"走。
- ⚠️ **跨模型 fallback 不是 try/except 换个 client 这么简单**:prompt 措辞、tool schema 方言、输出格式、停止原因语义都不通用,需要一层 adapter 把请求/响应在两家之间翻译;否则 fallback 触发时静默吐畸形输出。**最稳的 fallback 是同模型多 provider**(schema 一致)。

**断路器 circuit breaker(防雪崩).** 重试解决"偶发抖动",断路器解决"持续性故障"。机制是三态机:

```
        失败率/连续失败 > 阈值
 CLOSED ──────────────────────► OPEN ──(冷却 cooldown 到)──► HALF_OPEN
  正常放行                      快速失败(fail-fast)          放少量探测请求
   ▲                            不再打下游、不再等超时          │
   │                                                          ├─探测成功→ CLOSED
   └──────────────────────────────────────────────────────────┴─探测失败→ OPEN
```

为什么必须有:provider 真挂了时,**没有断路器 = 每个请求都傻等超时(几秒~几十秒)再重试**,会 ① 拖垮你自己的延迟预算 ② 把并发线程池占满 ③ 把 token/$ 预算在无望的重试里烧光。OPEN 态直接 fail-fast 走 fallback,把"等超时"省掉。✅ 稳定。

### B. token 预算硬限(不信任循环会自己停)

预算"硬"在哪——靠**三件套闭环**,缺一就软:

```
① 调用前预估(gate)   count_tokens/tiktoken 估 prompt + 预留 max_tokens 输出
        │                单次就要爆预算 → 直接拒,别打出去
        ▼
② 累计计量(ledger)   每次调用后从 response.usage 取真值,四类 token 分开累加
        │                (input / output / cache_read / cache_write,见 `../1.md` token 统计)
        ▼
③ 触顶即拒/降级(enforce) 累计 ≥ 上限 → 拒新调用 / 降档 / 截 context / 升 HITL
```

- **为什么预估和真值都要**:预估(tiktoken)会系统性少算(漏 chat overhead、tool schema、reasoning tokens),所以**预估只用于 gate(防单次就爆)**,**真值(usage)用于 ledger(防累计漂移)**。把 tiktoken 估算当计费真值是经典坑(见 `../1.md` token 统计「坑 2」)。
- **三个层级**:每任务(防单个 runaway)/ 每会话(防长对话堆积)/ 每用户·每租户(防滥用、控毛利)。可再加全局熔断。
- **挂钩 $/任务**:`token 预算 = ($/任务上限) / 单价`(输出单价≈输入 5×,现查)。预算硬限是 `8-cost-economics.md` 里「$/任务上限」的**执行手段**——成本经济学算出该花多少,这里负责"超了就停"。
- **防 runaway loop 是两道 AND 闸**:`max_steps`(步数上限,防绕圈)**且** token 预算(防即使步数没到、单步狂吐也烧穿)。只设步数不设 token,会被"少数几步但每步塞满 1M context"打穿。
- ⚠️ **并发下要防超卖**:多个任务共享同一 user 预算时,"读余额→判断→扣减"非原子会超卖。用 **reserve/settle 两段式**:pre-flight 按预估**预扣**(Redis 原子 `INCRBY`/Lua),调用后按真值**结算**多退少补。

### C. 越权工具拦截(不信任模型自律)

**架构铁律:策略在网关执行点判定,模型说了不算。** prompt 注入(尤其工具返回/网页里的间接注入)能让模型发起任意越权调用——你**不能**靠 system prompt 写"请不要 rm -rf"来防,注入内容能盖过它。必须在确定性的 gateway 层 enforce。三层粒度:

| 粒度 | 机制 | 例子 |
|---|---|---|
| **工具级** allowlist/RBAC | 每个 agent/role 只暴露需要的工具子集;调用前查 policy | 客服 agent 没有 `delete_db` 工具,根本不在表里 |
| **动作分级** | 只读 / 写 / 不可逆,按级配护栏强度 | 只读放行;写要 scoped 凭证 + 审计;不可逆 + HITL |
| **参数级** policy | 光看工具名不够,要看 args | `bash` 允许但拦 `rm -rf`;`transfer` 允许但 `amount>$1000` 升 HITL;`sql` 放 SELECT 拦 `DROP`/无 WHERE 的 DELETE |

**纵深防御(defense in depth),不靠单点**——挡住注入越权要四层叠加:
1. **策略在网关**(模型请求 ≠ 自动执行,gateway 查 policy 决定)。
2. **危险工具 default-deny + HITL**(白名单外一律拒,不可逆动作过人手)。
3. **工具返回是数据不是指令**(间接注入面;输入侧护栏,交叉引用 `7-safety-guardrails.md` ①输入护栏)。
4. **最小权限 scoped 凭证**(就算调用混过了,凭证本身也没权限做——只读 token 删不了库)。

> 👉 这呼应 `../1.md`「确定性优先」横切:**能用确定性 policy/查表挡的越权,别交给"希望模型乖"**。第 4 层(scoped 凭证)是性价比最高的兜底——它把"判断对不对"降级成"根本做不到"。

### D. 人审闸口 HITL(把人当安全闸)

- **插在哪**:不可逆/大额/对外/越权边界动作**前**;低置信升级;policy 命中"需审批"。原则——**审批前置于副作用**。
- **pause/resume 机制**:LangGraph `interrupt()` 抛 `GraphInterrupt` → checkpointer 存状态快照 → `Command(resume=...)` 喂回人的决定。机制细节(节点从头重跑、副作用必须在 interrupt 之后、多 interrupt 按顺序匹配)`../1.md` 已讲透,这里不重复。生产必须 `PostgresSaver` 而非 `InMemorySaver`,否则进程一重启隔天就接不上。
- **超时与默认值——fail-closed**:✅ 高危动作**默认拒绝**(deny by default),TTL 超时自动拒 + 通知,**绝不能 fail-open**(没人理就自动放行高危)。扫 checkpointer 里 `updated_at` 超 TTL 的 thread 做自动拒绝/重提醒,否则半中断 thread 永久挂着。
- **审计留痕**:每次审批落一条不可变记录 `{approver, action, params_hash, decision, ts, trace_id, state_snapshot_ref}`——合规与复盘都靠它。人既是安全闸,也是数据飞轮的标注来源(`../1.md` HITL 横切)。
- ⚠️ **与 trace 的坑(回链 06)**:`interrupt` 靠抛异常 + 两次 invoke 实现,naive tracing 会把一次人审切成**两条断裂 trace**、把暂停**误标 ERROR**。治法(同 thread_id 缝合 / `GraphInterrupt` 特判 paused / 用框架原生 tracing)在本系列 06 展开。

---

## 2. 应用场景(必须用 / 过度工程)

**甜区(必须上,缺了就是上线事故):**
- 对外、面向不可信用户;或处理不可信内容(网页/上传/工具返回 → 注入面)。
- 能产生副作用、blast radius 大(写库/转账/发消息/删文件/执行代码)。
- 按量付费且对外开放 → token 预算硬限防被刷爆账单。
- 受监管(医疗/金融)→ 审计留痕 + 人审是合规硬要求。
- 多 agent / 长时后台 agent → runaway loop 风险高,token+步数双闸必上。

**反模式(过度工程,先不做):**
- 纯内部、只读、给可信同事用的 demo,上分布式 budget ledger + 多 provider fallback adapter + circuit breaker 全套——维护成本 > 它挡的风险。
- 给只读查询 agent 加 HITL 审批,每条都等人点,体验崩、没必要。
- 为还没有流量的原型预搭跨模型 fallback——`8-cost-economics.md` 的「裸跑测基线再优化」同理:**没真实流量/事故前,护栏也别过度预建**。

**隐藏成本(每加一层护栏都要记账):**
- 每个 LLM 分类器型护栏 = 一次额外调用(延迟 + $ + **又一个注入面**)。
- 重试放大尾延迟(p99 可能是 base × max_attempts);断路器 OPEN 期间正常请求也被 fail-fast(误杀)。
- HITL 把延迟从秒级拉到分钟~小时级,且需要审批 UI + 通知 + TTL 管理一整套基建。

> 决策原则(对齐 `7-safety-guardrails.md` 强度分级):**护栏强度按风险轴定,不是越多越好**。每加一层都要能说出它挡的是哪条具体风险,挡不出就先别加。

---

## 3. 具体实现方案(最轻起步 → 升级)

### 起步路径

```
🟢 最轻(默认底线):工具 allowlist + 危险动作 HITL + 单任务 token/步数上限(进程内计数)
        │  ← 大多数内部能写的 agent 到这就够
🟡 中(对外/按量计费):+ 跨节点退避重试(SDK 内建够用)+ 参数级 policy + Redis 分布式预算 ledger
        │
🔴 重(高 blast radius/受监管/多 provider):+ circuit breaker + 多 provider fallback + 策略引擎(OPA/Cedar)+ 全程审计留痕
```

### 关键数据结构

```python
from dataclasses import dataclass
from enum import Enum

class Risk(Enum):
    READ = "read"            # 只读,放行
    WRITE = "write"          # 写,scoped 凭证 + 审计
    IRREVERSIBLE = "irrev"   # 不可逆,HITL + 二次确认

@dataclass
class ToolPolicy:
    name: str
    risk: Risk
    allowed_roles: set[str]                       # RBAC
    param_rules: list["ParamRule"]                # 参数级策略
    requires_approval: bool = False               # 是否强制人审

@dataclass
class ParamRule:
    # 返回 None=放行, str=拒绝原因, "ESCALATE"=升级到 HITL
    check: "Callable[[dict], str | None]"

@dataclass
class BudgetLedger:
    scope: str          # task:<id> / session:<id> / user:<id>
    limit_tokens: int
    used_tokens: int    # 真值累计(四类合一计费口径)
    reserved: int       # pre-flight 预扣中
```

### 闸 A:重试 + 退避 + 抖动 + 断路器(Python)

```python
import random, time
from anthropic import Anthropic, APIStatusError

RETRYABLE = {408, 429, 500, 502, 503, 504, 529}   # 现查 provider 文档

class CircuitBreaker:
    def __init__(self, fail_threshold=5, cooldown=30):
        self.fail_threshold, self.cooldown = fail_threshold, cooldown
        self.fails, self.opened_at, self.state = 0, 0.0, "CLOSED"

    def allow(self) -> bool:
        if self.state == "OPEN":
            if time.time() - self.opened_at >= self.cooldown:
                self.state = "HALF_OPEN"   # 放探测
                return True
            return False                   # fail-fast,不打下游
        # ⚠️ 简化:HALF_OPEN 期间这里对所有请求都放行,生产应只放 N 个探测
        #    (探测计数 / 信号量),否则冷却一到会"探测风暴"把刚恢复的下游再打垮
        return True

    def record(self, ok: bool):
        if ok:
            self.fails, self.state = 0, "CLOSED"
        else:
            self.fails += 1
            if self.fails >= self.fail_threshold or self.state == "HALF_OPEN":
                self.state, self.opened_at = "OPEN", time.time()

def call_with_guard(client, breaker, max_attempts=4, base=0.5, cap=20, **kw):
    if not breaker.allow():
        raise RuntimeError("circuit OPEN → 走 fallback")   # 交给上层降级
    for attempt in range(max_attempts):
        try:
            resp = client.messages.create(**kw)
            breaker.record(ok=True)
            return resp
        except APIStatusError as e:
            if e.status_code not in RETRYABLE:
                breaker.record(ok=False if e.status_code >= 500 else True)
                raise                                       # 4xx/拒绝:不重试
            breaker.record(ok=False)
            if attempt == max_attempts - 1:
                raise
            # 尊重 Retry-After,否则指数退避 + full jitter
            ra = e.response.headers.get("retry-after")
            delay = float(ra) if ra else random.uniform(0, min(cap, base * 2**attempt))
            time.sleep(delay)
```

> ⚠️ 生产里 **Anthropic/OpenAI 官方 SDK 自带退避重试**(默认 `max_retries`≈2,现查),很多场景直接用 SDK 内建即可——自写主要为了挂 **circuit breaker + fallback 路由**这两件 SDK 不管的事。别重复造退避轮子。

### 闸 B:并发安全的预算硬限(Redis reserve/settle)

```python
import redis
r = redis.Redis()

# pre-flight:原子预扣预估量;超限则整体回滚并拒绝
RESERVE = r.register_script("""
  local used = tonumber(redis.call('HGET', KEYS[1], 'used') or 0)
  local resv = tonumber(redis.call('HGET', KEYS[1], 'reserved') or 0)
  local limit = tonumber(ARGV[2])
  if used + resv + tonumber(ARGV[1]) > limit then return -1 end
  return redis.call('HINCRBY', KEYS[1], 'reserved', ARGV[1])
""")

def guarded_call(scope, est_tokens, limit, do_call):
    if RESERVE(keys=[scope], args=[est_tokens, limit]) == -1:
        raise BudgetExceeded(scope)          # 触顶即拒(或在此降档/截 context)
    try:
        resp = do_call()                     # 实际调用
        real = resp.usage.input_tokens + resp.usage.output_tokens   # 真值结算
        r.eval("redis.call('HINCRBY',KEYS[1],'used',ARGV[1]);"
               "redis.call('HINCRBY',KEYS[1],'reserved',-ARGV[2])",
               1, scope, real, est_tokens)    # used+=真值, reserved 退回预扣
        return resp
    except Exception:
        r.hincrby(scope, "reserved", -est_tokens)   # 失败也要退预扣,否则永久泄漏额度
        raise
```

> 关键:`reserved` 解决并发超卖,`used` 用真值校准漂移。**异常路径一定要退预扣**,否则失败请求会把额度永久"借走"。

### 闸 C+D:策略网关 + HITL(伪码)

```python
def gateway_invoke(tool_call, ctx):
    pol = POLICIES[tool_call.name]
    # ② RBAC / allowlist
    if tool_call.name not in ctx.allowlist or ctx.role not in pol.allowed_roles:
        return deny("tool not permitted for role")        # 越权拦截,模型说了不算
    # ③ 参数级策略
    for rule in pol.param_rules:
        verdict = rule.check(tool_call.args)
        if verdict == "ESCALATE":
            pol = replace(pol, requires_approval=True)     # 如 amount>阈值
        elif verdict:
            return deny(verdict)                           # 如 rm -rf
    # ④ HITL:不可逆 / 命中升级 → interrupt 暂停(机制见 ../1.md)
    if pol.risk is Risk.IRREVERSIBLE or pol.requires_approval:
        decision = interrupt({"action": tool_call.name, "args": tool_call.args})
        if decision != "approve":                          # 超时默认走这里 = 拒绝
            return deny("human rejected / timed out")
    audit_log(ctx, tool_call, "approved")                  # ⑥ 留痕(approval 之后)
    return execute_with_scoped_cred(tool_call, ctx)        # 最小权限凭证执行
```

> 注意顺序:**审计与副作用都在 `interrupt()` 之后**——因为 resume 时节点从头重跑,放前面会重复记录/重复执行(`../1.md` HITL 坑 1)。

---

## 4. 架构师取舍判断

| 闸 | 主选(够用) | 备选(升级) | 代价 / 选型轴 |
|---|---|---|---|
| 重试/退避 | **SDK 内建退避** | tenacity 自定义策略 | 选型轴:要不要挂 breaker/fallback。SDK 够用就别自写 |
| 断路器 | 进程内 `CircuitBreaker` | pybreaker / 服务网格(Envoy) | 单实例够;多实例要共享态(Redis)才不各判各的 |
| 模型 fallback | **同模型多 provider**(schema 一致) | 跨模型 + adapter 层 | 跨模型省钱但要维护翻译层,fallback 触发率低时不值 |
| fallback 编排 | 应用层 router 自写 | LiteLLM / OpenRouter / Portkey 网关 | 网关省事但多一跳延迟 + 黑盒;数据过第三方要评估(现查) |
| 预算计量 | 进程内计数器 | **Redis reserve/settle** / API 网关配额 | 单进程够;并发/多实例必上分布式原子计数 |
| 工具策略 | **硬编码 if + allowlist** | 策略引擎 OPA(Rego)/ Cedar | 规则多、要审计/热更/合规审查才上引擎;否则 if 更透明 |
| 策略判定 | 确定性规则 | ⚠️ LLM judge 判越权 | **慎用 LLM 判安全**:它本身可被注入、会误判、加延迟——安全闸应确定性 |
| HITL pause/resume | **LangGraph interrupt + Postgres** | 自建状态机 + 审批队列 | 用框架别自造;自建只在非 LangGraph 栈或要复杂审批流时 |

> 一条贯穿取舍:**安全闸优先确定性,容错闸优先复用成熟件**。policy/预算/RBAC 用规则不用 LLM;重试/退避用 SDK 不自写;fallback 链能同 provider 就别跨模型。

---

## 5. 面试高频问答(重中之重)

**Q1. 哪些错误该重试、哪些不该?重试时怎么保证不重复扣费?**
- 可重试 = 瞬时:429/500/502/503/504/529/408/超时;不可重试 = 4xx(400/401/403/404)和内容拒绝/refusal/超长——重试也是同结果,白烧 token。
- 退避:`min(cap, base*2^n)` + **jitter**(没抖动会惊群把 provider 二次打垮),429/503 尊重 `Retry-After`。
- 幂等:**写操作必须带 idempotency key**(任务 id + 动作指纹),下游去重;读操作随便重。"先有幂等键,再谈重试"。
- 面试官可能追问:**"schema 校验失败算可重试吗?"** → 答:那是另一类——**reask 重试**(带校验错误改写后重新生成),和瞬时退避重试不是一回事,前者每次 prompt 都变、后者重发同一份。混在一个 retry 装饰器里会出错。

**Q2. 主模型挂了切备用模型,直接 try/except 换个 client 行不行?**
- 不行。跨模型 fallback 要过 adapter:prompt 措辞、tool schema 方言、输出格式、停止原因语义都不通用,裸切会在最需要它时静默吐畸形输出。
- 最稳的 fallback 是**同模型多 provider**(Anthropic API↔Bedrock↔Vertex,schema 一致)。跨模型当最后兜底,且要为备用模型单独跑过 eval。
- 区分 fallback(往更稳/更贵走,保可用)和 cascade(往更便宜走,省钱),方向相反别混。

**Q3. token 预算怎么做到"硬"执行?并发请求共享用户预算时怎么不超卖?**
- 三件套闭环:**调用前预估 gate**(单次就爆直接拒)+ **调用后真值累计 ledger**(usage 四类分开)+ **触顶 enforce**(拒/降档/截 context/升 HITL)。预估只防单次爆,真值防累计漂移——拿 tiktoken 估算当真值是经典错。
- 并发:**reserve/settle 两段式**——Redis 原子预扣预估量,调用后按真值结算多退少补;异常路径必须退预扣否则额度泄漏。
- 面试官可能追问:**"只设步数上限够不够?"** → 不够。runaway 要 `max_steps` **且** token 预算双闸(AND):只设步数会被"少数几步每步塞满 context"打穿;只设 token 会被"无限空转的廉价小步"绕过。

**Q4. prompt 注入让 agent 调 `rm -rf /` 或转账,你在哪一层挡?**
- **不在 system prompt 层**(写"请不要…"会被注入盖过)。在**网关执行点用确定性 policy** 挡:工具级 allowlist + 参数级规则(拦 `rm -rf`、`amount>阈值` 升 HITL)。
- 纵深防御四层:① 策略在网关(模型请求≠执行)② 危险工具 default-deny + HITL ③ 工具返回是数据不是指令(挡间接注入)④ **最小权限 scoped 凭证**——就算前三层都被绕过,只读 token 也删不了库。
- 面试官可能追问:**"那能不能用一个 LLM 来判断这次调用安不安全?"** → 慎用。安全闸应确定性:LLM judge 本身可被同一注入攻破、会误判、加延迟和成本,还多一个注入面。LLM 判好坏属离线 eval(判质量),不该当运行时安全闸(判阻断)——这俩别互相替代。

**Q5. circuit breaker 解决什么?和重试是什么关系?**
- 重试管"偶发抖动",断路器管"持续性故障"。provider 真挂时,没断路器=每个请求傻等超时再重试,拖垮自己延迟、占满线程池、烧光预算。
- 三态:CLOSED 正常 → 失败超阈值转 OPEN(fail-fast 不打下游)→ cooldown 后 HALF_OPEN 放探测 → 成功回 CLOSED、失败再 OPEN。OPEN 期间直接走 fallback。
- 阈值取舍:太敏感→误熔断误杀正常请求;太钝→雪崩照样发生。多实例部署要共享断路器状态(Redis),否则各判各的。
- 面试官可能追问:**"HALF_OPEN 时你放几个探测?"** → 应只放**少量**(常 1 个,用探测计数/信号量限),探测成功才回 CLOSED。若 cooldown 一到就对所有请求放行,会"探测风暴"把刚恢复的下游二次打垮——本质和"重试无抖动惊群"是同一类坑。另一面:OPEN→HALF_OPEN 的 cooldown 用固定值还是带抖动也要想,多实例同时探测同样会撞。

**Q6. HITL 审批一直没人响应怎么办?默认拒绝还是默认放行?**
- **fail-closed:默认拒绝**。高危动作 TTL 超时自动拒 + 通知,绝不 fail-open(没人理就自动执行高危=灾难)。
- 实现:扫 checkpointer 里 `updated_at` 超 TTL 的中断 thread 做自动拒绝/重提醒,否则半中断 thread 永久占用。
- 留痕:`{approver, action, params_hash, decision, ts, trace_id}` 不可变审计记录,合规和复盘都靠它。

**Q7. 重试 + HITL + 副作用三者叠在一起,有什么坑?**
- ① **HITL resume 时节点从头重跑**,副作用(写库/扣费)必须放 `interrupt()` 之后,否则人一批准就重复执行(`../1.md` 坑 1)。
- ② **退避重试遇到带副作用的工具**必须先幂等,否则一次网络抖动重试两次=转两次账。
- ③ 三者交汇处:审批通过 → 执行 → 网络抖动重试,这条路径上幂等键要贯穿"审批后的那一次执行",而不是每次重试生成新 key。

**Q8. 护栏放在哪一层落地?为什么不嵌进 agent 的 prompt/代码里?**
- 放在**工具网关的中间件链**(02 的执行点),作为横切层:budget→policy→param→hitl→retry/breaker→audit 顺序串。
- 不嵌 prompt:模型不可信(概率 + 可被注入),自律不是护栏;不散落进各 agent 业务代码:会漏、不一致、改一处要改 N 处。集中在网关=**单一执行点、可审计、可统一升级**(对齐 `7-safety-guardrails.md`「在确定性边界设闸」)。

---

## 6. 踩坑 / 反模式

| 反模式 | 选错信号 | 治法 |
|---|---|---|
| 对 4xx / 内容拒绝也重试 | 账单上有大量"重试 N 次仍失败"的相同 4xx | 按状态码白名单重试,拒绝/4xx 直接失败 |
| 重试无退避 / 无抖动 | provider 刚恢复就被自己二次打垮、错误率周期性尖峰 | 指数退避 + jitter + 尊重 `Retry-After` |
| 有副作用动作无幂等就重试 | 偶发"重复扣费/重复发消息"投诉,难复现 | 写操作先上 idempotency key,再谈重试 |
| token 预算只预估不校准 / 只后扣不预扣 | 账单超预算上限;并发时偶发超卖 | 预估 gate + 真值 ledger + reserve/settle 原子化 |
| 把安全策略写进 system prompt("请不要…") | 一个间接注入就能让 agent 越权 | 策略移到网关确定性 enforce + scoped 凭证兜底 |
| 只看工具名做 allowlist,不看参数 | `bash`/`sql`/`transfer` 在白名单里就被任意 args 调用 | 加参数级 policy(危险参数/阈值/无 WHERE 拦截) |
| HITL fail-open(超时自动放行) | 半夜无人值守时高危动作自动执行 | 改 fail-closed:超时默认拒 + TTL 扫描 |
| circuit breaker 阈值拍脑袋 | 要么频繁误熔断、要么雪崩时根本没断 | 按真实错误率分布调阈值/cooldown;多实例共享状态 |
| fallback 链无限 / fallback 到更贵模型 | 主模型抖一下,成本/延迟反而暴涨 | fallback 链有界 + 成本上限;优先同 provider 多通道 |
| 安全闸全用 LLM 分类器 | 延迟翻倍、误杀正常请求、又被注入 | 能规则解决的别上概率件(确定性优先);LLM 判好坏归离线 eval |
| 护栏散落各 agent 业务代码 | 同一危险动作在 A agent 拦了 B agent 没拦 | 收敛到网关中间件单一执行点 |

---

## 7. 回链已有资产 / 课程

- **护栏选型主页(横切层)**:[`../../roadmap/agent-selection/7-safety-guardrails.md`](../../roadmap/agent-selection/7-safety-guardrails.md) — 五段护栏链(输入/输出/工具权限/沙箱/红队)、强度按风险轴分级、运行时拦截 vs 发布前红队的边界、候选工具表(NeMo/Llama Guard/Lakera 等,现查归属)。本章是其中「③ 工具权限边界 + 容错/预算」那一段的工程深挖。
- **成本 / 单位经济学**:[`../../roadmap/agent-selection/8-cost-economics.md`](../../roadmap/agent-selection/8-cost-economics.md) — token 预算硬限挂钩「$/任务上限」、熔断(token/步数上限)防重试雪崩烧账单、fallback vs cascade 的成本方向、四类 token 分开计量。
- **心智模型(权威)**:[`../1.md`](../1.md) — «L5 部署/安全运行时»(自主性 vs 可控性、prompt 注入、工具权限、沙箱)、«HITL 横切»(interrupt + Command(resume)、节点从头重跑/副作用顺序/超时设计)、«确定性优先»(能规则解决就别上概率件)、«成本横切»(熔断 + 步数上限)、token 统计(usage 四字段、预估 vs 真值)。
- **本系列同目录**(同 `jd-senior-agent-engineer/` 下,文件名以实际建档为准):
  - **02 工具调用网关 / MCP Gateway** — 护栏中间件链的**执行点**与工具契约本体(本章只讲"在其上挂什么策略")。
  - **06 全链路 trace** — HITL `interrupt` 打断 naive tracing(两条断裂 trace、误标 ERROR)的坑与缝合治法。
- **延伸**:[`../../roadmap/agent-selection/0-action-paradigm.md`](../../roadmap/agent-selection/0-action-paradigm.md)(CodeAct/computer-use → 何时必须沙箱)、[`../../roadmap/agent-selection/5-observability-eval.md`](../../roadmap/agent-selection/5-observability-eval.md)(运行时护栏 vs 离线 eval 的「拦截≠判好坏」分界)。

> 最后核对:2026-06。状态码集合、SDK `max_retries` 默认值、provider fallback 通道、缓存/价格折扣均**易变,定型前现查官网**;本章固化的是闸的机制与落点,不固化产品/数字快照。
