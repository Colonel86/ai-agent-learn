# 02 · 带鉴权的工具调用网关 · 工具契约 · 端云协同

> **一句话定位**:在「概率性的模型」和「确定性的真实世界副作用」之间,插一层**确定性边界**——统一鉴权、校验、限流、幂等、审计、危险拦截,并把同一份工具契约跑到端/云两侧。
> **对应 JD**:职责 2「开发**带鉴权的工具调用网关**与**工具契约**、MCP Gateway,**打通端云协同接口**」(本章只负责网关/契约/端云;MCP 作为接入标准归本系列 **03 章**,越权拦截/HITL 闸口的安全策略本体归 **07 章**,本章只讲网关怎么"挂"这些策略)。
> **结论分级**:✅ 稳定经验 / ⚠️ 2026-06 快照(易变,现查官网)/ ❓ 待验证。

---

## 1. 技术原理(网关到底拦在哪、拦什么)

### 1.1 先把"契约"和"网关"分清——它们是两件事

| | 工具契约(tool contract) | 工具网关(tool gateway) |
|---|---|---|
| 是什么 | **数据/声明**:工具长什么样、需要什么权限、有没有副作用 | **执行点/代码**:每次调用流经的一串确定性拦截器 |
| 给谁看 | 一半给**模型**看(name/description/params),一半给**网关**看(scopes/副作用/危险级) | 不给模型看,是后端基础设施 |
| 失败后果 | 描述写差 → 模型**选错工具、传错参**(静默错) | 缺一段 → 越权/重复扣费/泄露凭证(真实事故) |

核心心智:**契约是模型与工程之间的接口(对应 ../1.md L1 底层契约),网关是这个接口的强制执行机关。** 没有契约,网关不知道该拦什么;没有网关,契约只是一份"君子协定",模型一旦概率性跑偏就没人兜底。

### 1.2 工具契约:`name/description/JSON-Schema` 就是 prompt

模型**只知道契约告诉它的东西**。function calling 的机制是:你把每个工具的 `name`、`description`、参数 `JSON-Schema` 拼进请求,模型被训练成在该用工具时吐出一段结构化 `tool_call`(工具名 + 符合 schema 的 args),executor 执行后把结果回喂。所以:

- **description 写不好 = prompt 写不好**:模型靠它判断"这个查询该不该用这个工具"。两个语义重叠的工具(如 `token-price` vs `token-kline`)描述含糊,模型就会选错(✅,详见 ../1.md L1、../../roadmap/agent-selection/4-tools.md)。
- **参数 JSON-Schema 既是给模型的约束,也是给网关的校验源**:同一份 schema,模型侧用约束解码/strict 模式保证"吐出来的 args 合法",网关侧用它做服务端二次校验(模型可能在没开 strict 的 provider 上漂)。
- **契约里还有一组"模型看不到"的治理字段**:`scopes`(调它需要什么权限)、`side_effect`(无副作用/幂等/非幂等)、`danger_level`(要不要 HITL)、`runtime`(端/云)、`version`、`owner`。这组字段是网关工作的依据——**把"给模型看的"和"给网关看的"放进同一份契约、但分开消费**,是这层最重要的设计。

### 1.3 工具网关:一次调用的生命周期(请求 → 执行 → 回喂)

为什么非要在 agent 和真实工具之间加一层?因为模型输出是**概率的**(../1.md L0),而鉴权、限流、危险拦截、幂等必须是**确定性的**——你不能把"请不要越权""请别超预算"写进 prompt 指望模型自觉(那是 prompt,不是边界)。网关就是把这些确定性关注点**从每个工具实现里收口到一处**:

```
模型(概率) ──tool_call JSON──►【工具网关:确定性边界】──► 真实工具(DB/API/端侧)
  name + args                    │                          凭证在这里"服务端注入"
   ▲                             ├─① authN  你是谁?(身份来自 token/mTLS,不来自 prompt)
   │                             ├─② authZ  你能调"这个"工具吗?(per-tool RBAC + scope)
   │                             ├─③ 校验   args 合 JSON-Schema 吗?(schema 级 + 去未知字段)
   │                             ├─④ 策略闸 危险动作?→挂 HITL 闸(策略本体见 07 章)
   │                             ├─⑤ 限流   配额 + token 预算硬限(超限即拒)
   │                             ├─⑥ 幂等   非幂等工具防重(idempotency key)
   │                             ├─⑦ 执行   超时/重试/熔断/降级 + 注入凭证 + 端云路由
   └──结构化结果 / 结构化错误◄─────┴─⑧ 审计   全程一个 span 落库(脱敏后)
      (错误当数据回喂模型,不抛异常)
```

