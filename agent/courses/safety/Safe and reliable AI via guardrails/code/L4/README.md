# L4 · Checking for hallucinations using NLI —— 本地可运行版(真 guardrails + 真 NLI 模型)

对照 DeepLearning.AI《Safe and reliable AI via guardrails》L4。**严格按课程示例逻辑**,不做
等价替代:用真 guardrails 的自定义 `HallucinationValidation` validator + 真 NLI 模型
`GuardrailsAI/finetuned_nli_provenance` + SentenceTransformer + nltk 分句,做 **provenance 型
幻觉检测**(逐句核对回答是否被知识库来源蕴含)。

与 L3 不同:**L4 不需要 guardrails 服务器**,validator 在进程内直接跑,所以只要一个 venv。

## 本地化改造(只动接入层,不碰 validator 逻辑)

| 环节 | 原课程 | 本地版 |
|---|---|---|
| 复现幻觉的 RAG LLM | OpenAI `gpt-3.5-turbo` | DeepSeek `deepseek-v4-flash` |
| RAG 检索 embedding | `SentenceTransformer`(SimpleVectorDB) | fastembed `bge-small-en-v1.5` |
| **幻觉 validator** | HallucinationValidation | **逐字保留**:all-MiniLM + NLI 模型 + nltk,一行没改 |
| 交互 | ipywidgets 手动粘贴 | 纯脚本 `main.py` |

> validator 用的 `SentenceTransformer('all-MiniLM-L6-v2')` 和 NLI 模型都**照课程原样**,
> 因为那就是这门课要教的护栏本身。只有"复现幻觉"的那个 RAG 应用换成了 DeepSeek+fastembed。

## 运行

```bash
cp .env.example .env          # 填 OPENAI_API_KEY(DeepSeek 的 key)
/opt/homebrew/bin/python3.12 -m venv .venv-guardrails    # guardrails 只支持 <3.13
.venv-guardrails/bin/pip install -r requirements-guardrails.txt
.venv-guardrails/bin/python main.py
```

首次运行会从 HuggingFace 下载 NLI 模型 + all-MiniLM(约百 MB)。国内可先
`export HF_ENDPOINT=https://hf-mirror.com`。nltk 的 punkt_tab 分句数据由 `ensure_punkt()`
自动下载;若被网络限制,手动 `python -c "import nltk; nltk.download('punkt_tab')"`。

## 四步 & 实测(2026-07)

1. **复现幻觉**:向 RAG 要 "veggie supreme 的详细做法"——知识库只有配料、没有做法。
2. **NLI 模型**:课程两个例子。`The sun rises in the east.` → **entailment**;
   `The sun rises in the west.` → **contradiction**(被前提否定)。
3. **HallucinationValidation 单测**(sun 例子):
   - `"The sun sets in the east"` → **fail**(不被来源蕴含,判为幻觉)
   - `"The sun sets in the west"` → **pass**(被来源蕴含)
4. **[本地额外验证]** 把 validator 接到第 1 步的真实 RAG 回答上,用整个知识库当 sources。
   实测一个诚实的发现:这次 DeepSeek **拒答了**(没编造),但 validator 把**全部句子**都标成
   "无出处"——因为拒答语/寒暄语本就不在知识库里。这暴露了 provenance 护栏的真实取舍:
   **它会过度标记一切非知识库出处的句子,包括合理拒答**(见下方结论 3)。

## validator 逻辑(provenance 型幻觉检测,逐字照课程)

```
回答  --nltk.sent_tokenize-->  句子们
每个句子  --all-MiniLM embedding, cos>0.8 取 top5-->  相关来源
每个句子 × 相关来源  --NLI 模型-->  label == 'entailment' ?
  只要有一句 "没有任何来源蕴含它"  =>  FailResult(列出幻觉句)
```

关键:它不看模型"说得像不像真的",只认**知识库能否证明这句话**。没出处 = 幻觉,一律拦。

## 对架构师的结论

1. **幻觉护栏 = 事后逐句核对来源,不是求模型别编。** "别编造"写进提示词是软约束(见 L1);
   provenance 校验是**确定性**的:把回答拆句、找来源、用 NLI 判蕴含,没出处就判幻觉。
2. **NLI(自然语言推理)是幻觉检测的核心武器。** 相比"字符串匹配来源",NLI 能判断**语义蕴含**——
   句子换个说法但意思有出处,也算通过;意思无出处,再流畅也拦。代价是要跑一个额外的 NLI 模型。
3. **provenance 护栏会"过度标记",要主动管理误报。** 它只认知识库出处,于是**拒答语、寒暄语、
   合理的澄清**这些本就不在知识库里的句子会被一并标成"幻觉"(本课第 4 步实测到了)。工程上要:
   只对**事实性声明**启用、给拒答/寒暄开白名单、或调 cos 阈值。否则一堆假阳性会淹没真幻觉。
4. **护栏也要吃算力和延迟。** 每句都要 embedding + 若干次 NLI 前向,这是可靠性的成本。
   工程上权衡:抽样校验 / 只校验高风险回答 / 用更小的 NLI 模型。
5. **与红队课 L4 呼应:都是"LLM/模型当裁判"。** 那边用 LLM 判偏见,这边用 NLI 模型判蕴含——
   都是拿一个模型去**核对**另一个模型的输出,是规模化可靠性校验的通用范式。

## 文件

```
main.py                      # 四步:复现幻觉 → NLI 测试 → validator 单测 → 接真实回答验证
helpers/hallucination.py     # HallucinationValidation validator(逐字照课程)+ NLI pipeline
helpers/rag.py               # 本地 RAG(fastembed + DeepSeek),仅用于复现幻觉
helpers/__init__.py          # 导出
requirements-guardrails.txt  # 单 venv 依赖(guardrails + torch/transformers/st/nltk + RAG)
shared_data/                 # 知识库
helper.py / Lesson_4.ipynb   # 原课程 helper 与 notebook(参照)
```
