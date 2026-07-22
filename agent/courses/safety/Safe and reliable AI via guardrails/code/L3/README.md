# L3 · Building your first guardrail —— 本地可运行版(真 guardrails)

对照 DeepLearning.AI《Safe and reliable AI via guardrails》L3。**严格按课程示例逻辑用真
guardrails**(不做等价替代):自定义 `ColosseumDetector` validator → 包成 `Guard` → 跑在
**guardrails 服务器**上 → guarded client 指向服务器,LLM 调用在进模型前被 guard 拦截。

与前面的红队课不同,这里没有把 guardrails 换成手写等价物——用的就是 `guardrails-ai==0.5.3`
本体、真的把服务器跑起来。只在**接入层**做了本地化:裁判/生成 LLM 走 DeepSeek(litellm 的
`deepseek/` 路由)、embedding 走本地 fastembed。

## 架构:轻客户端 + 重服务器(两个 venv)

```
main.py (客户端, .venv)  --HTTP-->  guardrails 服务器 (.venv-guardrails)  --litellm-->  DeepSeek
   └ 直连 DeepSeek 也走这个客户端(无护栏对照)          └ config_l3.py 定义 guard
```

- **客户端**(`main.py`)只用 openai/fastembed/numpy/httpx,**不含 guardrails**,轻。
- **服务器**(`guardrails start`)才装 guardrails 那套重依赖,单独 3.12 venv。

## 运行(两步)

**第一步:起 guardrails 服务器**(单独的 3.12 venv;guardrails 只支持 Python <3.13):

```bash
/opt/homebrew/bin/python3.12 -m venv .venv-guardrails
.venv-guardrails/bin/pip install -r requirements-guardrails.txt

# 准备服务器环境文件:litellm 用 deepseek/ 路由,需要 DEEPSEEK_API_KEY
printf 'DEEPSEEK_API_KEY=<你的key>\nOPENAI_API_KEY=<你的key>\n' > server.env

.venv-guardrails/bin/guardrails start --config config_l3.py --env server.env --port 8000
```

**第二步:另开一个终端,跑客户端**:

