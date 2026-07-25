# 环境搭建(一次性)

沿用课程 12 系列的本地化标准栈:DeepSeek API(LLM)+ fastembed(本地 embedding,纯 CPU)+ Chroma(嵌入式向量库,零服务)。

```bash
cd "agent/courses/memory/12c-Mem0 Hands-On/code"

# 1. 独立虚拟环境(Python ≥3.10,mem0 的硬要求)
uv venv --python 3.11 .venv
source .venv/bin/activate

# 2. 依赖
uv pip install -r L1/requirements.txt

# 3. 配置密钥
cp .env.example .env   # 填入 DEEPSEEK_API_KEY
```

## .env 说明

| 变量 | 说明 |
|---|---|
| `DEEPSEEK_API_KEY` | mem0 的 deepseek provider 读这个变量(不是 OPENAI_API_KEY) |

## 已预埋的坑位处理(对应 12 系列经验)

1. **HF 直连卡死**:每课 main.py 开头都在 import 之前 `os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")`,fastembed 下载模型走镜像;
2. **中文语料**:embedding 用 `BAAI/bge-small-zh-v1.5`(512 维,fastembed 支持,ONNX 纯 CPU 不碰 MPS)——demo 对话是中文,zh 模型检索质量远好于惯用的 bge-small-en;
3. **temperature=0**:消解决策类 demo 需要可复现;
4. **DeepSeek json 模式**:mem0 的抽取/消解走 `json_object` 而非 `json_schema`,DeepSeek 支持,L1 实跑已验证无需 12 课那种子类 hack。

## 实跑发现(2026-07,mem0ai 2.0.12)

- **API 变化**:2.x 起 `get_all()`/`search()` 不再接受顶层 `user_id`,必须 `filters={"user_id": ...}`(`add()` 仍收顶层 `user_id`);网上大量教程还是旧签名,以本课代码为准;
- **记忆存成英文**:mem0 内部抽取 prompt 是英文,中文对话进去、英文事实出来;bge-small-zh 对英文也能检索(L1 中文查询命中 score≈0.51),但这是个跨语言损耗点;
- **Chroma 无 BM25**:启动时明确警告 hybrid 检索被禁用、只剩语义相似度——要混合检索得换 qdrant/pgvector(L6 的另一个动机);
- **消解不是必然发生**:L1 第④步"搬到上海"实测走了 ADD 而非 UPDATE,矛盾记忆并存(详见 L1 README 观察点④)。

## 每课产物

每课运行会在该课目录下落两个本地文件(已 gitignore):

- `chroma_db/`:向量库(记忆的语义索引)
- `history.db`:SQLite,**每条记忆的完整演化事件流(ADD/UPDATE/DELETE)**——这是观察 mem0 写路径的显微镜
