# L5 · Using hallucination guard in a chatbot —— 本地可运行版(真 guardrails)

对照 DeepLearning.AI《Safe and reliable AI via guardrails》L5。把 L4 造的幻觉 validator **真正
用起来**,分两部分,全程真 guardrails:

- **Part 1(进程内 Guard)**:`Guard().use(HallucinationValidation, on_fail=EXCEPTION)`,
  sources 直接传入,跑课程的 sun 例子。**逐字照课程**。
- **Part 2(guardrails 服务器)**:`hallucination_guard` 跑在真服务器上,guarded client 指过去,
  把 veggie 幻觉 prompt 经 RAG 打过去看护栏拦截。

## ⚠️ 与课程的唯一偏离(如实标注,非偷偷替换)

课程 Part 2 用 guardrails **hub** 上的 `ProvenanceLLM` 校验器。但装它需要 **Guardrails Hub 的
注册/付费 API key**——`guardrails hub install hub://guardrails/provenance_llm` 实测返回
**401 Unauthorized**,本环境拿不到。

因此 Part 2 改用**课程自己在 L4 建的 `HallucinationValidation`**(真 guardrails Validator,基于
NLI 的 provenance 检测)跑在**同一个真 guardrails 服务器**上。**服务器 / Guard / guarded client /
on_fail 语义全部是真 guardrails**,只是把"hub 的 LLM 版 provenance"换成"课程 NLI 版 provenance"。

> 如果你有 Guardrails Hub key:`guardrails configure` 登录后
> `guardrails hub install hub://guardrails/provenance_llm`,再把 `config_l5.py` 里的 guard 换成
> `Guard().use(ProvenanceLLM(llm_callable=..., on_fail=...))` 即可,其余不变。

## 运行(两步,共用一个 3.12 venv)

Part 1 的 Guard 在客户端进程内跑、也要 NLI 栈,所以客户端和服务器**共用** `.venv-guardrails`。

```bash
/opt/homebrew/bin/python3.12 -m venv .venv-guardrails       # guardrails 只支持 <3.13
.venv-guardrails/bin/pip install -r requirements-guardrails.txt
.venv-guardrails/bin/pip install "click<8.2"                # 装完再压一次(见坑 3)

# server.env:litellm 用 deepseek/ 路由,需 DEEPSEEK_API_KEY
printf 'DEEPSEEK_API_KEY=<key>\nOPENAI_API_KEY=<key>\n' > server.env
cp .env.example .env && 填 OPENAI_API_KEY

# 终端 1:起服务器(启动会加载 NLI 模型,十几秒~几十秒)
PYTHONPATH=. .venv-guardrails/bin/guardrails start --config config_l5.py --env server.env --port 8000

# 终端 2:跑客户端(Part 1 进程内 + Part 2 打服务器)
.venv-guardrails/bin/python main.py
```

(没起服务器时,main.py 只跑 Part 1 并提示如何起服务器。)

## 实测(2026-07)

**Part 1**(逐字照课程):

| 输入 | 结果 |
|---|---|
| `The sun rises in the east.` | ✅ 通过(被 sources 蕴含) |
| `The sun is a star.` | 🛡️ 抛异常 `hallucinated: ['The sun is a star.']` |

**Part 2**(服务器 hallucination_guard + veggie prompt):RAG 回答在服务器端被拦下 ——
`BadRequestError: ... The following sentences are hallucinated: [...]`。

> 承 L4 结论:这次 DeepSeek 其实**拒答了**(没编造做法),但护栏仍拦下——因为拒答语没有知识库
> 出处。**provenance 护栏会过度标记非知识库出处的句子(含合理拒答)**。生产中要只对事实性声明
> 启用 / 给拒答开白名单 / 调阈值。若模型真编了一段做法,同样会被这条护栏拦下,判据一致:没出处=拦。

## 对架构师的结论

1. **validator → Guard → 服务器,是"可靠性"落地的三级跳。** L4 造校验器,L5 先用 `Guard` 在进程内
   拦(Part 1),再把它挂上服务器变成**独立护栏服务**(Part 2)。应用只需把 `base_url` 指过去就接入,
   护栏与业务解耦、可复用、可独立升级——这正是把安全能力平台化的形态。
2. **进程内 vs 服务器,是部署取舍。** 进程内:低延迟、无网络跳;服务器:集中管控、多应用共享、
   可独立扩缩容(NLI 很吃算力,单独部署更好按负载伸缩)。
3. **hub 生态 vs 自建校验器。** 课程想用 hub 的 ProvenanceLLM(开箱即用但要 key、要联网/联 LLM);
   自建 NLI validator 无需 key、可离线,但要自己维护模型。工程选型看合规、成本、可控性——
   这跟你在选型矩阵里权衡"托管 vs 自建"是同一类决策。
4. **护栏的真实成本要正视:算力、延迟、假阳性。** 每条回答逐句跑 NLI 很慢;provenance 又会过度
   标记(见上)。可靠性不是免费的,要在"拦得住"和"别误伤"之间调参、按风险分级启用。

## 文件

```
main.py                      # Part 1 进程内 Guard + Part 2 服务器 hallucination_guard
config_l5.py                 # 服务器配置:hallucination_guard(用 L4 的 HallucinationValidation)
helpers/hallucination.py     # HallucinationValidation validator(逐字照课程)
helpers/rag.py               # 本地 RAG(client 可注入:直连 / 指向服务器)
helpers/__init__.py          # 导出
requirements-guardrails.txt  # 单 venv 全量依赖(guardrails 服务器 + NLI 栈 + RAG)
shared_data/                 # 知识库
helper.py / Lesson_5.ipynb   # 原课程 helper 与 notebook(参照)
```
