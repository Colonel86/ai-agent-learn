# L4 · PDF 与图片的视觉预处理（Document Image Analysis：DLD vs Vision Transformer）

> 课程：Preprocessing Unstructured Data for LLM Applications（DeepLearning.AI × Unstructured）
> 本课任务：当文档**自身不带结构信息**（PDF、扫描图片）时，如何用"看图"的模型抽出格式与文本，产出与 HTML/Word 一致的规范化 document elements。

## 0. 承上：从"读标签"到"看图"

L3（metadata & chunking）之前处理的都是**自带结构**的文档——HTML 有 `<title>`/`<table>` 标签、Word 有样式，规则解析器（rules-based parser）就能直接读出 element 类型。但一大类文档没有这种内建结构：

- **PDF**：有些是"文本型"（文字可直接抽），有些是"扫描型"（整页就是一张图）；
- **图片**：截图、扫描件，只有像素，没有任何标签。

对这类文档，只能靠**视觉信息**理解版面结构。本课就是这条"看图"支线，学两种 document image analysis 方法：**Document Layout Detection（DLD，文档版面检测）** 与 **Vision Transformer（视觉 Transformer）**。

路线：① 为什么要看图 → ② 两法总览 → ③ DLD 两步法 → ④ Vision Transformer → ⑤ 取舍 → ⑥ 同一文档 HTML vs PDF 实操对照。

## 1. 两种方法总览

| 维度 | Document Layout Detection | Vision Transformer |
|---|---|---|
| 范式 | 目标检测（object detection） | 图像→文本的 seq2seq |
| 步骤 | **两步**：画框标注 → 抽框内文本 | **一步**：图进，文本出 |
| 输出 | bounding box + 类别 + 文本 | 直接生成结构化文本（如 JSON） |
| 代表模型 | **YOLOX** | **Donut**（Document Understanding Transformer） |
| 是否需 OCR | 视文档而定（扫描件要，文本型 PDF 不要） | 不需要（模型内部一步搞定） |
| 能否加 prompt | 否 | 可，像 LLM 一样接文本 prompt |

一句话区分：**DLD 先框后取，Vision Transformer 端到端直出。**

## 2. Document Layout Detection：画框 + 取字，两步走

DLD 用一个目标检测模型在文档上**画 bounding box 并打标签**（narrative text / title / bulleted list / table …），然后把框内文字取出来。取字有两条路：

```
第一步：目标检测模型 → 在页面上画框 + 标类别
第二步：把每个框里的文字取出——
   ├─ 扫描件/图片：框内没有可读文本 → 跑 OCR（光学字符识别）
   └─ 文本型 PDF：文字本就在文档里 → 用框坐标回溯原文档，直接抠出文本（无需 OCR）
```

常用模型是 **YOLOX**（archive 有论文）。"回溯原文取字"是 DLD 的一个隐藏优势——文本型 PDF 里文字是精确的，比 OCR 更准且省一次模型调用。

> **架构师视角**：DLD 输出的 **bounding box 坐标是可追溯性（provenance）的载体**。RAG 回答要标注"这句话来自原文第几页哪个位置"时，坐标就是锚点；纯生成式抽取丢了坐标，就只能靠文本匹配去猜来源。对合规/审计场景，"能指回原文哪一块"往往是硬需求，这会直接决定选 DLD 而非 Vision Transformer。

## 3. Vision Transformer：一步端到端，直出结构化文本

Vision Transformer 把整张文档图片当输入，**一步**产出文本；OCR 不再是独立环节，模型内部就把"识字"做了。代表架构 **Donut（Document Understanding Transformer）** 可被训练成直接吐出**合法 JSON 字符串**，每个元素带 `text` 和 `category`：

```
文档图片 → Vision Transformer → 合法 JSON 字符串
  → 解析成规范化 document elements（与其它文档类型对齐）
```

关键特性：可选地接一个**文本 prompt**（就像 LLM），因此对**非标准文档（表单等）更灵活**——抽 key-value pair 很容易，加一种新 element 类型甚至只要改 prompt，不用重训模型。代价是它是**生成式**的：会幻觉/重复，且算力开销远大于 DLD。

> **对比 Document AI 文档抽取**：Google Document AI / Azure Form Recognizer 这类"文档抽取"托管服务，本质就是把 DLD + OCR（甚至 Vision Transformer）打包成 API——你上传 PDF，它回结构化字段。本课把这层拆开讲清楚：**托管服务省心但受限于它预置的 schema 与 element 类型**；自己走 Vision Transformer + prompt 路线，能适配任意本体（ontology），但要自担幻觉与算力。选型分野 = "标准发票/表单，量大" 走托管抽取；"schema 多变、需自定义 element" 才值得上可 prompt 的 Vision Transformer。

