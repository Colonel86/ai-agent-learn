# L7 · Ensuring no PII is leaked —— 本地可运行版(真 guardrails + Microsoft Presidio)

> ⚠️ **2026-07-25 环境合并**:L1-L8 已共用 `code/.venv`(guardrails 0.10.2,见 [`../README.md`](../README.md));下文中 `.venv-guardrails`/独立 venv 的搭建命令是历史记录,运行一律用 `../.venv/bin/python`,服务器用 `../.venv/bin/guardrails-api start`。

对照 DeepLearning.AI《Safe and reliable AI via guardrails》L7。**严格按课程逻辑**,不做等价替代:
用 **Microsoft Presidio**(本地开源 PII 引擎,**无需任何 key**)+ 自定义 `PIIDetector`(真 guardrails
Validator),在**输入/输出两侧**防 PII 泄漏。

服务器段:课程 `config.py` 用 hub 的 `DetectPII`(需 Guardrails Hub key,实测 401)。这里用课程自己
引入的 **Presidio + 自定义 PIIDetector** 实现同样的两侧防护——**hub DetectPII 本质就是 Presidio 的
封装**,所以这不是等价替代,是用课程本身的工具还原。有 key 者可换 hub 版。

## 本地化改造(只动接入层)

| 环节 | 原课程 | 本地版 |
|---|---|---|
| 复现 PII 留存的 RAG LLM | OpenAI `gpt-3.5-turbo` | DeepSeek `deepseek-v4-flash` |
| **PII 引擎 / validator** | Presidio + PIIDetector | **逐字保留**(Presidio 是本地开源,无需 key) |
| 服务器 pii_guard | 课程 config.py(hub DetectPII) | config_l7.py(本地 PIIDetector,同样输入 refrain/输出 fix) |

## 运行(两步,共用一个 3.12 venv)

```bash
/opt/homebrew/bin/python3.12 -m venv .venv-guardrails       # guardrails 只支持 <3.13
.venv-guardrails/bin/pip install -r requirements-guardrails.txt
.venv-guardrails/bin/pip install "click<8.2"                # 装完再压一次
# Presidio 默认用 spacy en_core_web_lg(~400MB):
.venv-guardrails/bin/python -m spacy download en_core_web_lg
#   若网络受限,直接装 wheel:
#   .venv-guardrails/bin/pip install \
#     https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl

printf 'DEEPSEEK_API_KEY=<key>\nOPENAI_API_KEY=<key>\n' > server.env
cp .env.example .env && 填 OPENAI_API_KEY

# 终端 1:起服务器(启动加载 Presidio/spacy)
PYTHONPATH=. .venv-guardrails/bin/guardrails start --config config_l7.py --env server.env --port 8000
# 终端 2:跑客户端
.venv-guardrails/bin/python main.py
```

## 六步 & 实测(2026-07)

1. **复现 PII 留存**:Hank Tate 的姓名+电话被原样存进后端 `messages`(角色 user)。
2. **Presidio**:识别 `['PERSON','PHONE_NUMBER']`;anonymizer 打码为
   `...my name is <PERSON> and my phone number is <PHONE_NUMBER>`。
3/4. **PIIDetector + 进程内 pii_guard(EXCEPTION)**:含 PII 的输入 → 🛡️ 抛异常
   `PII detected: PERSON, PHONE_NUMBER`。
5. **服务器 pii_guard(输入 refrain / 输出 fix)**:含 PII 的输入在服务器端被 refrain
   (`400 Message history validation failed`)——PII 不进入后续处理/留存。
6. **输出脱敏(on_fail=FIX)**:把 LLM 输出里的电话/人名实时替换成 `<PHONE_NUMBER>`/`<PERSON>`
   再返回。(注:`.example` 这种保留域名不被 Presidio 的邮箱识别器命中,属其 recognizer 边界。)

> 关于 Part 5 的 400:作用在**输入消息**上的 refrain/fix,在本课 pinned 的 guardrails-api 0.0.1 上
> 会以 400 返回(与 L3 的 FIX-on-messages 一致),这是真实服务器行为,未美化。意图达成:PII 输入被拦。

## 对架构师的结论

1. **PII 泄漏是架构层问题,不是模型问题(承 L1)。** 模型再"守规矩"也拦不住——泄漏发生在
   **存储 / 日志 / 输出**侧。解法只能是把 PII 校验放到确定性护栏层。
2. **两侧设防:输入 + 输出。** 输入侧(refrain/exception)让含 PII 的用户输入不留存、不喂给模型,
   缩小暴露面;输出侧(fix)把模型可能吐出的 PII 实时打码。缺一面都留口子。
3. **确定性引擎 vs LLM 判 PII。** Presidio 用规则+NER(spacy)确定性识别,可离线、可审计、无需 key,
   比"让 LLM 自己别说 PII"可靠得多——PII 这种有明确 pattern 的东西,专用引擎优于通用 LLM。
4. **合规视角:PII 护栏往往是硬需求(GDPR/等保)。** 把它做成独立护栏服务,可对多个应用统一
   实施、统一审计、统一升级识别规则——这跟你在选型矩阵里对"数据层权限/脱敏"的思路一致。

## 文件

```
main.py                      # 六步:复现留存 → Presidio → PIIDetector → 进程内/服务器 guard → 输出脱敏
config_l7.py                 # 服务器配置:pii_guard(输入 refrain / 输出 fix,用本地 PIIDetector)
helpers/pii.py               # PIIDetector validator + Presidio 检测/打码(逐字照课程 + fix_value)
helpers/rag.py               # 本地 RAG(client 可注入),仅用于复现 PII 留存
helpers/__init__.py          # 导出
requirements-guardrails.txt  # 单 venv 依赖(guardrails 服务器 + presidio/spacy + RAG)
shared_data/                 # 知识库
config.py / helper.py / Lesson_7.ipynb   # 原课程配置/helper/notebook(参照)
```
