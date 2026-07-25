# Guardrails 课 L1-L8 —— 统一环境(单 venv)

2026-07-25 起,L1-L8 及全部 hub 变体合并为**一个代码项目、一个 venv**(`code/.venv`,
guardrails **0.10.2** 现代栈),取代原先 7 个分散 venv(约 6.2GB → 约 2.8GB)。
各课入口不变:进对应目录跑各自的 `main.py` / `main_hub.py`。

## 一次性搭建

```bash
cd ".../code"
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r requirements-unified.txt
# hub 校验器 + spacy 模型(需 ~/.guardrailsrc 的 Hub token,见 HUB.md):
TOKEN=$(grep '^token=' ~/.guardrailsrc | cut -d= -f2)
.venv/bin/pip install guardrails-grhub-detect-pii guardrails-grhub-competitor-check \
  guardrails-grhub-provenance-llm tryolabs-grhub-restricttotopic \
  --index-url "https://__token__:${TOKEN}@pypi.guardrailsai.com/simple" \
  --extra-index-url https://pypi.org/simple
.venv/bin/pip install \
  https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl \
  https://github.com/explosion/spacy-models/releases/download/en_core_web_trf-3.8.0/en_core_web_trf-3.8.0-py3-none-any.whl
```

## 运行

```bash
cd L4 && ../.venv/bin/python main.py            # 免服务器课:L1、L4
cd L5 && ../.venv/bin/python main_hub.py        # hub 变体:L5/L6/L7/L8(原 .venv-hub 已并入)

# 服务器课(L3/L5/L6/L7/L8):先起服务器再跑 main.py
cd L5 && ../.venv/bin/guardrails-api start --config config_l5.py --env server.env --port 8000
cd L5 && ../.venv/bin/python main.py            # 另一个终端
```

## 0.5.3 → 0.10.2 迁移实录(2026-07-25,全课实测通过)

自定义 validator(`@register_validator` + `Validator` 基类 + `validate(value, metadata)`)
**零代码改动**——这套 API 两版间完全稳定。坑全在 guardrails-api 0.0.1 → 0.4.3 的服务器层:

1. **config 加载不带 sys.path**:0.4.x 以文件路径 import config,不把其目录加入 `sys.path`,
   config 里 `from helpers.x import ...` 直接炸 → 各 config 顶部加了
   `sys.path.insert(0, dirname(__file__))` 自举。
2. **guard 按 `id` 注册、按 URL 的 name 查找**:`Guard(name="x")` 不显式传 `id` 时 id 是随机
   UUID,请求永远 404 → 一律 `Guard(id="x", name="x")`。
3. **同步 Guard 会被序列化重建**(最深的坑):0.4.x 对同步 Guard 走
   `AsyncGuard.from_dict(guard.to_dict())`,自定义 validator 构造参数(如 L5 的 `sources`)
   不在序列化契约里就**静默丢失**(重建后为 None → 500),且**每个请求都重建**(重新加载
   模型,慢)→ 服务器 config 一律用 **AsyncGuard**,直接持有活实例,双问题同时消失。
4. **杂项**:`/guards/` 返回 307(健康检查要 follow_redirects);otel 会向不存在的
   collector 疯狂重试(server.env 加 `OTEL_SDK_DISABLED=true`)。

⚠️ 教训:demo 的 except 分支把任何异常都当"护栏拦截成功"打印,曾把 404/500 演成假绿。
**判定服务器端护栏是否生效,要看服务器日志的状态码 + 报错文本里的业务语义**
(如 `banned topics: ['politics']`),不能只看客户端文案。

## 历史文件说明

- 各课 `requirements*.txt`(L 目录内)与 README 里的 `.venv-guardrails` 命令为旧分散环境
  的历史记录;现只用本目录 `requirements-unified.txt` + `.venv`。
- `requirements.txt` / `requirements-lock.txt`(本目录)是课程 2024 原始冻结锁,仅作参照。
- L3 的两版对比(0.5.3 旧栈的坑)见 `L3/README.md`;hub 校验器详情见 `HUB.md`。
