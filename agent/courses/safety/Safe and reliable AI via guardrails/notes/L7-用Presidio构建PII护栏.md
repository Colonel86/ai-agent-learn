# L7 · 用 Presidio 构建 PII 护栏（输入侧拦截 + 输出侧流式脱敏）

> 课程：Safe and Reliable AI via Guardrails（DeepLearning.AI × GuardrailsAI）
> 本课任务：处理**PII（Personally Identifiable Information，个人可识别信息）的泄露与不当处理**——输入侧：在用户 prompt 发往第三方模型之前检出并拦截 PII；输出侧：用 Guardrails Hub 的 SOTA validator 对 LLM 输出做实时（含流式）PII 脱敏。

## 0. 为什么 PII 在 genAI 应用里格外要命

PII = 姓名、邮箱、社保号、电话……任何敏感且能定位到个人的信息。任何应用都要认真对待它，但 genAI 应用有两个放大因素：**用第三方模型**（每次调用都是一次把数据发出去的外部 API 请求），以及 **RAG 从大量多样的内部文档里检索文本**（谁也不敢保证文档里没混进敏感信息）。

要守的两个方向：

```
方向①（输入侧）：客户/员工/组织的私有数据
        用户 ──✗──> 第三方 LLM provider     绝不外泄给第三方

方向②（输出侧）：组织自己的数据
        LLM 响应 ──✗──> 不该看到它的用户     绝不经由回答误发
```

## 1. 失败复现：Hank 的电话号码进了后端存储

同一套 unguarded RAG chatbot。用户消息：

```
"能告诉我我在 <日期> 下的订单吗？我叫 Hank Tate，电话是 555-123-4567。"
```

LLM 的回复本身没问题——问题在别处：翻看聊天应用**后端存储的 messages**，Hank 的姓名和电话被原样落库了。对披萨店这不算什么（你家楼下披萨店本来就有你电话），但换成**银行、政府机构、尤其医疗服务**，看似无害的细节也必须极其敏感地处理。理想做法是**在源头检测并过滤**用户分享的私密信息，同时告警底层系统、按组织政策启动相应处理措施。

眼尖的话还会发现：对话上下文里另有一些 PII 是**retriever 从 vector database 里捞出来的**——这是本课结尾要处理的第二个问题。

## 2. Microsoft Presidio：analyzer + anonymizer 两个引擎

本课底层用微软开源的 **Presidio**，它做两件事：

```python
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine

analyzer = AnalyzerEngine()      # 检出文本里有哪些敏感实体（是什么、在哪）
anonymizer = AnonymizerEngine()  # 把检出的实体抹掉，其余文本保持可用
```

对 Hank 的消息跑 analyzer，检出三类实体（带字符区间定位）：

| 实体类型 | 位置 | 内容 |
|---|---|---|
| DATE_TIME | 43–60 | 下单日期 |
| PERSON | 73 起 | Hank Tate |
| PHONE_NUMBER | 串尾 | 电话号码 |

再过 anonymizer，得到脱敏文本：

```
"能告诉我我在 <DATE_TIME> 下的订单吗？我叫 <PERSON>，电话是 <PHONE_NUMBER>。"
```

**PII 被滤掉，但句子其余部分仍然可用**——还能正常回答 Hank 的问题，只是不再误持有他的私密信息。注意：对披萨店来说 PERSON 和 PHONE_NUMBER 敏感、DATE_TIME 无所谓；**具体过滤哪些实体完全取决于你的组织、用例和行业**（Presidio 支持的完整实体清单见官方文档）。

## 3. 自建 PII validator：检测函数 + 注册类

依旧两步。第一步，检测函数（只关心 PERSON 和 PHONE_NUMBER 两类）：

```python
def detect_pii(text: str) -> list[str]:
    results = analyzer.analyze(text,
                               entities=["PERSON", "PHONE_NUMBER"],
                               language="en")
    return [r.entity_type for r in results]   # 返回检出的实体类型
```

第二步，validator 类（核心逻辑照例都在 `validate` 方法里）：

```python
@register_validator(name="pii_detector", data_type="string")
class PIIDetector(Validator):
    def validate(self, value, metadata={}) -> ValidationResult:
        detected = detect_pii(value)
        if detected:   # 检出任何 PII → 失败，带上类型与 metadata
            return FailResult(error_message=f"PII detected: {detected}",
                              metadata=metadata)
        return PassResult(message="No PII detected")
```

初始化成"一旦检出姓名或电话就抛 exception"的 guard，用 Hank 的原句测试 → `Validation failed: PII (PERSON, PHONE_NUMBER) detected`；删掉电话号码再测 → 仍失败，检出 PERSON。

## 4. 输入侧上生产：exception 抢在数据出域之前

