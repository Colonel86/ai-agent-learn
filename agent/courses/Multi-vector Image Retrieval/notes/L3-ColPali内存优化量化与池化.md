# L3 · ColPali 内存优化：量化（quantization）与池化（pooling）

> 课程：Multi-vector Image Retrieval（DeepLearning.AI × Qdrant，C2）
> 本课任务：把 L2 那个"百万文档 = 500 GB"的内存硬伤治一治。三类手段——**标量/二值量化**（压每个维度的字节数）与**行/列池化 + 层次池化**（压向量的个数），在同一个 Qdrant collection 里用 7 个命名向量并排跑，用"与原始 ColPali 结果的重合度"当 precision 指标横向比较。核心命题：**能省多少内存而不牺牲检索质量？**

## 0. 本课定位

ColPali 向量里有大量冗余（比如整片同色背景 patch）。优化沿两个正交方向压：

```
方向一：压「每个数字」的大小   → 量化（scalar / binary）
方向二：压「向量的个数」        → 池化（row / column / hierarchical）
两者可叠加使用
```

数据集换成来自多门 DeepLearning.AI 课程的**幻灯片页**，每页约 1031 个 token 向量（一致）。

## 1. 三类优化技术总览

| 技术 | 压什么 | 做法 | 压缩比 |
|---|---|---|---|
| Scalar Quantization | 每维字节 | float32(4B) → int8(1B) | 4× |
| Binary Quantization | 每维字节 | float32(4B) → 1 bit | 32× |
| Row / Column Pooling | 向量个数 | 按行/列对 patch 求平均 | 1024 → 32 |
| Hierarchical Pooling | 向量个数 | 相似 patch 聚类后各簇求平均 | 按 pool_factor（2× 即减半） |

## 2. 量化：把每个维度压小

### 2.1 Scalar Quantization（标量量化，4×）

把 float32 映到 int8：为**每一维**在整个数据集上学最小/最大值，再把这段连续范围**线性映射到 0–255 的整数桶**。

```python
# 概念演示：某维在数据集上范围 [-0.8, 1.2]，值 0.2 落在哪个桶？
value_space = np.linspace(-0.8, 1.2, 256)
bucket_index = np.argmin(np.abs(value_space - 0.2))   # ≈ 128
```

关键性质：**dataset-aware（数据集相关）**——必须分析所有向量（或有代表性的样本）才能定出每维的范围。好在 Qdrant 内部自动处理：只在 collection 级配置量化、照常发原始 float 向量，引擎自动压缩转换。

### 2.2 Binary Quantization（二值量化，32×）

更激进：每维 float32 → **1 bit**。规则极简——**正值→1，负值或零→0**：

```python
binary_vector = (simple_vector > 0).astype(int)   # [-0.3, 0.7, ...] -> [0, 1, ...]
```

好处：相似度计算退化成高效的**位运算**。适用条件：embedding **以 0 为中心、分布相对对称**时效果好（归一化的神经网络输出常满足）。代价：这种极端压缩有精度损失（trade-off）。同样由 Qdrant 内部处理。

## 3. 池化：把向量的个数压少

利用 ColPali 的**空间结构**——文档图被切成 **32×32 patch 网格**。先把展平的向量重塑回网格：

```python
patch_size, model_dim = 32, 128
def embeddings_grid(image_embeddings):
    # 用 image_mask 隔离出 1024 个 image patch 向量后，重塑成 32×32×128
    return image_embeddings.reshape((patch_size, patch_size, model_dim))
```

### 3.1 Row / Column Pooling（行/列池化）

沿网格的行或列求平均，保留空间关系的同时把向量数从 1024 砍到 **32**：

```python
def row_mean_pooling(grid):    return grid.mean(axis=1)   # 32 个向量，捕捉横向模式
def column_mean_pooling(grid): return grid.mean(axis=0)   # 32 个向量，捕捉纵向模式
```

### 3.2 Hierarchical Token Pooling（层次池化，更聪明的池化）

用**层次聚类**把相似的 patch 向量分组，每簇求平均成一个代表向量。相似 patch（如整片同色背景）会被聚到一起。ColPali engine 库自带实现：

```python
from colpali_engine.compression.token_pooling import HierarchicalTokenPooler
pooler = HierarchicalTokenPooler()

def hierarchical_token_pooling(arr, pool_factor=2):
    arr_tensor = torch.from_numpy(arr[np.newaxis, :, :])
    pooled = pooler.pool_embeddings(arr_tensor, pool_factor=pool_factor)
    return pooled.cpu().detach().numpy()[0]

# 1031 个向量 → pool_factor=2 → 515 个（约减半）
```

**pool_factor** 决定簇数：9 个 patch、factor=2 → ⌊9/2⌋=4 个簇。**注意**：池化拿到的只是一串 embedding，**不含任何空间信息**——所以簇内 patch 不必相邻（也无从判断相邻），纯按向量相似度聚类。这与 row/column 池化（依赖空间网格）本质不同。

