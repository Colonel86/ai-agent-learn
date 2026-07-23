# 真·Guardrails Hub 变体 —— 统一设置指南(`.venv-hub`)

课程各课默认用的是**自建 validator**(本地模型 + guardrails 0.5.3),避免依赖 Guardrails Hub。
如果你有 Hub API key,想跑**真·hub 校验器**做对照,按本文档建一个**独立的 `.venv-hub`**,四课的
`main_hub.py` 都用它。

> 为什么单独一个 venv:hub 校验器与各课本地版的依赖(尤其 torch/transformers 版本、numpy)会互相
> 冲突。隔离开,各跑各的,互不污染。

## 关键决策:用 guardrails **0.10.2**,不是课程的 0.5.3

课程锁的是 `guardrails-ai==0.5.3`(2024 年)。那套旧栈坑很多(只支持 Python <3.13、click<8.2、
numpy<2、旧 regex/scipy…),而且 hub 校验器装进现代 torch/transformers 环境会把这些依赖全搅坏。

**改用最新的 `guardrails-ai==0.10.2`**(`Requires-Python: >=3.10,<4.0`,支持 3.13)后,这些坑
基本消失:numpy 2、click 8.2 都能用。**这本身就是架构结论:与其重建供应商冻结的旧栈,不如升到
现代版本让依赖自洽。**

## 一、建 `.venv-hub` 并装 guardrails 0.10.2

```bash
cd ".../code"
/opt/homebrew/bin/python3.12 -m venv .venv-hub
.venv-hub/bin/pip install "guardrails-ai==0.10.2" openai fastembed python-dotenv httpx
```

## 二、配 Hub token(全局,一次即可)

```bash
.venv-hub/bin/guardrails configure --token <你的KEY> --disable-remote-inferencing --disable-metrics
```

写入 `~/.guardrailsrc`(`use_remote_inferencing=false` = 用本地模型,免费离线)。

## 三、装 4 个 hub 校验器 —— 用**手动 pip**(绕过 CLI 的 token bug)

> ⚠️ 实测 `guardrails hub install hub://...` 在本环境**没把 token 传给 pip**,直接 401/失败。
> 解法:直接用带 token 的私有源手动 pip 装 `*grhub*` 包。

```bash
TOKEN=$(grep '^token=' ~/.guardrailsrc | cut -d= -f2)
IDX="https://__token__:${TOKEN}@pypi.guardrailsai.com/simple"
PIP() { .venv-hub/bin/pip install "$1" --index-url "$IDX" --extra-index-url https://pypi.org/simple; }

PIP guardrails-grhub-detect-pii          # L7  DetectPII
PIP guardrails-grhub-competitor-check    # L8  CompetitorCheck
PIP guardrails-grhub-provenance-llm      # L5  ProvenanceLLM
PIP tryolabs-grhub-restricttotopic       # L6  RestrictToTopic(注意:tryolabs 前缀)
```

**再补两个 spacy 模型**(DetectPII 用 lg、CompetitorCheck 用 trf):

```bash
.venv-hub/bin/pip install \
  https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl
.venv-hub/bin/pip install spacy-transformers \
  https://github.com/explosion/spacy-models/releases/download/en_core_web_trf-3.8.0/en_core_web_trf-3.8.0-py3-none-any.whl
```

## 四、导入方式:从 `guardrails_grhub_*` 直接导

手动 pip 跳过了 `guardrails hub install` 的"注册进 `guardrails.hub` 命名空间"后处理,所以
`from guardrails.hub import DetectPII` 可能失败。**改从各自的包直接导**(各 `main_hub.py` 就是这么写的):

```python
from guardrails_grhub_detect_pii import DetectPII
from guardrails_grhub_competitor_check import CompetitorCheck
from guardrails_grhub_provenance_llm import ProvenanceLLM
from tryolabs_grhub_restricttotopic import RestrictToTopic
```

## 五、跑各课的 hub 变体

```bash
cd L7 && ../.venv-hub/bin/python main_hub.py    # DetectPII
cd L8 && ../.venv-hub/bin/python main_hub.py    # CompetitorCheck
cd L6 && ../.venv-hub/bin/python main_hub.py    # RestrictToTopic(disable_llm 离线)
cd L5 && ../.venv-hub/bin/python main_hub.py    # ProvenanceLLM(需 .env 里 DEEPSEEK/OPENAI_API_KEY)
```

## 实测结果 & 每个校验器的坑(2026-07)

| 课 | hub 校验器 | 实测 | 要点 |
|---|---|---|---|
| L7 | DetectPII | ✅ 输入 EXCEPTION 拦、输出 FIX 打码 `<PERSON>/<PHONE_NUMBER>/<EMAIL_ADDRESS>` | 底层 Presidio,需 spacy `en_core_web_lg` |
| L8 | CompetitorCheck | ⚠️ 能跑,但**漏了 "Pizza by Alfredo"** | NER(`en_core_web_trf`)先抽实体再比,NER 没识别到该名字就漏;**自建版有精确匹配兜底反而更稳** |
| L6 | RestrictToTopic | ✅ 披萨问题通过、福特皮卡拦 `Invalid topics: ['automobiles']` | 0.10.x 默认要 LLM;设 `disable_llm=True` 只用本地 zero-shot(离线、免凭证) |
| L5 | ProvenanceLLM | ✅ 有出处通过、编造句被拦 | 用 LLM 当裁判,`llm_callable="deepseek/deepseek-chat"` 接 DeepSeek;需联网下 embedding 模型 |

## 对架构师的结论(hub vs 自建)

1. **能力层(检测)可换,编排/网关层不变。** 换 hub 版还是自建版,变的是"检测能力"这一层;
   `Guard`/`on_fail`(编排)、服务器(网关)都不动——这正是三层护栏架构分离的价值。
2. **hub 不是"更强"的同义词。** L8 就打脸:hub CompetitorCheck 的 NER 路线**漏了**自建版精确匹配
   能抓的竞品名。开箱即用 ≠ 更准,选型要按你的实际数据实测。
3. **hub 的隐性成本:token / 网络 / 版本耦合 / 依赖冲突。** 要独立 venv、要 token、部分校验器
   (ProvenanceLLM/RestrictToTopic)还要联网或 LLM。自建版换来的是可控、可离线、逻辑透明。
4. **升级到最新版往往比复刻旧锁更省事。** 0.5.3→0.10.2 一步跨过了一大半依赖坑。工程上遇到
   "供应商冻结的旧栈",先看有没有现代版本可用,别急着复刻老环境。

## 文件

```
.venv-hub/                 # 隔离 venv(guardrails 0.10.2 + 4 grhub + spacy,已 gitignore)
L5/main_hub.py             # ProvenanceLLM(DeepSeek 裁判)
L6/main_hub.py             # RestrictToTopic(disable_llm 离线)
L7/main_hub.py             # DetectPII
L8/main_hub.py             # CompetitorCheck
```