## 4. 两法取舍：优缺点对照

| | 优点 | 缺点 |
|---|---|---|
| **DLD**（YOLOX） | ① 固定 element 集合，识别可以做到很准；② 有 bounding box，可回溯原文、文本型 PDF 免 OCR | ① 有时需两次模型调用（检测 + OCR）；② 不灵活，只认预置的固定类型 |
| **Vision Transformer**（Donut） | ① 对表单等非标准文档灵活，易抽 key-value；② 可 prompt，易适配新本体；③ 单次模型调用 | ① 生成式，易幻觉/重复；② 算力贵，要么烧显卡要么跑得慢 |

## 5. 代码实操：同一篇新闻，HTML vs PDF 三种走法

示例文档是一篇 CNN 关于 El Niño 天气的新闻，**同时有 PDF 和 HTML 两个版本**。目标：验证"无论哪种表示，抽出的 element 集合几乎一致"。因为 PDF 是 model-based 工作负载，`hi_res` 走 Unstructured **API**（省去本地装模型）。

**① HTML —— 规则解析（本地开源库）**：

```python
from unstructured.partition.html import partition_html

html_elements = partition_html(filename="example_files/el_nino.html")
for el in html_elements[:10]:
    print(f"{el.category.upper()}: {el.text}")   # 直接靠 HTML 标签识别 Title / NarrativeText
```

**② PDF —— fast 策略（直接抽文本，不上模型）**：

```python
from unstructured.partition.pdf import partition_pdf

# fast：从文本型 PDF 里直接抽字，适合本例这种简单 PDF（无需视觉模型）
pdf_elements = partition_pdf(filename="example_files/el_nino.pdf", strategy="fast")
```

**③ PDF —— hi_res + YOLOX（DLD，走 API）**：

```python
from unstructured_client.models import shared

with open("example_files/el_nino.pdf", "rb") as f:
    files = shared.Files(content=f.read(), file_name="el_nino.pdf")

req = shared.PartitionParameters(
    files=files,
    strategy="hi_res",          # 高精度：走视觉模型
    hi_res_model_name="yolox",  # 指定 DLD 模型
)
resp = s.general.partition(req)              # model-based，可能要几分钟
dld_elements = dict_to_elements(resp.elements)
```

**对照结果**（用 `collections.Counter` 按类别计数）：

| 表示 / 策略 | 总 element 数 | 明细 |
|---|---|---|
| HTML（rules） | 35 | 23 NarrativeText + 10 Title + … |
| PDF + YOLOX（DLD） | 39 | 28 NarrativeText + 10 各类 Title（含 Header/Title）+ … |

结论：**不完全相同，但非常接近**。同一篇内容，走规则（HTML）还是走视觉（PDF/YOLOX），下游应用都能当成同一份规范化 element 集合处理——这正是 Unstructured "统一 element 抽象"的价值：**把异构输入收敛成同一种数据结构，上层逻辑不必关心它原来是什么格式**。

> **架构师视角**：`strategy="fast"` vs `"hi_res"` 是一个典型的**成本/精度旋钮**。简单文本型 PDF 用 fast（无模型、秒级、免费），复杂/扫描件才升到 hi_res（模型、分钟级、贵）。生产管线里最省钱的做法是**按文档难度分流**：先 fast 试，检测到疑似扫描/复杂版面再回退到 hi_res——而不是无脑全量上视觉模型。

## 6. 本课总结

| 要点 | 一句话 |
|---|---|
| 何时看图 | 文档自身无结构（PDF、图片）时，靠视觉信息还原版面 |
| DLD | 目标检测画框 + 取字（OCR 或回溯原文），有坐标可追溯，YOLOX |
| Vision Transformer | 图→文本一步直出，可 prompt、灵活，但生成式易幻觉且贵，Donut |
| 策略旋钮 | fast（抽文本）↔ hi_res（视觉模型），按难度分流控成本 |
| 统一抽象 | HTML/fast/DLD 三路产出几乎一致的 element，上层无差别处理 |

> **记忆点（引出 L5）**：本课把整页版面拆成了 Title / NarrativeText 等 element，但**表格**被当成一个整体框——框里的行列结构还没还原。L5 专攻表格：如何在 PDF/图片里检测出表，并推断其行列结构、导出 `text_as_html`，让 LLM 读懂表内数据。

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（RAG 数据摄取——文本型 vs 扫描型 PDF 的分流策略、fast/hi_res 成本旋钮）
- 工具/服务选型：DLD 自建 vs Document AI 托管抽取的取舍，可沉淀进"文档解析"选型条目
- [[project_selection_matrix]]