> **对比 Qdrant C1《Retrieval Optimization》**：scalar/binary 量化本就是 C1 里给普通 dense（bi-encoder）向量用的老技术，这里**原样搬到多向量的每个 token 向量上**——Qdrant 引擎内部处理这一点没变。真正的新东西是**池化**：它利用了 ColPali 特有的"patch 网格"空间结构，是 dense 单向量世界里不存在的优化维度。选型时的分工：量化 = 通用、零预处理、collection 级开关；池化 = 多向量专属、需改变向量本身。

## 4. 并排实验：7 个命名向量同台比

在**一个** collection 里配 7 个命名向量，各代表一种方案，同一文档写 7 份表示，直接横比检索质量与内存：

```python
client.create_collection(collection_name, vectors_config={
    "original":         VectorParams(size=128, distance=DOT,
                          multivector_config=MultiVectorConfig(MAX_SIM),
                          hnsw_config=HnswConfigDiff(m=0), on_disk=True),
    "scalar_quantized": <同上 + quantization_config=ScalarQuantization(INT8)>,
    "binary_quantized": <同上 + quantization_config=BinaryQuantization(always_ram=True)>,
    "hierarchical_2x":  <同 original>,
    "hierarchical_4x":  <同 original>,
    "row_pooled":       <同 original>,
    "column_pooled":    <同 original>,
})
```

要点：

- 量化在**命名向量**级别开（不是整个 collection），且 Qdrant 内部处理——所以 upsert 时 `scalar_quantized` / `binary_quantized` 都直接写 `original` 原始向量，引擎自己压；池化类则要写**预先池化好**的向量。
- **query 侧不做池化**：query 序列本就短；行/列池化对文本也没意义（文本无空间关系）；量化由 Qdrant 内部处理，所以对所有方案，查询都直接用原始 query embedding 打过去。

## 5. 结果：precision@5

**precision 的定义**：某方案 top-k 里有多少比例的文档**与 baseline（original 原始向量）返回的重合**——衡量优化保留了多少检索准确度（**不看顺序，只看相关与否**）。三个 query（`coffee mug` / `size vs performance tradeoff` / `one learning algorithm`）逐个看，再看全局平均：

| 方法 | 表现（相对 original baseline） |
|---|---|
| **Scalar Quantization** | 三个 query **始终**返回与 baseline 完全相同的文档集——最稳，且**零预处理、仅 collection 级配置**，最有前途 |
| **Hierarchical Token Pooling** | 显著好于行/列池化，且 **pool_factor 影响不大**（2× 与 4× 差不多）——说明还能压更狠 |
| **Binary Quantization** | 不是最好，但**对内存和处理速度影响巨大（32×）**，某些场景值得考虑 |
| **Row Pooling** | 一般，多个 query 掉链子 |
| **Column Pooling** | **最差**，常连一个 baseline 标为相关的文档都选不出来 |

> **架构师视角**：这张表就是一份现成的**内存 vs 质量取舍决策卡**。反直觉结论有两个：(1) 最朴素的 scalar quantization 反而质量最稳、还零预处理——**先上量化，别急着上花哨的池化**；(2) 空间池化里 hierarchical（按相似度聚类）远胜 row/column（按几何行列强切），因为文档语义不沿行列对齐。讲师还点明可**叠加**：hierarchical 池化后再叠 scalar 量化，只要质量仍可接受。但反复强调：**三个手挑 query 不算 benchmark**，真实评估要广、要建 ground truth、且高度依赖你自己的数据集——"experiment with different techniques on your data"。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 两个正交方向 | 量化压"每维字节"，池化压"向量个数"，可叠加 |
| Scalar Quantization | float32→int8，4×，dataset-aware，Qdrant 内部处理，质量最稳 |
| Binary Quantization | float32→1bit，32×，正→1/非正→0，退化为位运算，精度有损 |
| Row/Column Pooling | 沿网格行/列求平均，1024→32，依赖空间结构，本课表现差 |
| Hierarchical Pooling | 相似 patch 聚类后求平均，无空间信息，pool_factor 影响小，表现好 |
| 并排比较法 | 一个 collection 配 7 个命名向量，precision=与 baseline 重合度 |
| 结论 | 先上 scalar 量化；池化选 hierarchical；量化+池化可叠加；评估依赖你的数据集 |

> **记忆点（引出 L4）**：量化和池化把 ColPali 的内存压下来了，**但没解决扩展性的根——MaxSim 非对称导致仍然用不了 HNSW**，大库检索还是绕不开慢速全扫描。L4 的 **MUVERA** 换个思路：把**变长的向量序列转成一个定长向量**，从而重新解锁 HNSW / ANN 那套成熟的近似搜索，同时保住多向量的细粒度匹配优势——把多向量与单向量的长处合到一起。

## 与我的资产映射

- 检索层选型：`agent/skills/agent-selection/3-retrieval.md`（多向量落地的成本工程——量化/池化是"选了 ColPali 之后"必配的内存优化，本课那张 precision 表可直接当取舍决策卡）
- Qdrant C1《Retrieval Optimization》（scalar/binary 量化的原始出处，本课把它从 dense 搬到多向量；池化是多向量专属的新增维度）
- 已学课程 06《Advanced Retrieval》（质量评估——讲师强调 ground truth 与全局 metric，呼应 reranker 评估方法）
- [[project_selection_matrix]]（检索层的"内存 vs 质量"取舍参数化：量化开关 + 池化策略 + pool_factor）