几个机制要点,经得起追问:

- **凭证不进 prompt(第 ⑦ 步才注入)**:模型只传**逻辑参数**(`account_id="A123"`),真实凭证(API key / OAuth token)由网关在执行阶段按调用方身份**服务端注入**。因为 context 里的任何东西都可能被 prompt 注入诱导泄露、被 trace 原样记录、被下游 echo——凭证一旦进窗口,blast radius 就不可控。
- **授权 ≠ 凭证**:authZ(第 ② 步)是"判断这个 caller 有没有这些 scope"的决策;凭证注入(第 ⑦ 步)是"拿哪把钥匙去开门"的执行。两者分开,授权可以纯靠 caller 身份 + 契约 scopes 算,不碰密钥。
- **错误当数据,不当异常**(../1.md L1):网关内部用 typed error 短路链路,但回喂给模型时要转成**结构化错误**(如 `{"error":"rate_limited","retry_after_ms":1200}`),让 agent 能推理降级——且**必须脱敏**,别把内部 scope/拓扑/凭证提示原样吐回去(那本身是注入面/信息泄露)。
- **审计装在最外层**:`audit` 中间件包住整链,start+end 都记,这样被前面任何一段短路(authZ 失败、限流拒绝)也有留痕。

### 1.4 鉴权:每工具粒度 + 短期下放凭证

- **每工具粒度授权**:RBAC 的主体是**调用方身份**(哪个 agent / 哪个 run / 代表哪个终端用户),客体是**单个工具**。每个工具在契约里声明所需 `scopes`,网关在 authZ 阶段做交集判断。这天然实现了 ../../roadmap/agent-selection/7-safety-guardrails.md 的「工具白名单 + 最小权限」——一个 agent 只拿到它该有的工具子集。
- **scoped / 短期凭证**:别给工具全权 long-lived key。用 OAuth 2.0 **Token Exchange(RFC 8693)** 把用户授权的 token 换成一个**降权 + 限定 audience + 几分钟过期**的下放 token 再注入;资源定向可配 **Resource Indicators(RFC 8707)**(✅ RFC 稳定;具体到 MCP 的 HTTP 鉴权走 OAuth 2.1 方向,⚠️ 演进中,现查官网,细节见 03 章)。
- **下放(delegation)的意义**:即使某次调用的下放 token 泄露,它也只够调这一个工具、这一个资源、活几分钟——把"凭证泄露"的损失从"全盘"压到"一次一工具"。

### 1.5 端云协同:同一份契约,两侧执行

JD 要"打通端云协同接口"。架构上的关键不是"端做什么云做什么"的清单,而是**让模型不关心工具在哪执行**:

- **同一份契约(同一 JSON-Schema)在端/云两侧都成立**,模型吐的 `tool_call` 形状一致,网关按 `contract.runtime` + 运行时策略**路由**到端或云。
- **一致性靠幂等 + 对账**:端侧离线时把调用塞进 **outbox 队列**,联网后带 **idempotency key** 重放到云,云是审计 source of truth。这样"端侧先执行、云侧后对账"不会重复扣费。
- **接口契约 = 端 agent ↔ 云网关之间的协议**:可走 MCP-over-HTTP(见 03)或自定义 RPC;端侧实时热路径(低延迟、无 GC 停顿、资源受限设备)常用 **Rust** 写网关代理/工具执行器(JD 加分项,⚠️ 具体栈现查)。

---

## 2. 应用场景(什么时候必须用 / 什么时候是过度工程)

**🎯 甜区(独立网关明确值回票价)**
- 工具**有副作用**(写库/转账/下单/发消息)且会重试 → 必须有幂等 + 危险闸。
- **多 agent / 多租户共享同一批工具** → 网关是唯一治理点,否则鉴权/限流逻辑在 N 个 agent 里复制 N 份、漏 N 次。
- **100+ 工具**:网关在 authZ 阶段按 scope 先砍掉"这个 agent 根本无权调的工具",既是安全也天然收窄路由候选集(路由本体见 4-tools.md)。
- **受监管 / PII / 端云混合**:需要统一审计留痕、统一凭证治理、端云路由。

