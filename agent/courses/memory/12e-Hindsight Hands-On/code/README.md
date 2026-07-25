# 环境搭建(一次性)

Hindsight 是 client-server 架构,但 Python 有 **embedded 模式**:`HindsightServer` 在进程内拉起服务(嵌入式 PostgreSQL pg0 存数据),**不需要 docker、不需要任何外部服务**——这是三门课里工程形态最省事的。

```bash
cd "agent/courses/memory/12e-Hindsight Hands-On/code"

uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -r L1/requirements.txt   # hindsight-all 体积不小,含 pg0 + 本地模型运行时

cp .env.example .env   # 填 DEEPSEEK_API_KEY
```

## 零适配点(对比 12c/12d 的爽点)

- **LLM**:`HINDSIGHT_API_LLM_PROVIDER=deepseek` **原生支持**,不用 OpenAI 兼容绕行;
- **结构化输出**:默认走"schema 进 prompt + json_object"软模式(`STRICT_SCHEMA=false`),DeepSeek 无压力——12 系列坑 1 官方帮你趟平了;
- **embedding**:默认 `local` provider + `BAAI/bge-small-en-v1.5`,和我们的标准栈同款,模型自动从 HF 下载(记得镜像);
- **中文**:`HINDSIGHT_API_LLM_OUTPUT_LANGUAGE=Chinese` 强制所有生成产物(事实/观察/reflect 回答)用中文——mem0 中文进英文出的问题它有官方开关。

## 预埋的坑位处理

1. `HF_ENDPOINT=https://hf-mirror.com`:embedding + cross-encoder 模型首启自动下载,必须走镜像(main.py 已在 import 前设置);
2. `HINDSIGHT_API_EMBEDDINGS_LOCAL_FORCE_CPU=true`:官方自带的 macOS MPS 规避开关,我们这台机器必开;
3. pg0 数据默认落在 `~/.pg0`;重置实验删 bank 即可,不用动数据目录;
4. `HINDSIGHT_API_LLM_MAX_CONCURRENT` 默认 32,压到 8 防 DeepSeek 限流。

## 实跑发现(2026-07,hindsight 0.8.4 + deepseek-v4-flash)

- **HF 下载被阻断的绕行**(本机 HF CDN 连 SSL 都握不上,镜像又对该 repo 308 回源):
  ① embedding 改用 `EMBEDDINGS_PROVIDER=onnx` 指向本地模型文件(`code/models/fast-bge-small-zh-v1.5`,复用 12c/12d 已下载的 fastembed 产物,BGE 系记得 POOLING=cls + 前缀留空);
  ② reranker 改 `RERANKER_PROVIDER=rrf`,免掉 cross-encoder 下载。两处都已预置在 L1 main.py;
- **HindsightServer 构造坑**:LLM 参数必须显式传构造函数(默认 groq,**不读** `HINDSIGHT_API_LLM_*` 环境变量);首启初始化 pg0 很慢,要 `start(timeout=600)` 而不是 `with` 默认 30s;
- **retain 实测 1.5–5.5s**/条,和 mem0 同量级,比 Graphiti 的 7s 轻;
- **写入即见 observation**:三条 retain 之后 recall 结果里已经出现 `type: observation` 的条目——后台 consolidation 是自动的,不用显式调用(L4 主角提前露脸);
- **TEMPR 可观察性极好**:recall 返回的每条记忆自带 `scores: {final, reranker, semantic, keyword}` 分解——L3 解剖检索就靠它;
- **中文开关生效**:`OUTPUT_LANGUAGE=Chinese` 下事实全部中文存储;
- **reflect 是重操作**:单次 reflect 输入 token 1.1 万(把大量记忆拉进上下文推理),别在热路径上滥用。

## 每课产物

embedded server 起在随机端口(`server.url`),UI 不随 embedded 模式提供;要看管理界面用 docker 形态(L7 再说)。
