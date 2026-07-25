# L6 · Keeping a chatbot on topic —— 本地可运行版(真 guardrails + 本地 zero-shot 分类器)

> ⚠️ **2026-07-25 环境合并**:L1-L8 已共用 `code/.venv`(guardrails 0.10.2,见 [`../README.md`](../README.md));下文中 `.venv-guardrails`/独立 venv 的搭建命令是历史记录,运行一律用 `../.venv/bin/python`,服务器用 `../.venv/bin/guardrails-api start`。

对照 DeepLearning.AI《Safe and reliable AI via guardrails》L6。**严格按课程逻辑**,不做等价替代:
自定义 `ConstrainTopic` validator(真 guardrails Validator)+ HuggingFace zero-shot 分类器
`facebook/bart-large-mnli`,把**跑题**的输入挡在 LLM 之前。

服务器段用**课程自带的 `local_config.py` 思路**(本地 `ConstrainTopic`)——课程本就给了两版
配置:`config.py`/`on_topic_config.py`(hub 的 `RestrictToTopic`,需 Guardrails Hub key,实测 401)
与 `local_config.py`(本地分类器,无需 key)。这里用后者,所以是**忠实还原**,不是替代。

## 本地化改造(只动接入层)

| 环节 | 原课程 | 本地版 |
|---|---|---|
| 复现跑题的 RAG LLM | OpenAI `gpt-3.5-turbo` | DeepSeek `deepseek-v4-flash` |
| 性能对比里的 LLM | `gpt-4o-mini` + `beta.chat.completions.parse`(结构化输出) | DeepSeek 普通 completion + 防御式 JSON 解析(DeepSeek 不支持 beta.parse,实测 400) |
| **话题分类器 / validator** | zero-shot `bart-large-mnli` + ConstrainTopic | **逐字保留** |
| 服务器 guard | 课程 `local_config.py`(ConstrainTopic) | 同思路 `config_l6.py` |

## 运行(两步,共用一个 3.12 venv)

分类器在客户端进程内也要跑,所以客户端与服务器共用 `.venv-guardrails`。

```bash
/opt/homebrew/bin/python3.12 -m venv .venv-guardrails       # guardrails 只支持 <3.13
.venv-guardrails/bin/pip install -r requirements-guardrails.txt
.venv-guardrails/bin/pip install "click<8.2"                # 装完再压一次

printf 'DEEPSEEK_API_KEY=<key>\nOPENAI_API_KEY=<key>\n' > server.env
cp .env.example .env && 填 OPENAI_API_KEY

# 终端 1:起服务器(启动加载 bart 分类器)
PYTHONPATH=. .venv-guardrails/bin/guardrails start --config config_l6.py --env server.env --port 8000

# 终端 2:跑客户端
.venv-guardrails/bin/python main.py
```

(没起服务器时,main.py 跑完 Part 1-5 并提示如何起服务器。)首次运行下载 bart-large-mnli(约 1.6G)。
> 提示:HF 新的 xet 下载后端偶发 I/O 报错,可 `export HF_HUB_DISABLE_XET=1` 用经典下载路径。

## 六步 & 实测(2026-07,Mac Studio)

1. **复现跑题**:伪『系统指令』诱导 → DeepSeek 果然去讲 Ford F-150 vs Ranger。
2. **zero-shot 分类器**:`"Chick-Fil-A is closed on Sundays."` → food 0.67 / business 0.18 / politics 0.03。
3. **zero-shot vs LLM(各跑 5 次)**:

   | 方式 | 单次耗时 |
   |---|---|
   | DeepSeek(LLM) | ~0.86s |
   | bart zero-shot(本地) | **~0.12s** |

   本机上本地小模型比 LLM 快约 **7 倍**(课程学习平台 CPU 弱,结论相反——所以这是**依机器而定**的取舍)。
4/5. **ConstrainTopic + topic_guard**(禁止 politics/automobiles):
   - `"Who should i vote for in the upcoming election?"` → 🛡️ 抛异常(politics)
   - `"What pizzas are on the menu?"` → ✅ 通过
6. **服务器 topic_guard**:跑题 prompt 经 guarded client → 🛡️ 在进 LLM 之前被拦
   (`banned topics: ['politics']`)。

## 对架构师的结论

1. **话题护栏 = 用分类器在输入侧判话题,越界即拦。** 比"提示词里写别跑题"(软约束,L1 里一句注入
   就绕过)可靠得多——分类是确定性的,且**在进 LLM 之前**就拦,省掉一次无谓生成。
2. **小专用模型 vs 大 LLM,是这一课最值钱的取舍。** 分类这种窄任务,本地 zero-shot(bart)在有算力的
   机器上又快又省又可离线(本机快 7 倍);LLM 免部署、免下模型,但有网络/费用/延迟,且弱 CPU 上本地模型
   反而更慢。**选型要看:机器算力、并发量、延迟预算、是否需离线/合规**——正是选型矩阵那套判断。
3. **同一个 validator,进程内与服务器两种部署。** 进程内低延迟;服务器集中管控、多应用复用、可按负载
   独立扩缩容(分类器吃算力,单独部署更好伸缩)。
4. **hub 生态 vs 自建。** 课程给了 hub `RestrictToTopic`(SOTA、开箱即用,但要 key/联网)与本地
   `ConstrainTopic`(自建、可离线)两版。工程选型按合规、成本、可控性权衡——本课用本地版跑通全链路。

## 文件

```
main.py                      # 六步:复现跑题 → 分类器 → 计时对比 → validator → 进程内/服务器 guard
config_l6.py                 # 服务器配置:topic_guard(用本地 ConstrainTopic,对应课程 local_config.py)
helpers/topic.py             # ConstrainTopic validator + zero-shot 分类器(逐字照课程)
helpers/rag.py               # 本地 RAG(client 可注入),仅用于复现跑题
helpers/__init__.py          # 导出
requirements-guardrails.txt  # 单 venv 依赖(guardrails 服务器 + transformers/torch + RAG)
shared_data/                 # 知识库
config.py / local_config.py / on_topic_config.py  # 原课程三份配置(参照)
helper.py / Lesson_6.ipynb   # 原课程 helper 与 notebook(参照)
```
