# L4 · Lab 2：PaddleOCR 实战 + 布局检测

> 课程：Document AI: From OCR to Agentic Doc Extraction（DeepLearning.AI × LandingAI）· Lesson 2 Lab（讲师 Andrea Kropp）
> 本课任务：亲手跑 PaddleOCR——拿到 bounding box 定位信息、重跑 L2 的收据/表格/手写看提升，再引入 **LayoutDetection** 给页面区域打标签，最后用 report/article/bank_statement 三个新样本**故意暴露弱点**：逐行思维搞不定图表、多栏与表格切分。

## 1. 建 PaddleOCR pipeline

```python
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
from paddleocr import PaddleOCR

ocr = PaddleOCR(lang='en')   # L3 架构图里的 _DET 检测 + _REC 识别两模型都在这
```

**你不用手动顺序调这两个模型**——PaddleOCR 把预处理 + 检测 + 识别当**一条 pipeline** 统一处理。

跑 OCR，结果是「每页一个 dict」的列表（单页图 → 只有一个 dict）：

```python
result = ocr.predict(image_path)
page = result[0]
texts  = page['rec_texts']   # 识别出的文字串
scores = page['rec_scores']  # 每行置信度
boxes  = page['rec_polys']   # bounding box 坐标（4 个角点）

for text, score, box in zip(texts, scores, boxes):
    coords = box.astype(int).tolist()
    print(f"{text:25} | {score:.3f} | {coords}")
```

## 2. 三样新东西：定位、纠偏、读对数字

在 L2 的收据上重跑，PaddleOCR 输出相比 Tesseract 多了关键信息：

```python
img = page['doc_preprocessor_res']['output_img']   # 预处理后的图
# 在处理后的图上叠 bounding box + 识别文字
cv2.polylines(img_plot, [pts], True, (0,255,0), 2)
cv2.putText(img_plot, text, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,0,0), 2)
```

| 收获 | 说明 |
|---|---|
| **纠偏/去背景** | pipeline 自动 deskew/unwarp——对比原图，背景被去掉、轻微顺时针旋转扶正 |
| **Localization（定位）** | bounding box 告诉你每个文字字段**在收据的哪个位置**（Tesseract 没有）|
| **识别更准** | 那个 L2 读错的 `795`，这次**读对了** |

## 3. 封成 agent 工具，重跑三个 L2 样本

工具返回结构升级为「文字 + bbox + 置信度」的字典列表：

```python
@tool
def paddle_ocr_read_document(image_path: str) -> List[Dict[str, Any]]:
    """Reads an image and returns extracted text with bounding boxes."""
    result = ocr.predict(image_path)
    page = result[0]
    texts, boxes = page['rec_texts'], page['dt_polys']
    scores = page.get('rec_scores', [None]*len(texts))
    items = []
    for text, box, score in zip(texts, boxes, scores):
        xs = [p[0] for p in box]; ys = [p[1] for p in box]
        bbox = [min(xs), min(ys), max(xs), max(ys)]     # 4 角点 → [xmin,ymin,xmax,ymax]
        item = {'text': text, 'bbox': bbox}
        if score is not None: item['confidence'] = score
        items.append(item)
    return items
```

agent 搭法与 L2 完全一致（`gpt-5-mini` + `create_tool_calling_agent` + `AgentExecutor`），只换了工具。重跑结果：

| 样本 | PaddleOCR + LLM 结果 |
|---|---|
| **收据** | 输入正确 → 加法正确 → **总额算对**（L2 因 $7.99 算错）|
| **表格** FLOPs | **完全正确**：ByteNet / Deep-Att 正确标为 not found（原表空白）；科学计数被修正 |
| **手写** 填空 | 名字仍误识为 "Myar"；但第 9 题手写 `is` **识别正确**（Tesseract 做不到）；JSON 格式对，且**保留了学生的语法错误答案**（任务明令 "do not correct any grammatical errors"）|

**表格那处的亮点**——LLM 的推理救场：OCR 一度把 `10²⁰` 读成 `1020`，但因为字段是 **FLOPs（浮点运算次数）**，结果是 `10 20` 在物理上讲不通、必须是极大数，agent 用**领域推理**把它纠回 `10²⁰`。这是「OCR 输入 + LLM 认知」互补的正面案例（对照 L2 是互补失败）。

> **对比 L2（Tesseract）**：同样三个样本，换引擎后收据算对、表格全对、手写第 9 题读对——**detection 阶段给了 bbox 帮助理解整体结构，recognition 阶段字符级错误也更少**。这正是 L3 选型表「PaddleOCR 更适合真实世界样本」的实证。但注意手写名字仍崩——OCR 换代不是万能药。