**🚫 反模式(过度工程的信号)**
- 单个**只读**工具的原型 / 内部单用户 demo → 框架原生 tool 装饰器 + Pydantic 校验入参就够,**别为它起一个独立网关服务**多付一跳延迟和运维。
- 把网关当"万能拦截器"什么逻辑都往里塞 → 它该只做横切关注点(authN/Z、限流、幂等、审计),业务逻辑留在工具里。

**💸 隐藏成本**
- 独立网关 = **多一跳延迟**(内网 ~1-5ms,可接受;但它在每次工具调用的热路径上)+ **潜在 SPOF**(见第 6 节治法)。
- **契约 registry 要长期维护**:版本治理、弃用窗口、owner 责任田——这是技术债的常发地。
- **误拒成本**:限流/校验过严会把正常调用挡掉(对应护栏的 false positive,见 7-safety-guardrails.md §三)。

> 判断口径:**先问"能不能先不做"**。能用框架原生 + 入参校验解决的原型,别上独立网关——和 ../1.md「确定性优先」「最轻起步」一脉相承。网关每加一段拦截,都要能说出它挡的是哪条具体风险。

---

## 3. 具体实现方案(最轻起步 → 升级路径)

### 3.1 升级阶梯

```
L0 原型      框架原生 tool 装饰器,直接调用 + Pydantic 校验入参。无网关。       ~0 延迟
   │  ← 单 agent、少量只读工具到这就够
L1 要治理     in-process 中间件链(本节伪码):authN(进程内可信)→ authZ(白名单)
   │          → schema 校验 → 审计日志。同进程。                              ~0 额外跳
L2 多租户     抽成独立网关服务(sidecar 或中心服务):+ RBAC + scoped 凭证注入
   │          + 限流/token 预算 + 幂等 store + 分布式 trace。                  +1 跳 ~1-5ms
L3 跨厂商/端云 网关说 MCP(见 03)+ 端云路由 + outbox 对账;端侧热路径上 Rust。
```

### 3.2 工具契约数据结构(Python / Pydantic)

```python
from enum import Enum
from pydantic import BaseModel

class SideEffect(str, Enum):
    NONE           = "none"            # 纯读,无副作用
    IDEMPOTENT     = "idempotent"      # 可重复执行结果一致(PUT/DELETE 语义)
    NON_IDEMPOTENT = "non_idempotent"  # 重复执行有害(转账/下单)——重试要靠幂等键

class ToolContract(BaseModel):
    # ---- 给模型看的(拼进 prompt,就是 function calling 的工具定义)----
    name: str                 # 稳定标识,版本化的一部分
    description: str          # 这是 prompt:写清"什么时候用、和谁区分"
    parameters: dict          # JSON-Schema:模型 args 契约 + 网关校验源

    # ---- 给网关看的(模型看不到)----
    version: str              # semver,如 "1.2.0"
    scopes: list[str]         # 调用此工具需要的权限 scope(authZ 用)
    side_effect: SideEffect = SideEffect.NONE
    danger_level: int = 0     # 0 安全 / 1 需审计 / 2 需 HITL 审批(挂闸,策略见 07)
    timeout_ms: int = 5000
    max_retries: int = 0      # 非幂等工具默认 0,绝不盲重试
    runtime: str = "cloud"    # "cloud" / "edge" / "either" —— 端云路由依据
    owner: str = ""           # 责任团队,审计与下线用
    deprecated: bool = False  # 弃用窗口期标记
```

### 3.3 网关中间件链(authN→authZ→校验→闸→限流→幂等→执行→审计)

