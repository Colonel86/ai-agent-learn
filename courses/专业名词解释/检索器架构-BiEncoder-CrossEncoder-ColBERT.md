# 检索器架构：Bi-Encoder / Cross-Encoder / ColBERT

> 场景：RAG / 语义搜索的「召回 → 精排」两阶段管线中，如何对 query 与 doc 计算相关性。
> 核心区别只有一个问题：**query 和 doc 的交互发生在什么时候？**

---

## 〇、一图看懂三者位置

按「交互时机」排在一条光谱上：

```
Bi-Encoder      ：交互最晚——各自压成单向量后才点积       (no-interaction，最快最糙)
ColBERT         ：交互居中——各自编码成 token 向量矩阵，末端做 MaxSim (late-interaction)
Cross-Encoder   ：交互最早——输入端就拼接做 attention    (full-interaction，最慢最准)
```

典型管线（漏斗式，把算力花在刀刃上）：

```
全库(百万+) ──Bi-Encoder / ANN──► Top-K(粗排, 快, 够全)
                                      │
                          Cross-Encoder 或 ColBERT 逐对/逐候选打分
                                      │
                                  Top-N(精排, 准)
```

---

## 一、Bi-Encoder（双塔编码器）—— 召回阶段主力

query 和 doc **分别独立编码**，编码时彼此「看不见」，最后只用一个向量的点积/余弦度量相关性。

```
query ──► Encoder ──► 向量 q  ┐
                              ├──► cos(q, d) 相似度
doc   ──► Encoder ──► 向量 d  ┘
```

- ✅ **优点**：doc 向量可**离线预计算**存进向量库，检索时只算一次 query 编码 + ANN（近似最近邻），极快，能在亿级文档上跑。
- ❌ **缺点**：把整段文本压成**单个固定向量**，信息有损；query 与 doc 的词级交互（谁回答了谁）全部丢失。**召回准，精排不够准。**

---

## 二、Cross-Encoder（交叉编码器）—— 精排阶段主力

把 query 和 doc **拼接在一起**送进同一个 Transformer，全程自注意力让两者在每一层做交叉交互。

```
输入:  [CLS] query 文本 [SEP] doc 文本 [SEP]
        │
        ▼
   Transformer（query 每个 token 都能 attend 到 doc 每个 token，反之亦然）
        │
        ▼
   取 [CLS] 输出 ──► 线性层 ──► 一个标量分数(相关性)
```

- ✅ **优点**：精度最高。模型不是「分别理解再比较」，而是「放在一起直接判断这段 doc 是否回答了这个 query」。
- ❌ **缺点**：doc 必须和 query 拼起来才能编码，**无法预建索引**——每来一个 query，要对 K 个候选各做一次完整前向。所以**做不了一级检索**，只能在小 K（几十～几百）上精排。
- 常见实现：`sentence-transformers` 的 `CrossEncoder`、Cohere Rerank、BGE-reranker、Jina Reranker。

---

## 三、ColBERT（Late Interaction）—— 介于两者之间

**C**ontextualized **L**ate Interaction over **BERT**。核心改动：编码时**不池化（no pooling）**，保留每个 token 的向量。

```
query ──► BERT ──► [q1, q2, ..., qNq]   向量矩阵 Nq × dim（不是 1 个向量）
doc   ──► BERT ──► [d1, d2, ..., dM]    向量矩阵 Md × dim
```

query 和 doc **仍然独立编码**——所以 **doc 的 token 向量可离线预计算并建索引**（这是它能做检索的关键）。

### 打分函数：MaxSim（最大相似度求和）

交互推迟到最后一步，且只用廉价向量运算、不过 Transformer：

```
score(q, d) = Σ        max       sim(q_i, d_j)
          (每个 query token i)(在所有 doc token j 中取最相似的)
```

直觉：query 的每个词都去 doc 里「找自己的最佳落点」，doc 能为更多 query 词提供强匹配，分就越高 —— 找回了 Bi-Encoder 丢掉的 token 级细粒度匹配。

```
        d1   d2   d3 ... dM
   q1 [ .1   .9*  .2 ... ]   → max = .9
   q2 [ .8*  .1   .3 ... ]   → max = .8
   q3 [ .2   .3   .7* ... ]   → max = .7
                              ─────────────
                       score = .9+.8+.7 = 2.4
```

### 它如何真的能做一级检索（ColBERTv2 / PLAID）

1. 把所有 doc 的 token 向量灌进向量索引（量化压缩 + ANN）。
2. 检索时，用 query 的每个 token 向量分别做 ANN，召回一批候选。
3. 只对候选算完整 MaxSim 做精排。

- ❌ **主要代价是存储**：每篇 doc 不再是 1 个向量，而是几十～几百个 token 向量，即使量化压缩，索引体积仍远大于 Bi-Encoder。
- 需要专门的 late-interaction 索引（PLAID 等）；现 Qdrant / Vespa / Weaviate 已支持 multi-vector。

---

## 四、三者对比总表

| 维度 | Bi-Encoder | ColBERT | Cross-Encoder |
|---|---|---|---|
| 交互时机 | 最晚（单向量点积） | 居中（末端 MaxSim） | 最早（输入端 attention）|
| token 级交互 | ❌ 丢失 | ✅ MaxSim 保留 | ✅ attention 最强 |
| doc 能否离线预计算 | ✅ 1 向量/doc | ✅ Md 向量/doc | ❌ 不能 |
| 能否做一级检索 | ✅ | ✅ | ❌ 只能精排 |
| 交互成本 | 1 次点积 | 矩阵相似度（廉价）| K 次完整前向（昂贵）|
| 精度 | 中 | 高（逼近 Cross） | 最高 |
| 主要代价 | 精度有损 | **索引存储膨胀** | **延迟高、不可索引** |

---

## 五、架构师视角的取舍

1. **K 怎么定**：K 太小，召回阶段漏掉的好文档救不回来；K 太大，精排延迟线性上涨。常见折中 K=50~200。
2. **延迟预算**：Cross-Encoder 每候选一次前向，是 rerank 的主要延迟来源 —— 可用更小 reranker、batch 推理、GPU 压。
3. **要不要上 rerank**：领域窄、query 简单时 Bi-Encoder 召回已够，rerank 收益有限；query 与 doc 语义关系微妙、需细粒度判别时，Cross-Encoder 提升最明显。
4. **何时选 ColBERT**：语料大且需精确词级匹配（长尾实体、专有名词、代码检索）→ 收益大；语料小或已有「Bi + Cross」且延迟可接受 → 未必值得引入它的存储复杂度。
5. **三者不互斥**：实务常见 **Bi-Encoder 粗召回 → ColBERT 或 Cross-Encoder 精排** 的组合。ColBERT 适合「既要可索引、又要比单向量准」的中间档需求。

---

## 一句话总结

- **Bi-Encoder**：独立编码成单向量、点积比较，快但有损，做召回。
- **Cross-Encoder**：拼接后联合 attention，精度最高但不可索引、必须逐对现算，做精排。
- **ColBERT**：独立编码成 token 向量矩阵、末端用 MaxSim 交互，在保留 doc 可离线索引的前提下逼近 Cross-Encoder 精度，代价是索引存储显著变大。
