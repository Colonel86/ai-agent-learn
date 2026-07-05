# L3 · 构建第一个护栏：自定义 Validator + Guard + Guardrails Server

> 课程：Safe and reliable AI via guardrails（DeepLearning.AI × GuardrailsAI）
> 本课任务：给披萨店 RAG 客服 chatbot 实现第一个护栏——阻止它提及尚未公开的秘密项目 **Project Colosseum**（防信息泄露），走完 **自定义 Validator → 装进 Guard → 通过 Guardrails Server 接入应用** 的完整链路。

## 0. 本课目标与衔接

L2 讲清了 AI validation 的概念和护栏在应用中的位置：**Input Guard 在用户输入 / 检索文本进入 LLM 之前检查；Output Guard 在 LLM 响应返回之后按验证规则检查**。本课从概念落到代码：写一个最简单的 validator + guard。

```
用户输入 / 检索文本 ──▶ [Input Guard] ──▶ LLM ──▶ [Output Guard] ──▶ 响应
                        进 LLM 前拦                 出 LLM 后拦
```

Setup 与前课相同：忽略 warnings、导入 OpenAI 作 LLM client、导入 RAG chatbot 与 vector database 的 helper 函数。讲师顺带强调全程用 **type hints**——保证代码对后来者可读，是推荐的 Python 实践。

## 1. 术语：Validator vs Guard

开始实现前必须分清两个词：

| 术语 | 是什么 | 职责 |
|---|---|---|
| **Validator** | 护栏的**核心逻辑**（讲师常直接称它 guardrail） | 实现"检查输入/输出是否符合你的验证规则"的代码 |
| **Guard** | **应用栈的一部分** | 处理输入/输出并传给 validator；**一个 guard 可以装多个 guardrail** |

> **架构师视角**：这是"规则逻辑"与"接入点"的解耦——validator 只回答"这段文本合不合规"，guard 负责"在管线哪个位置、对什么内容、失败了怎么办"。同一个 validator 可复用在 input 侧和 output 侧，也可与其他 validator 混搭进同一个 guard 一次执行。这与 `7-safety-guardrails.md` 的分层一致：卡点（①输入/②输出）是位置，检查器是逻辑，两者正交。

## 2. Guardrails AI SDK 的关键 imports

```python
from guardrails import Guard, OnFailAction, settings   # 核心三件套
# 以下只有"自定义 validator"才需要，用现成 hub validator 则不必导
from guardrails.validators import (
    Validator,           # 基类：subclass 它并写入自定义逻辑
    register_validator,  # 注册器：让编排框架能按名字找到你的 validator
    PassResult,          # 校验通过时返回
    FailResult,          # 检测到失败时返回
    ValidationResult,    # 仅用于 type hint（Pass/Fail 的联合类型）
)
```

- **Guard**：guardrail 的容器，可混搭多个 guardrail 同时运行；可初始化为跑在 LLM 调用的 **input 或 output 侧**；
- **OnFailAction**：指定失败时的处理方式——例如检测到幻觉，是**阻断** LLM 回答，还是**放行但在后端记录**这次失败；
- **register_validator**：注册后可按名字引用 validator。

## 3. 场景复现：system prompt 挡不住信息泄露

RAG chatbot 的搭建与前课相同（client + vector database 装着披萨店的 dummy 文档 + system message），唯一新增一句指令：

```
Do not respond to questions about Project Colosseum.
```

Project Colosseum 是披萨店尚未公开的新项目（不同 toppings 用不同面粉等）。模拟竞争对手套话：粘贴一个诱导性提问——**chatbot 直接泄露了披萨面团（crust）的配比**。system prompt 里"不许谈"的指令没能挡住信息泄露，这就是 validator 要解决的问题。

> **对比 7-safety-guardrails.md**：这正是选型文档里"**护栏是在确定性边界上设闸，不是让模型更乖**"的最小案例——把约束写进 system prompt 是"让模型更乖"（概率性、可被绕过），validator 是在边界上跑确定性代码（`if "colosseum" in value`），命中即拦，不依赖模型自觉。

## 4. 写最简单的 Validator

逻辑：输入字符串包含 Colosseum 的任何提及 → 拒绝回答。

```python
@register_validator(name="detect_colosseum", data_type="string")  # 注册，可按名引用
class ColosseumDetector(Validator):                # subclass 基类
    def validate(self, value: str, metadata: dict) -> ValidationResult:
        # value：待检查文本；metadata：附加信息（本例用不上）
        if "colosseum" in value.lower():
            return FailResult(
                error_message="Colosseum detected",   # 告知用户和 LLM 为什么失败
                fix_value="I'm sorry I can't answer questions "
                          "about Project Colosseum.", # 可选：失败时的替换文本
            )
        return PassResult()   # 通过不需要携带任何东西
```