```python
from dataclasses import dataclass
from typing import Awaitable, Callable
import jsonschema

@dataclass
class ToolCall:
    tool: str
    args: dict
    version: str | None       # None = 取该工具当前活跃版本
    raw_credential: object    # caller 的 token/mTLS 上下文(身份来自这里,不来自 prompt)
    request_id: str           # 幂等键的一部分
    caller: "Identity | None" = None   # authN 填充

class ToolError(Exception):           code = "tool_error"
class AuthnError(ToolError):          code = "unauthenticated"
class AuthzError(ToolError):          code = "forbidden"
class ValidationError(ToolError):     code = "invalid_args"
class RateLimited(ToolError):         code = "rate_limited"
class BudgetExceeded(ToolError):      code = "budget_exceeded"

Next = Callable[[ToolCall], Awaitable["ToolResult"]]

async def audit(call: ToolCall, nxt: Next):           # 装在最外层,包住整链
    span = tracer.start_span("tool.call", tool=call.tool, req=call.request_id)
    try:
        res = await nxt(call); span.ok(res); return res
    except ToolError as e:
        span.error(e.code); raise                     # 失败也有 span
    finally:
        audit_log.write(call, span, redact=True)      # 脱敏后落库

async def authn(call, nxt):
    call.caller = identity.verify(call.raw_credential)  # 失败抛 AuthnError,短路整链
    return await nxt(call)

async def authz(call, nxt):
    c = registry.resolve(call.tool, call.version)        # 多版本并存:按 (name,version) 解析
    if not rbac.has_scopes(call.caller, c.scopes):
        raise AuthzError(f"{call.caller.id} lacks {c.scopes}")
    return await nxt(call)

async def validate(call, nxt):
    c = registry.resolve(call.tool, call.version)
    jsonschema.validate(call.args, c.parameters)         # schema 级校验(模型可能没开 strict)
    call.args = strip_unknown(call.args, c.parameters)   # 去未知字段,防越权塞参
    return await nxt(call)

async def policy_gate(call, nxt):                        # 危险动作只在这里"挂"闸
    c = registry.resolve(call.tool, call.version)
    if c.danger_level >= 2:
        await require_human_approval(call)               # interrupt 闸,审批策略见 07 章
    return await nxt(call)

async def limit(call, nxt):
    if not limiter.allow(call.caller, call.tool):        # 配额
        raise RateLimited(call.tool)
    if not budget.charge(call.caller, estimate_cost(call)):  # token 预算硬限
        raise BudgetExceeded(call.caller.id)
    return await nxt(call)

async def execute(call, nxt):                            # 终端:不再调 nxt
    c = registry.resolve(call.tool, call.version)
    key = idempotency_key(call)                          # = caller + tool + request_id + args 摘要
    if c.side_effect == SideEffect.NON_IDEMPOTENT:
        if (cached := idem_store.get(key)) is not None:
            return cached                                # 防重:命中直接返回上次结果
    cred = secrets.lease(call.caller, c)                 # 短期 scoped 凭证,服务端注入
    target = route_runtime(c, call)                      # 端/云路由
    res = await call_with_timeout_retry(target, c, call.args, cred)  # 超时/重试/熔断/降级
    if c.side_effect == SideEffect.NON_IDEMPOTENT:
        idem_store.put(key, res, ttl=...)
    return res

def compose(chain):
    async def dispatch(call):
        async def run(i, c):
            if i == len(chain):
                raise RuntimeError("chain reached end without terminal")
            return await chain[i](c, lambda cc: run(i + 1, cc))
        return await run(0, call)
    return dispatch

# 顺序即语义:authN 在最前,execute 在最后,audit 包住一切
gateway = compose([audit, authn, authz, validate, policy_gate, limit, execute])
```

> **TS 一行版心智**:在 TS 里同样的链就是 `koa/express` 式 `(ctx, next) => {...; await next(); ...}` 洋葱模型——概念完全一致,选 Python 还是 TS 看 agent 主体语言(JD 要求两者皆通)。

**关于顺序的取舍(面试会追)**:JD 给的基线是 `authN→authZ→校验→限流→执行→审计`。生产里**限流常被前移到 authZ 之前**——身份校验后就先挡掉超额请求,省下后面 schema 校验的开销;代价是会限流掉一个本来就会 authZ 失败的请求(无所谓)。但**authN 必须最先**(不知道你是谁就谈不上其它),**审计必须最外**(任何短路都要留痕),**execute 必须最后**。这是有约束的排序,不是随意。

---

## 4. 架构师取舍判断(主选 vs 备选 vs 代价)

### 4.1 网关形态选型

