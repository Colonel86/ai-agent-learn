# L8 · Preventing competitor mentions —— 本地可运行版(真 guardrails + 本地 NER 校验器)

> ⚠️ **2026-07-25 环境合并**:L1-L8 已共用 `code/.venv`(guardrails 0.10.2,见 [`../README.md`](../README.md));下文中 `.venv-guardrails`/独立 venv 的搭建命令是历史记录,运行一律用 `../.venv/bin/python`,服务器用 `../.venv/bin/guardrails-api start`。

对照 DeepLearning.AI《Safe and reliable AI via guardrails》L8。**严格按课程逻辑**,不做等价替代:
自定义 `CheckCompetitorMentions` validator(真 guardrails Validator),**三层查竞品**——
精确匹配 + NER(`dslim/bert-base-NER`)抽实体 + 向量相似(all-MiniLM + 余弦)。

服务器段:课程 `config.py` 用 hub 的 `CompetitorCheck`(需 Guardrails Hub key,实测 401)。这里用
课程自己写的 `CheckCompetitorMentions`(真 guardrails Validator,NER+相似,全本地无需 key)——
非等价替代,是用课程本身的校验器还原。有 key 者可换 hub 的 CompetitorCheck。

## 本地化改造(只动接入层)

| 环节 | 原课程 | 本地版 |
|---|---|---|
| 复现提竞品的 RAG LLM | OpenAI `gpt-3.5-turbo` | DeepSeek `deepseek-v4-flash` |
| **竞品 validator** | CheckCompetitorMentions(NER+相似) | **逐字保留** |
| 服务器 competitor_check | 课程 config.py(hub CompetitorCheck) | config_l8.py(本地 CheckCompetitorMentions) |

## 运行(两步,共用一个 3.12 venv)

```bash
/opt/homebrew/bin/python3.12 -m venv .venv-guardrails       # guardrails 只支持 <3.13
.venv-guardrails/bin/pip install -r requirements-guardrails.txt
.venv-guardrails/bin/pip install "click<8.2"                # 装完再压一次

printf 'DEEPSEEK_API_KEY=<key>\nOPENAI_API_KEY=<key>\n' > server.env
cp .env.example .env && 填 OPENAI_API_KEY

# 终端 1:起服务器(启动加载 NER + all-MiniLM)
PYTHONPATH=. .venv-guardrails/bin/guardrails start --config config_l8.py --env server.env --port 8000
# 终端 2:跑客户端
.venv-guardrails/bin/python main.py
```

首次运行下载 `dslim/bert-base-NER` + all-MiniLM(约几百 MB)。HF 新 xet 后端偶发 I/O 错误,
可 `export HF_HUB_DISABLE_XET=1` 走经典下载路径。

## 四步 & 实测(2026-07)

1. **复现提竞品**:诱导比较 → DeepSeek 虽拒绝比较,但回答里**仍出现** "Pizza by Alfredo"
   (承 L1:模型嘴上说不聊竞品,却把名字带了出来)。
2/3. **CheckCompetitorMentions + 进程内 guard(EXCEPTION)**:
   - `"Sure! Pizza by Alfredo offers a great deal..."` → 🛡️ 抛异常
     `directly mentions competitors: Pizza by Alfredo`(精确匹配层命中)
   - `"We have Margherita, Pepperoni and Veggie Supreme..."` → ✅ 通过
4. **服务器 competitor_check**:诱导 prompt 经 guarded RAG,**输出**提到竞品 →
   服务器端拦下 `Your response directly mentions competitors: Pizza by Alfredo`。

## validator 的三层逻辑(逐字照课程)

```
回答文本
 ├─ 1) exact_match       整词命中竞品名(regex \b...\b)      → 命中即 Fail(最快、零误报)
 ├─ 2) extract_entities  NER(bert-base-NER)抽出命名实体
 └─ 3) vector_similarity 实体 embedding vs 竞品 embedding,cos≥0.6 → 命中即 Fail(抓改写/近义)
任一层命中 → FailResult(列出命中的竞品)
```

## 对架构师的结论

1. **提竞品护栏放在输出侧,用实体/相似度检测。** 比"提示词里写别提竞品"(软约束,L1 里被绕过)
   可靠——它扫的是模型**实际吐出的字**,不管模型是不是"想"提。
2. **精确 + 语义分层,是召回与误报的平衡术。** 精确匹配零误报但脆(错拼/变体漏);向量相似
   能抓改写但会误报(阈值太低会把无辜实体也拦)。三层递进 + 可调阈值(0.6),是产品旋钮。
3. **NER 缩小比对范围是关键设计。** 不是把整段文本硬和竞品名比,而是先抽"组织/品牌"实体再比——
   既省算力又降误报。这种"先结构化再匹配"的思路,在很多护栏/检索场景通用。
4. **hub 开箱即用 vs 自建可控。** 课程给了 hub CompetitorCheck(SOTA、免维护,但要 key/联网);
   自建 NER 版无需 key、可离线、阈值可调。选型看合规、成本、可控性——本课用本地版跑通全链路。

## 文件

```
main.py                      # 四步:复现提竞品 → validator 单测 → 进程内 guard → 服务器 guard
config_l8.py                 # 服务器配置:competitor_check(用本地 CheckCompetitorMentions)
helpers/competitor.py        # CheckCompetitorMentions validator(NER+相似,逐字照课程)
helpers/rag.py               # 本地 RAG(client 可注入),仅用于复现提竞品
helpers/__init__.py          # 导出
requirements-guardrails.txt  # 单 venv 依赖(guardrails 服务器 + transformers/torch/st/sklearn + RAG)
shared_data/                 # 知识库
config.py / helper.py / Lesson_8.ipynb   # 原课程配置/helper/notebook(参照)
```