## 4. 故意暴露弱点：逐行思维的三道坎

用 `run_ocr()`（把上面打印+叠框逻辑封成一个函数）跑三个新样本：

### 4.1 report.png（美国经济报告内页）——图表丢失

顶部表格、中部文字、底部**带标注的折线图**。PaddleOCR：表格和文字尚可，但折线图**整体没有框**（未被当作单一单元），只有零散的 X/Y 轴标签（`0, -2, -4, -6`）被框住，且**完全脱离上下文**——散落在其他内容之间，无从得知它们本是 Y 轴标签、更不知它们属于一张被彻底忽略的图表。→ **弱点 1：图表被无视。**

### 4.2 article.jpg（关于牙齿的学术文章）——多栏读乱

顶部 abstract 与 callout 两栏、正文三栏、中间插一张表。PaddleOCR 的**阅读顺序横着走**：本该沿左栏向下读，它却跨栏平读——"in most of the westernized countries **that** system based on..."（`that` 后本应接 `undertake`，却跳到别栏的 `system`），整篇被搅成乱码。→ **弱点 2：多栏布局被打乱（garble）。**

结论：**layout-aware text detection 是准确 OCR 的基石**，而 PaddleOCR 的 detection「没有视觉（vision）」，复杂文档需要某种 vision 模型。

## 5. 引入 LayoutDetection：给区域打标签

好消息：PaddleOCR 自带 Layout Detection（此前没用）。它给区域返回 **label + score + bbox**：

```python
from paddleocr import LayoutDetection
layout_engine = LayoutDetection()

def process_document(image_path):
    layout_result = layout_engine.predict(image_path)
    regions = []
    for box in layout_result[0]['boxes']:
        regions.append({
            'label': box['label'],        # text / chart / paragraph_title / number / footer ...
            'score': box['score'],
            'bbox':  box['coordinate'],    # [x1,y1,x2,y2]
        })
    return sorted(regions, key=lambda x: x['score'], reverse=True)
```

效果：

| 样本 | LayoutDetection 结果 |
|---|---|
| report.png | 正确识出 text / paragraph_title / table / **chart（整张图一个框）** / number / footer——图表这次被当作整体 |
| article.jpg | 识出 doc_title / abstract / text / paragraph_title / footnote / footer / table（高置信）；正文被整块框住 → **不再把 `that` 接到别栏的 `system`**，跨栏乱读被治好 |
| bank_statement.png | 把全部识别成**一张大表**，但按人眼该在 headers（Date/Description/Category/Amount/Balance）处断成两张表；底部小字被**完全忽略**（可能藏法律脚注）→ 仍有弱点 |

## 6. Lab 2 收尾

| 要点 | 一句话 |
|---|---|
| PaddleOCR 强于传统 | 真实世界图像上碾压 Tesseract（收据/表格/手写均改善）|
| 但仍逐行思考 | 本质仍以「一行行文字」为单位，不懂区域 |
| bounding box | detection 给出定位，助力整体理解 |
| LayoutDetection | 补上 region-level 结构（段落/表/图在哪），但**仍非完整语义理解** |
| 仍有缺口 | 表格切分、图表内部、多页结构、小字——不符合「人如何看文档」|
| 方向 | 人类靠视觉系统看文档 → 后续引入更多 vision（VLM）|

> **记忆点（引出 L5）**：本 lab 露出两层缺口——PaddleOCR 逐行思维搞乱多栏、无视图表；LayoutDetection 补了「区域在哪、是什么」却仍非语义理解，也没解决**阅读顺序**（bank statement 表切分、小字丢失）。L5（Lesson 3「Layout detection & reading order」，讲师换回 David）正面攻这两点：用学习模型 **LayoutReader**（基于 LayoutLM、在 50 万页 ReadingBank 上训练）预测阅读顺序，再引入 **VLM** 补上「看图理解」，最终把 layout（确定性 grounding）+ VLM（视觉推理）组合成**混合架构**，由 agent 编排——这正是 L6 lab 要搭的东西。

## 与我的资产映射

- **检索层上游**：bounding box 定位 + region 标签 = RAG 里做「结构化切块（layout-aware chunking）」的原料——`agent/skills/agent-selection/3-retrieval.md` 的分块质量直接受益于此，比纯文本切块更能保住表格/图表边界。
- **同族课程**：`Preprocessing Unstructured Data for LLM Applications`（layout-aware 分块）；`19-Event-Driven Agentic Document Workflows with LlamaIndex`（同为复杂文档区域化处理）。
- 选型沉淀：「OCR → +LayoutDetection → +VLM」的能力阶梯与各自缺口 → [[project_selection_matrix]]。
