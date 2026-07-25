# L3 · Building your first guardrail —— 本地可运行版(真 guardrails)

> ⚠️ **2026-07-25 环境合并**:L1-L8 已共用 `code/.venv`(guardrails 0.10.2,见 [`../README.md`](../README.md));下文中 `.venv-guardrails`/独立 venv 的搭建命令是历史记录,运行一律用 `../.venv/bin/python`,服务器用 `../.venv/bin/guardrails-api start`。

对照 DeepLearning.AI《Safe and reliable AI via guardrails》L3。**严格按课程示例逻辑用真
guardrails**(不做等价替代):自定义 `ColosseumDetector` validator → 包成 `Guard` → 跑在
**guardrails 服务器**上 → guarded client 指向服务器,LLM 调用在进模型前被 guard 拦截。

与前面的红队课不同,这里没有把 guardrails 换成手写等价物——用的就是 `guardrails-ai==0.10.2`
本体(已从课程原 pin 0.5.3 升级,与 ../HUB.md 的 `.venv-hub` 同版本)、真的把服务器跑起来。
只在**接入层**做了本地化:裁判/生成 LLM 走 DeepSeek(litellm 的 `deepseek/` 路由)、embedding
走本地 fastembed。

## 架构:轻客户端 + 重服务器(两个 venv)

```
main.py (客户端, .venv)  --HTTP-->  guardrails 服务器 (.venv-guardrails)  --litellm-->  DeepSeek
   └ 直连 DeepSeek 也走这个客户端(无护栏对照)          └ config_l3.py 定义 guard
```

- **客户端**(`main.py`)只用 openai/fastembed/numpy/httpx,**不含 guardrails**,轻。
- **服务器**(`guardrails-api start`)才装 guardrails 那套重依赖,单独 3.12 venv。

## 运行(两步)

**第一步:起 guardrails 服务器**(单独的 3.12 venv;0.10.2 其实已支持 3.13,用 3.12 只为与
`.venv-hub` 保持一致):

```bash
/opt/homebrew/bin/python3.12 -m venv .venv-guardrails
.venv-guardrails/bin/pip install -r requirements-guardrails.txt

# 准备服务器环境文件:litellm 用 deepseek/ 路由,需要 DEEPSEEK_API_KEY
printf 'DEEPSEEK_API_KEY=<你的key>\nOPENAI_API_KEY=<你的key>\n' > server.env

# 注意:用 guardrails-api 的 CLI 启动,不用 `guardrails start`(封装层有 bug,见下「坑」)
.venv-guardrails/bin/guardrails-api start --config config_l3.py --env server.env --port 8000
```

**第二步:另开一个终端,跑客户端**:

```bash
cp .env.example .env          # 填 OPENAI_API_KEY(DeepSeek 的 key)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

(main.py 会先探活服务器;没起服务器则只跑 A 段无护栏对照,并提示如何起服务器。)

## 演示三条路径 & 实测(deepseek-v4-flash + guardrails 0.10.2,2026-07)

| 路径 | 说明 | 实测 |
|---|---|---|
| **A. 无护栏**(直连 DeepSeek) | 用"续写"套路诱导泄漏机密 Project Colosseum | ✅ 这次 DeepSeek 守住了(对齐较好);但软约束不可靠,换模型/措辞就可能破防 |
| **B. colosseum_guard**(EXCEPTION) | 含 `colosseum` 的输入 | 🛡️ **确定性拦截**:`BadRequestError: Validation failed ... Colosseum detected`,请求根本没进 LLM |
| B. 同上 + 正常问题 | "What pizza types do you have?" | ✅ 正常经 DeepSeek 回答(列出菜单) |
| **C. colosseum_guard_2**(FIX) | 含 `colosseum` 的输入 | ✅ **优雅降级**:fix_value 替换命中输入后继续进 LLM,返回礼貌拒答(0.5.3 时代此路径报 400,升级后与课程视频行为一致) |
| C. 同上 + 正常问题 | "How long does delivery take?" | ✅ 正常经 DeepSeek 回答(配送时间) |

**核心对比 A vs B**:同一条"别聊 Colosseum"的规则,写进系统提示词(A)是**软约束**、一个续写
套路就可能绕过;做成 guardrails 服务器上的 **validator**(B)是**确定性护栏**、在进 LLM 之前按
代码规则拦截,和模型是否"听话"无关。这就是"第一个 guardrail"的意义。

## 为什么升到 0.10.2 & 新旧坑对照

课程原 pin `guardrails-ai==0.5.3`(2024)那套旧栈坑很多:只支持 Python <3.13、`guardrails start`
自举时拼出非法版本号(`guardrails-api>="^0.0.0a0"`)必须预装 0.0.1、必须钉死 `click<8.2`、
guardrails-api 0.0.1 对 AsyncGuard 同步调用直接 500、输入侧 FIX 有 bug 仍返回 400。

升到 **0.10.2**(与 ../HUB.md 的 `.venv-hub` 同版本)后,上述坑**全部消失**:支持 Python 3.13、
click 8.2/numpy 2 自洽、guardrails-api 解析到合法的 0.4.3、FIX 路径按课程预期优雅降级。这正是
"旧包优先升级而非复刻旧锁"的实证。

但 0.10.2 + guardrails-api 0.4.3 组合有**两个新坑**(均已规避,写进 requirements 注释):

1. **`guardrails start` 封装层崩溃**:它以编程方式调用 `guardrails_api` 的 `start()` 却漏传
   `middleware` 参数,typer 的 `OptionInfo` 默认值一路漏进 `os.path.abspath` →
   `TypeError: expected str ... not OptionInfo`。解法:**改用 `guardrails-api start` 直接启动**
   (走 typer CLI,默认值正确解析),参数完全相同。
2. **Guard 按 id 查找、id 默认是随机 UUID**:0.10.2 里 `Guard(name=...)` 的 `id` 不再等于 name,
   而服务器内存注册表(`guards[export.id] = export`)和 `/guards/{id}/openai/v1/...` 路由都按
   **id** 查找、不按 name 回退——启动横幅却打印 name 型 URL,按其访问一律 404。解法:
   `config_l3.py` 里所有 Guard **显式 `id=name`**。

另有一个客户端小改动:guardrails-api 0.4.x 对 `GET /guards/` 返回 **307 重定向**到 `/guards`,
`main.py` 的探活改为 `follow_redirects=True`。

## 对架构师的结论

1. **软约束 vs 确定性护栏**:提示词里的"别做 X"依赖模型自觉;guardrails 把它变成进 LLM 前/后的
   **代码级校验**,不受模型漂移影响。这是"可靠"二字的落点。
2. **护栏该是独立服务**:把 guard 跑成服务器 + OpenAI 兼容端点,应用只需把 `base_url` 指过去就
   接入——护栏与业务解耦,可独立升级、可复用给多个应用。这跟你之前问的 AI Gateway 思路一致。
3. **`on_fail` 是产品决策**:EXCEPTION(硬失败,适合高危)vs FIX/refrain(优雅降级,适合体验优先),
   同一个 validator 按场景选动作。
4. **版本治理:优先升级,不复刻旧锁**:0.5.3 那套旧 pin 处处是坑(预装 workaround、压 click、
   FIX 路径 bug),升到 0.10.2 后全部消失、FIX 还修好了——代价只是两个新坑(启动入口 + id=name),
   且都有干净解法。护栏框架这类快速迭代的安全组件,复刻供应商冻结的旧栈通常比升级更贵。

## 文件

```
main.py                      # 客户端:A 无护栏 / B EXCEPTION / C FIX 三路径(轻依赖)
config_l3.py                 # guardrails 服务器配置:ColosseumDetector + colosseum_guard(_2)
requirements.txt             # 客户端轻依赖(openai/fastembed/numpy/httpx)
requirements-guardrails.txt  # 服务器重依赖(guardrails-ai 0.10.2 + guardrails-api 0.4.3)
helpers/rag.py               # 本地 RAG(client 可注入:直连 DeepSeek 或指向服务器)
helpers/__init__.py          # 导出 LocalRAG
shared_data/                 # 知识库(含机密文档 project_colosseum.md)
config.py                    # 原课程完整 config(含 L4–L8 的 hub 校验器,作参照)
helper.py / Lesson_3.ipynb   # 原课程 helper 与 notebook(参照)
```

> 说明:`config.py`(原课程)里还定义了 hallucination/pii/topic/competitor/final 等 guard,那些
> 依赖 guardrails hub 上的模型(需 hub API key + 下载 spacy/PII 模型),属于 **L4–L8**,不在 L3 的
> 示例逻辑内,故本课 `config_l3.py` 只保留 L3 实际用到的 colosseum 两个 guard。