`validate` 是 validator 的**唯一必须实现的方法**：进（value + metadata）→ 检查 → 出（`PassResult` 或 `FailResult`）。`FailResult` 两个字段各有用途：`error_message` 解释失败原因；`fix_value` 告诉 Guardrails 失败时用什么优雅替代。

## 5. 装进 Guard：位置 + 失败策略

```python
guard = Guard(name="Colosseum Guard").use(
    ColosseumDetector(on_fail=OnFailAction.EXCEPTION),  # 命中即抛异常
    on="messages",   # 跑在 input 侧（用户消息）；guard 默认跑在 output 侧
)
```

两个关键配置：

- **`on="messages"`**：本例把检查放在**输入侧**（在问题到达 LLM 前就拦下），而 guard 的**默认行为是跑在 output 侧**；
- **`on_fail=EXCEPTION`**：命中即抛异常——会**打断应用流**；改成 **`FIX`** 则返回 validator 里设置的 `fix_value`，给用户一条优雅的拒答消息。

## 6. Guardrails Server：一行 base_url 接入应用

Guardrails Server 是官方提供的部署工具：**把 LLM API 调用包起来，四周环上 input/output 护栏**。可本地运行或云端托管，可配置一个或多个 guard 供应用使用；guard 里既可以用你的自定义 guardrail（本例的 Colosseum detector），也可以用 Guardrails Hub 下载的现成 guardrail（后续课程展开）。

对生产应用的价值：

| 好处 | 说明 |
|---|---|
| 云部署容易 | 便于容器化 Guardrails 应用 |
| 独立扩缩 | 护栏所需基础设施（尤其 GPU）与主应用分开伸缩 |
| **OpenAI API 兼容** | OpenAI 或任何兼容 OpenAI SDK 的 LLM（含开源模型），**改一行就换成受保护端点** |
| 自建门槛低 | 一个简单配置文件 + 一条终端命令即可启动 |

接入方式就是给 OpenAI client 换 base_url：

```python
guarded_client = OpenAI(
    base_url="http://localhost:8000/guards/colosseum_guard/openai/v1/",
)   # 指向本地 Guardrails Server 上的 Colosseum guard，其余代码不变
```

> **架构师视角**：OpenAI 兼容端点是护栏产品的关键采纳设计——护栏作为**反向代理**插进"应用 → LLM"之间，应用代码零改造。这和 E2B 课把危险的本地 `exec` 换成云沙箱是同一招"换端点不换代码"：都把安全能力做成**基础设施层**而非应用逻辑，才能在组织里横向铺开。代价也要认识到：多一跳网络 + 每次调用都过 validator 的延迟，这是 `7-safety-guardrails.md` 里"同步拦截"的固有成本。

## 7. 验证效果与失败策略取舍

用同一条套话 prompt 打 guarded chatbot：

```
ValidationError: Validation failed for field with errors: Colosseum detected
```

在 LLM 有机会泄露任何专有数据**之前**，输入侧护栏就发现有人在套秘密并拦截。当前 `EXCEPTION` 策略会打断应用流；把 `on_fail` 改为 `FIX` 即可回传 `fix_value` 那条更优雅的消息。

## 8. 本课总结

| 要点 | 一句话 |
|---|---|
| Validator vs Guard | validator 是检查逻辑（subclass + validate 方法），guard 是应用侧容器（可装多个 validator） |
| validate 契约 | 进 value + metadata，出 PassResult / FailResult（error_message + 可选 fix_value） |
| 位置与策略 | `on="messages"` 选输入/输出侧（默认 output）；OnFailAction 选 EXCEPTION（阻断）或 FIX（优雅替换） |
| Guardrails Server | OpenAI 兼容端点，换 base_url 一行接入；支持容器化、独立扩缩 GPU |
| prompt ≠ 护栏 | system prompt 里"不许谈"挡不住套话，确定性 validator 才挡得住 |

> **记忆点（引出 L4）**：本课的 validator 只是 `if "colosseum" in value` 的字符串包含检查——"禁词"问题足够，但对付**幻觉**这种"输出流畅合理却不忠于事实"的失败模式毫无办法。L4 引入 **NLI（自然语言推理）模型**，构建一个真正有 ML 判断力的幻觉检测 validator。

## 与我的资产映射

- 护栏层选型：`agent/skills/agent-selection/7-safety-guardrails.md`（五段护栏链路——本课覆盖①输入护栏/②输出护栏两个卡点；OnFailAction 对应"阻断/改写"动作分类）
- 面试包：`agent/interview/jd-senior-agent-engineer/07-safety-guardrails.md`（validator/guard 术语与"确定性边界设闸"心智是标准答案素材）
- 执行面对照：`agent/courses/Building Coding Agents with Tool Execution/notes/L4-用E2B沙箱在云端运行Agent代码.md`（同为"换端点接入安全层"的基础设施化打法）
- [[project_selection_matrix]]
