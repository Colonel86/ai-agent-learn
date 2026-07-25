# 环境搭建(一次性)

栈:DeepSeek(OpenAIGenericClient)+ fastembed 本地 embedding(自定义 EmbedderClient)+ Neo4j docker。

```bash
cd "agent/courses/memory/12d-Zep Graphiti Hands-On/code"

# 1. 虚拟环境
uv venv --python 3.11 .venv
source .venv/bin/activate
uv pip install -r L1/requirements.txt

# 2. Neo4j(带 Browser 可视化,学习期首选;端口 7474/7687)
docker run -d --name graphiti-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/graphiti123 \
  neo4j:5.26
# Browser: http://localhost:7474 (账号 neo4j / graphiti123)

# 3. 密钥
cp .env.example .env   # 填 DEEPSEEK_API_KEY
```

## 三个适配点(graphiti-core 0.29.2 源码核实过)

1. **LLM**:`OpenAIGenericClient(config=LLMConfig(...), structured_output_mode="json_object")`——
   框架原生支持 json_object 降级,DeepSeek 的 json_schema 坑(12 系列坑 1)不需要 hack;
2. **Embedder**:graphiti 没有 fastembed 集成,但 `EmbedderClient` 接口只有 `create`/`create_batch` 两个方法,
   `common.py` 里 30 行包一个 `FastEmbedEmbedder`(bge-small-zh-v1.5,与 12c 同款);
3. **Reranker**:默认 `OpenAIRerankerClient` 依赖 OpenAI 专属 `logit_bias` token ID(6432/7983),DeepSeek 接不了——
   L1 用 `common.py` 里的余弦相似度极简 reranker 替代,L3 换正经方案。

## L1 实跑发现(2026-07,graphiti-core 0.29.2 + deepseek-v4-flash)

- **端到端可用**:json_object 模式下 DeepSeek 的实体/关系/时序抽取全部正常,未触发结构化输出问题;
- **摄入耗时**:单个 episode 约 7s(mem0 的 add 约 1–2s)——图谱路线写入贵,实测坐实;
- **中文保真**:实体和事实都以中文存储("用户—住在→杭州"),对比 mem0 中文进英文出——Graphiti 的抽取 prompt 不改写语言,跨语言检索损耗更小;
- **valid_at 与 created_at 实测分离**:valid_at 取自 reference_time(事件时间),created_at 是写库时间(摄入时间),bi-temporal 不是纸面概念;
- **无害警告**:检索 Cypher 引用 `e.episodes` 属性触发 neo4j 驱动警告,common.py 已静音。

## 其它注意

- graphiti 全 async(`await graphiti.add_episode(...)`),demo 统一 `asyncio.run(main())`;
- `max_coroutines` 压到 5,避免撞 DeepSeek 并发限流;
- 图数据在 Neo4j 容器里,重置实验用 main.py 的 `--reset`(清空整库),或 `docker rm -f graphiti-neo4j` 重来;
- 摄入比 mem0 慢得多是**预期行为**(每个 episode 抽实体+关系+时序判断,多次 LLM 调用)——这本身就是面试答案的一部分。