| 方案 | 形态 | 甜区 | 代价 |
|---|---|---|---|
| **框架原生 tool wrapper** | LangChain/LangGraph 装饰器 | 原型、单 agent | 鉴权/限流/审计要塞进每个 tool,易漏;无统一治理点 |
| **in-process 中间件链** ⭐起步 | 进程内函数链(本章伪码) | 单体 agent、想最快拿到治理 | 跨语言/跨服务复用难;随 agent 进程一起挂 |
| **out-of-process Gateway** ⭐主选 | 独立服务 / sidecar | 多 agent、多租户、要独立扩缩 + 统一审计 | +1 跳延迟、运维成本、可能 SPOF |
| **MCP Gateway** | 说 MCP 协议的网关 | 工具要被多 client/框架/跨厂商复用 | MCP 鉴权/治理仍演进(现查);协议细节见 03 |
| **复用通用 API Gateway**(Kong/Envoy/APISIX) | HTTP 层网关 | 已有 API 网关基建、工具就是 HTTP API | **不懂 agent 语义**(工具契约/幂等/token 预算/危险 HITL),要写插件补 |

> **关键判断**:通用 API Gateway 解决的是 **HTTP 层治理**(L7 限流/authN/可观测),但它不理解"工具契约""副作用幂等""token 预算""危险动作 HITL"这些 **agent 语义**。所以常见落地不是二选一,而是 **"API Gateway 兜底网络层 + 一薄层 agent-aware 网关补语义"**。把这点说出来,面试官会知道你分得清"网络网关"和"工具网关"。

### 4.2 选型轴

```
要不要独立网关服务?
├─ 单 agent + 少量只读工具? ───────────────► 不要,in-process 中间件链够(L1)
├─ 多 agent/多租户 共享工具 + 有副作用? ────► 要,独立 Gateway(L2)
└─ 工具要跨框架/跨厂商/端云复用? ──────────► 网关说 MCP(L3,见 03)+ 端云路由

凭证怎么给?
├─ 内部可信、低敏感? ──────────────────────► 网关持 long-lived key,服务端注入
└─ 代表终端用户/受监管/blast radius 大? ───► OAuth Token Exchange 换短期下放 token

端还是云?(contract.runtime="either" 时)
├─ 强隐私(PII 不出端)/ 离线 / 延迟敏感? ──► 端(端侧执行,云只收审计回执)
└─ 重算力 / 统一治理 / 共享状态? ──────────► 云
```

---

## 5. 面试高频问答(背诵级)

**Q1. 框架已经能调用工具了,为什么还要在中间加一层网关?**
- 框架的 tool wrapper 解决的是"模型能调到工具";网关解决的是"这次调用**安全、可控、可审计、可复用**"。
- **确定性边界**:鉴权/限流/危险拦截必须是确定性代码,不能写进 prompt 让模型自觉(模型概率不可靠,../1.md L0)。
- **横切收口**:authN/Z、限流、审计、幂等若塞进每个 tool 实现,N 个工具漏 N 次;网关收成一处。
- **可观测**:每次调用一个 span,成本/延迟/错误率统一埋点。
- **面试官可能追问:那是不是所有项目都该上独立网关服务?** → 不是。单 agent 少量只读工具,in-process 中间件链就够;独立服务是为多 agent/多租户/独立扩缩才付那 ~1-5ms 一跳和运维成本的。判断口径是"先问能不能先不做"。

**Q2. 怎么做每工具粒度的鉴权,又不把凭证泄露给模型?**
- **授权和凭证分开**:授权决策按 caller 身份做 RBAC,每个工具声明所需 scopes,网关在 authZ 阶段算交集;真实凭证由网关在**执行阶段服务端注入**,模型只传逻辑参数(`account_id` 而非 token)。
- **凭证绝不进 context**:context 里任何东西都可能被 prompt 注入诱导泄露、被 trace 记录、被下游 echo。
- **短期下放**:用 OAuth Token Exchange(RFC 8693)换降权 + 限 audience + 几分钟过期的 token,泄露了 blast radius 也小。
- **面试官可能追问:OAuth 在这里具体怎么接?** → caller 持用户授权 token,网关换成"只够调这个工具、只在这个资源 audience、几分钟过期"的下放 token 再注入;MCP 的 HTTP 鉴权也走 OAuth 2.1 方向(⚠️ 现查官网)。

**Q3. 工具契约怎么做版本化和向后兼容?**
- `name + version`(semver)。description / parameters 改了就是契约变更。
- **兼容规则**(类比 API/protobuf):加可选字段=兼容;删字段/改类型/可选变必填=**破坏性**,必须升 major + 老版本**并行供给**一段弃用窗口(双跑)。
- **模型侧特有风险**:改 description 会改变模型**选择行为**——契约变更必须进 **eval 回归**(横切带 B),不是只测代码就完事。
- **面试官可能追问:线上同时有调老版本的 agent 怎么办?** → registry 按 `(name, version)` 解析,网关支持多版本并存 + deprecation window:老版本打 deprecated 标记、监控调用量降到 0 再下线。