生产用 **Guardrails Hub 的 PII guardrail**（而非自建版），理由有二：支持**多得多的实体类型**，且支持**实时 streaming**。部署与前几课一致——OpenAI client 换 base_url 指向 guardrails server，但这次 **guard 跑在输入侧**：

```
用户消息 ──> PII Guard（输入侧）──✗ 检出 PII → 立刻抛 exception
                    │                    （消息根本没发往第三方 LLM）
                    ▼ 干净
                第三方 LLM
```

用 Hank 的消息打这个 guarded chatbot：`Message history validation failed`，而且**非常快**——因为异常在请求发出去之前就抛了。检查后端日志：**只存了 system message，Hank 那条含敏感信息的消息没有落库**。这就是"在源头检测"的含义：检测 → 脱敏 → 再按组织政策决定如何处置。

## 5. 输出侧流式脱敏：即使 LLM"看见了"，用户也看不见

最佳实践当然是**数据入 vector database 之前先清洗**。但两种现实必须兜底：一是意外——敏感数据总会混进去；二是**授权分级**——数据在库里是合法的，但不是每个用户都有权看到。所以要保证：**即使 LLM 在检索上下文里看到了私密信息，它也不会出现在给最终用户的答案里**。

Hub 版 PII guardrail 的亮点是能**实时**做这件事——把 PII 过滤从输入侧换到输出侧，配合 OpenAI streaming：

```python
response = guarded_client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[...],        # 让 GPT 写一个含编造的 10 位电话号码的两句话短故事
    stream=True)           # 流式输出

for chunk in response:     # 逐 chunk 校验：边流边验
    print(chunk)
```

演示里 LLM 确实生成了几个电话号码，但护栏逐 chunk 检出并**把已脱敏的结果返回给你**——体感即时。这样既**不付出明显的延迟代价**，又保证 LLM 的任何输出都已消毒、不含个人隐私信息。（演示用编造号码代替真实数据；真实系统里 LLM 输出可能真的 grounded 在被误泄给它的敏感信息上。）

> **架构师视角**：PII 护栏是少数**必须双侧部署**的护栏——输入侧守"数据出域"（合规红线，exception 要抢在网络请求之前），输出侧守"越权可见"（授权分级问题，靠流式脱敏控制延迟）。而且它和话题护栏不同：话题护栏失败可以直接拒答，PII 护栏的正解常常是 **anonymize 后继续服务**——用户的问题仍然值得回答，只是系统不该持有他的隐私。fail 之后"拒绝 vs 修复后放行"是设计护栏时必答的分叉题。

> **对比 Red Teaming LLM Applications（课程红队篇）**：红队视角下 PII 泄露是攻击者**主动诱导**出来的（prompt injection 套出训练数据/上下文），防守靠攻击面测试；本课的 PII 泄露大多是**无恶意的意外**（用户随手贴、文档里本来就有）。同一个失败模式，前者用对抗性 eval 在上线前找洞，后者用运行时护栏兜底——两者互补而非二选一，这也是 7-safety-guardrails.md 里"测试时安全 vs 运行时安全"的分层。

## 6. 本课总结

| 要点 | 一句话 |
|---|---|
| 两个泄露方向 | 输入侧：私有数据不外泄给第三方 LLM；输出侧：组织数据不经回答误发给用户 |
| Presidio | analyzer 检出实体（类型+位置），anonymizer 抹掉实体、保留文本可用性 |
| 实体选择 | 过滤哪些实体由组织/用例/行业决定（披萨店在乎 PERSON/PHONE，不在乎 DATE_TIME） |
| 输入侧护栏 | exception 抢在消息发往第三方之前，后端连日志都不落敏感信息 |
| 输出侧护栏 | Hub 版支持流式逐 chunk 脱敏，延迟几乎无感 |
| 数据库卫生 | 入库前清洗是最佳实践，但输出侧脱敏必须兜底（意外 + 授权分级） |

> **记忆点（引出 L8）**：PII 护的是**用户和组织的数据**；最后一类失败模式护的是**品牌与声誉**——别让你的 chatbot 替竞争对手带货。L8 构建 competitor check 护栏：精确匹配 → NER → 向量相似度的三级级联检测，并为全课收官。

## 与我的资产映射

- 安全层选型：`agent/skills/agent-selection/7-safety-guardrails.md`（PII 双侧部署、fail 后拒绝 vs 脱敏放行的分叉）
- 观测评估层：`agent/skills/agent-selection/5-observability-eval.md`（后端日志本身也是 PII 泄露面——观测数据同样要脱敏）
- 面试包：`agent/interview/jd-senior-agent-engineer/07-safety-guardrails`（Presidio analyzer/anonymizer、流式输出验证是高频考点）
- [[project_selection_matrix]]