```bash
cp .env.example .env          # 填 OPENAI_API_KEY(DeepSeek 的 key)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

(main.py 会先探活服务器;没起服务器则只跑 A 段无护栏对照,并提示如何起服务器。)

## 演示三条路径 & 实测(deepseek-chat,2026-07)

| 路径 | 说明 | 实测 |
|---|---|---|
| **A. 无护栏**(直连 DeepSeek) | 用"续写"套路诱导泄漏机密 Project Colosseum | ✅ 这次 DeepSeek 守住了(对齐较好);但软约束不可靠,换模型/措辞就可能破防 |
| **B. colosseum_guard**(EXCEPTION) | 含 `colosseum` 的输入 | 🛡️ **确定性拦截**:`BadRequestError: Colosseum detected`,请求根本没进 LLM |
| B. 同上 + 正常问题 | "What pizza types do you have?" | ✅ 正常经 DeepSeek 回答(列出菜单) |
| **C. colosseum_guard_2**(FIX) | 含 `colosseum` 的输入 | ⚠️ 仍以 400 返回(见下"FIX 说明") |

**核心对比 A vs B**:同一条"别聊 Colosseum"的规则,写进系统提示词(A)是**软约束**、一个续写
套路就可能绕过;做成 guardrails 服务器上的 **validator**(B)是**确定性护栏**、在进 LLM 之前按
代码规则拦截,和模型是否"听话"无关。这就是"第一个 guardrail"的意义。

## 本地化时踩的坑(真 guardrails 0.5.3 这套旧 pin 的通病)

严格用真 guardrails 就得直面这套旧依赖的坑,已全部在 requirements/启动步骤里规避:

1. **Python 版本**:guardrails 只支持 `<3.13`,本机默认 3.13 → 必须用 3.12 建 `.venv-guardrails`。
2. **服务器自举 bug**:`guardrails start` 会自动 pip 安装 guardrails-api,但拼的版本号非法
   (`guardrails-api>="^0.0.0a0"`,Poetry 风格漏进 pip)→ 被现代 pip 拒绝。解法:**预装**
   `guardrails-api==0.0.1`(已写进 requirements-guardrails.txt)。
3. **click 冲突**:新版 click(8.2+)与 guardrails 0.5.3 的 typer CLI 冲突,报
   `Secondary flag is not valid for non-boolean flag`,CLI 直接崩 → 钉死 `click<8.2`。
   (注:装 guardrails-api 会把 click 顶回新版,需最后再 `pip install "click<8.2"` 压一次。)
4. **AsyncGuard 同步调用 bug**:课程原 `config.py` 用 `AsyncGuard`,但 guardrails-api 0.0.1 的
   非流式 `/openai/v1/chat/completions` handler 是**同步**调用 `guard(**payload)` 后立刻读
   `guard.history.last`——对 AsyncGuard 同步调用只拿到协程、不执行、history 为 None → 500。
   `config_l3.py` 里改用同步 `Guard`(validator/on/on_fail/服务器全部照旧,仅换 Guard 类型)。

### FIX 说明(C 路径为何不是"静默替换")

课程视频里 FIX 版应"无错误地"返回 `fix_value`。但作用在**输入消息**上的 FIX,在本课 pinned 的
guardrails-api 0.0.1 上仍以 `400 Message history validation failed` 返回,不是静默替换。课程
notebook 本身也注明"返回消息可能与视频不完全一致"。**这是真实服务器行为,未做美化。**

## 对架构师的结论

1. **软约束 vs 确定性护栏**:提示词里的"别做 X"依赖模型自觉;guardrails 把它变成进 LLM 前/后的
   **代码级校验**,不受模型漂移影响。这是"可靠"二字的落点。
2. **护栏该是独立服务**:把 guard 跑成服务器 + OpenAI 兼容端点,应用只需把 `base_url` 指过去就
   接入——护栏与业务解耦,可独立升级、可复用给多个应用。这跟你之前问的 AI Gateway 思路一致。
3. **`on_fail` 是产品决策**:EXCEPTION(硬失败,适合高危)vs FIX/refrain(优雅降级,适合体验优先),
   同一个 validator 按场景选动作。
4. **旧依赖本身就是"不可靠"的反面教材**:这套 0.5.3 装起来处处是坑(见上)。工程上要么锁死整套
   lock 文件、要么用更新版本——这也是为什么真实项目里护栏框架的版本治理很重要。

## 文件

```
main.py                      # 客户端:A 无护栏 / B EXCEPTION / C FIX 三路径(轻依赖)
config_l3.py                 # guardrails 服务器配置:ColosseumDetector + colosseum_guard(_2)
requirements.txt             # 客户端轻依赖(openai/fastembed/numpy/httpx)
requirements-guardrails.txt  # 服务器重依赖(guardrails-ai 0.5.3 + guardrails-api 0.0.1 + click<8.2)
helpers/rag.py               # 本地 RAG(client 可注入:直连 DeepSeek 或指向服务器)
helpers/__init__.py          # 导出 LocalRAG
shared_data/                 # 知识库(含机密文档 project_colosseum.md)
config.py                    # 原课程完整 config(含 L4–L8 的 hub 校验器,作参照)
helper.py / Lesson_3.ipynb   # 原课程 helper 与 notebook(参照)
```

> 说明:`config.py`(原课程)里还定义了 hallucination/pii/topic/competitor/final 等 guard,那些
> 依赖 guardrails hub 上的模型(需 hub API key + 下载 spacy/PII 模型),属于 **L4–L8**,不在 L3 的
> 示例逻辑内,故本课 `config_l3.py` 只保留 L3 实际用到的 colosseum 两个 guard。