**Q4. 副作用工具 + 重试,怎么不重复扣费/下单?**
- **幂等键**:caller 生成 idempotency key(request_id/业务键),网关执行前查 idem store,命中直接返回上次结果。
- 契约里 `side_effect=non_idempotent` 的工具 `max_retries` 默认 0;只在"明确可安全重试"的错误上重试,而那很难判定,所以保守。
- 关联 **HITL 坑**(../1.md L2):节点从头重跑会重复执行 interrupt 之前的副作用,所以副作用要放闸之后 + 幂等兜底。
- **面试官可能追问:超时了到底重不重试?** → 超时是"不知道成没成"的状态。要么工具端支持幂等键能安全重试,要么走**对账(reconcile)**而非盲重试。默认非幂等不自动重试。
- **面试官可能追问:两个并发的重复请求(同一 idempotency key 同时到)会不会都执行?** → 会——§3.3 的 `execute` 是"查 store→执行→写 store",存在 TOCTOU 窗口:两个并发请求都 miss、都执行,扣两次费。光"查完再写"挡不住并发重复。生产要把幂等 store 当**并发锁**:执行前用唯一约束**原子插入一条 `pending` 占位**(`INSERT ... ON CONFLICT`),抢到的执行并回填结果,没抢到的等结果或返回 409;这才是 Stripe 式 Idempotency-Key 的完整语义(键既防重放也防并发)。

**Q5. 端云怎么分工?路由怎么决策?一致性怎么保?**
- 四个轴:延迟 SLO、数据敏感度(PII 不出端)、离线需求、算力需求。端侧=低延迟/隐私/离线/本地资源/小模型;云侧=重算力/统一治理/共享态/贵工具。
- **一致性**:两侧同一份契约(同一 JSON-Schema),模型不关心在哪执行;端侧离线用 outbox 队列 + 幂等键,联网后与云对账,云是审计 source of truth。
- 数字感:内网网关一跳 ~1-5ms;跨端云公网一来回几十~上百 ms,所以延迟敏感/离线放端侧。
- **面试官可能追问:Rust 在这条链路里干嘛?** → 端侧实时热路径(低延迟、无 GC 停顿、塞进资源受限设备)常用 Rust 写网关代理/工具执行器(JD 加分项,⚠️ 具体栈现查)。

**Q6. 100+ 工具时,网关怎么帮模型选对工具?**
- 这是**工具路由**问题,正交于鉴权治理。全塞进 prompt 会 token 浪费 + 注意力稀释 + 准确率下降(经验 ~10-20 工具上限,../1.md L1)。
- 三阶段:embedding 粗筛 → cross-encoder rerank → LLM 最终选;或 Anthropic Tool Search / `defer_loading` 按需加载(⚠️ 2026-06 快照:省 ~85% token、Opus 工具选择准确率 49%→74%,现查官网)。详见 ../../roadmap/agent-selection/4-tools.md。
- **网关的角色**:在 authZ 阶段先按 caller 的 scope 砍掉"这个 agent 无权调的工具"——既是安全,也天然把路由候选集收窄。

**Q7. 怎么在网关上挂 token 预算硬限和危险动作拦截?**
- **token 预算**:每个 caller/run 维护预算计数器,执行前估算并 charge,超限**直接拒**(硬限),返回结构化错误让 agent 降级(换便宜模型/减步数)。
- **危险动作**:`danger_level` 过阈值时 `policy_gate` 触发 HITL interrupt(技术上 `interrupt + Command(resume)`,../1.md HITL),人批准后才进 execute。**网关只负责"挂"这个闸,审批策略/UX 在 07/10 章**。
- **面试官可能追问:为什么不让模型自己遵守预算/不调危险工具?** → 模型概率不可靠(../1.md L0),"请别超预算"是 prompt 不是边界。硬限必须是确定性代码 + 网关强制,这正是"确定性优先"横切。

**Q8. 网关会不会成为 SPOF / 瓶颈?**
- 会,这是独立网关的隐藏成本。治法:**无状态横向扩**(鉴权/限流状态外置到 Redis)、幂等 store 与审计**异步写**、**熔断降级**让单工具故障不拖垮全网关、本地缓存契约 registry。
- 代价是**最终一致**(限流/审计可能有微小窗口)——这是用一致性换可用性的明确取舍。

---

## 6. 踩坑 / 反模式(选错信号 + 治法)

| # | 反模式 | 选错的典型信号 | 治法 |
|---|---|---|---|
| 1 | **凭证进 prompt / 写进工具 description** | trace 里能看到 API key;"用 key=xxx 调用"出现在 context | 服务端注入,凭证 keyed by 身份,绝不进窗口(§1.3) |
| 2 | **对非幂等工具开自动重试** | 重复下单/扣费工单 | 幂等键 + 默认 `max_retries=0`;超时走对账不盲重试 |
| 3 | **把鉴权写进系统 prompt**("你只能调 A/B") | 注入一句话就越权 | 确定性 authZ(RBAC + scope),prompt 不是边界 |
| 4 | **工具 description 含糊 / 语义重叠** | 模型选错工具、传错参(静默错) | description 即 prompt,写清触发条件 + 区分点 + 进 eval 回归 |
| 5 | **端云 schema 漂移** | 同一工具端云行为不一致 | 契约单一来源(registry 生成两端 stub),禁手维护两份 |
| 6 | **错误原样回喂模型** | 错误信息泄露内部拓扑/scope/凭证提示,成注入面 | 错误脱敏 + 结构化错误码(可参考 RFC 9457 problem details,2023 起取代 RFC 7807) |
| 7 | **限流/预算只"软提示"模型** | 模型无视提示继续烧 token | 硬限:超额直接拒 + 返回结构化错误让 agent 降级 |
| 8 | **契约不版本化,直接改线上** | 老 agent 突然选错/崩 | semver + 多版本并存 + 弃用窗口 |
| 9 | **网关变成 SPOF** | 网关一挂全停;扩缩困难 | 无状态横向扩,状态外置,异步审计,熔断降级(Q8) |
| 10 | **什么逻辑都往网关塞** | 网关里出现业务逻辑、难维护 | 网关只做横切关注点,业务留在工具里 |

> 共性根因:把本该**确定性强制**的边界(鉴权/预算/幂等)交给**概率模型**去"自觉"。网关存在的全部意义,就是把这些不确定性**吸收在它溢出之前**(对齐 7-safety-guardrails.md §一「在确定性边界上设闸」)。

---

## 7. 回链已有资产 / 课程

- **选型矩阵 · 工具层**:[`../../roadmap/agent-selection/4-tools.md`](../../roadmap/agent-selection/4-tools.md) —— 100+ 工具的**路由/检索**(Q6 交叉引用):Tool2Vec 粗筛 → cross-encoder rerank → LLM 选择;Anthropic Tool Search/`defer_loading`。本章的网关只在 authZ 阶段做"按 scope 收窄候选",真正的选对靠那篇。
- **选型矩阵 · 护栏**:[`../../roadmap/agent-selection/7-safety-guardrails.md`](../../roadmap/agent-selection/7-safety-guardrails.md) —— ③「工具权限边界」(白名单 + 最小权限凭证 + 危险操作 HITL + 副作用幂等)。**本章网关 = 这层护栏的执行点**:护栏说"该挡什么",网关说"在哪一步、用什么机制挡"。
- **心智模型(权威)**:[`../1.md`](../1.md) —— L0 概率底座、L1 底层契约(工具 description=prompt、错误当数据、副作用幂等)、L5 部署/安全(工具权限边界、限流降级)、**HITL 横切**(危险动作审批=`interrupt + Command(resume)`)、**确定性优先横切**(硬限/鉴权必须确定性)、《前后端 stream》§7(错误脱敏 / JSON Patch 注入面 RFC 6902)。
- **同系列**:**03 章**(MCP server/client 作为**工具接入标准** + MCP Gateway 协议细节)、**07 章**(越权拦截 / HITL 闸口的**安全策略本体** + token 预算/人审策略)。本章与它们的分界:**网关是"执行点",03 给"接入协议",07 给"策略内容"**。

> **最后核对:2026-06**。易变项(MCP OAuth 2.1 鉴权形态、Anthropic Tool Search 的省 token/准确率数字、Rust 端侧栈)定型前**现查官方**,本章只给机制与分界,不固化产品快照。
