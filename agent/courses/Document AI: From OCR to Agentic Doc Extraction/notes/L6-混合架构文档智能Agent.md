# L6 · 混合架构的文档智能 Agent（PaddleOCR + LayoutReader + LangChain + VLM 工具）

> 课程：Document AI: From OCR to Agentic Doc Extraction（DeepLearning.AI × LandingAI）
> 本课任务（Lab 3）：把前几课讲的「版面检测 + 阅读顺序 + VLM」拼成一条**三段式管线**，用 LangChain Agent 编排两个 VLM 专用工具，做到「看结构 → 按需深入」地回答文档问题。

## 0. 从 L5 接上：为什么要「混合」

L5（David 的理论课）铺垫了本课的全部动机：文档不是自上而下、从左到右的纯文本流。传统「OCR → 展平文本 → 喂 LLM」是**破坏性抽取**——列、行被搅在一起，表格变成漂浮文本团，图注与图分离，阅读顺序不可预测。L5 给出的解法链条是：

1. **Layout Detection（版面分析）**：识别段落/表格/图/页眉页脚等区域，先懂结构再抽内容；
2. **Reading Order（阅读顺序）**：规则法（top-to-bottom + X-Y cut）在多栏/侧栏/浮动元素上立刻崩溃，改用学习模型 **LayoutReader**（LayoutLM 为 encoder 的 seq2seq，训练集 ReadingBank 50 万页）；
3. **VLM**：本质仍是 LLM，只是前面加了 Vision Encoder（CLIP/SigLIP）+ Projector，能「看」图但缺确定性 grounding，单独喂整页会幻觉、定位差；
4. **Hybrid**：Layout 提供确定性 grounding，VLM 负责需视觉推理的区域，用 **agentic 框架**编排。

本课就是把第 4 步落地成代码。

## 1. 三段式管线总览

```
输入文档(经济报告 report_original.png)
        │
 ┌──────┴───────┐
 │ ① 文本抽取    │  PaddleOCR 出文本+置信度+bbox
 │   + 阅读顺序  │  LayoutReader(LayoutLMv3) 重排序
 ├──────────────┤
 │ ② 版面检测    │  PaddleOCR LayoutDetection → text/table/chart/title 区域
 ├──────────────┤
 │ ③ Agent 编排  │  LangChain create_tool_calling_agent
 │              │  工具: AnalyzeChart / AnalyzeTable (VLM=gpt-4o-mini)
 └──────┬───────┘
        ▼
   连贯的回答（文本问题走 OCR 上下文，图表问题调 VLM 工具）
```

类比一个人类分析师读复杂报告：先扫全局结构，再对特定小节深挖。

## 2. 阶段一：文本抽取 + 阅读顺序

先用 PaddleOCR 出三样东西——识别文本、置信度、bbox：

```python
ocr = PaddleOCR(lang='en')
page = ocr.predict(image_path)[0]
texts  = page['rec_texts']    # 识别出的文本串
scores = page['rec_scores']   # 置信度
boxes  = page['rec_polys']    # bbox（四点多边形）
```

用 `@dataclass` 把裸列表包成结构化的 `OCRRegion`，并给一个把四点多边形转成 `[x1,y1,x2,y2]` 的便捷属性——这个结构会贯穿整条管线：

```python
@dataclass
class OCRRegion:
    text: str
    bbox: list          # [[x1,y1],...,[x4,y4]]
    confidence: float
    @property
    def bbox_xyxy(self):          # 四点 → 两点，后续全用这个
        xs = [p[0] for p in self.bbox]; ys = [p[1] for p in self.bbox]
        return [min(xs), min(ys), max(xs), max(ys)]
```

接着加载 HuggingFace 上的 `hantian/layoutreader`（LayoutLMv3 做 token 分类），核心函数 `get_reading_order` 五步走：

```python
layout_model = LayoutLMv3ForTokenClassification.from_pretrained("hantian/layoutreader")

def get_reading_order(ocr_regions):
    # 1. 从所有 bbox 估计画布尺寸，加 10% padding
    # 2. 把 bbox 归一化到 0-1000（LayoutLM 的坐标约定）
    boxes = [[int(x1/W*1000), int(y1/H*1000),
              int(x2/W*1000), int(y2/H*1000)] for ...]
    # 3. 转成 transformer 输入
    inputs = prepare_inputs(boxes2inputs(boxes), layout_model)
    # 4. 推理
    logits = layout_model(**inputs).logits.cpu().squeeze(0)
    # 5. 从 logits 解析出每个区域的阅读位置
    return parse_logits(logits, len(boxes))
```

可视化把红色序号叠在每个区域上：标题在前、正文随后，大体符合人类阅读流。**但并不完美，会有跳序**——讲师明说这就是该路线的局限，复杂文档可能要自己 fine-tune 版面模型，而「难开发、难扩展、难维护」。最后把 OCR 文本按阅读位置排序，产出 `[{position, text, confidence, bbox}]`，作为 Agent 上下文的一部分——**基础文本问题不必调 VLM 就能答**。

> **架构师视角**：这一段暴露了「专用模型拼装」路线的税负。每一环（PaddleOCR、LayoutReader、后面的 VLM）都是独立训练、独立调优、独立监控的组件，任何一环退化都会向下游传染，而阅读顺序的跳序错误会直接污染喂给 Agent 的上下文。这正是 `5-observability-eval.md` 里「管线越长、可观测点越多、根因定位越难」的典型样本——记住这个痛点，L7 的单一 API 就是冲它来的。

## 3. 阶段二：版面检测

PaddleOCR 另有一个独立的 `LayoutDetection` 类，专做结构识别，与 OCR 分开：

```python
layout_engine = LayoutDetection()

def process_document(image_path):
    res = layout_engine.predict(image_path)[0]
    regions = [{'label': b['label'], 'score': b['score'], 'bbox': b['coordinate']}
               for b in res['boxes']]
    return sorted(regions, key=lambda x: x['score'], reverse=True)
```

每个区域带 `label`（text / table / chart / figure / paragraph_title …）、`score`、`bbox`。再包成 `LayoutRegion` dataclass，**关键是给每个区域一个 `region_id`**——工具要靠它引用具体区域。可视化用不同颜色框 + `id: type (conf)` 标注。

## 4. 区域裁剪 + base64：为 VLM 工具备料

Agent 要分析某个图表/表格时，只把**裁剪后的区域**发给 VLM，而非整页。三大好处：

| 好处 | 说明 |
|---|---|
| 聚焦分析 | VLM 只看相关内容 |
| 降噪 | 周围文字不干扰 |
| 降本 | 图更小 → API 更便宜 |

```python
def crop_region(image, bbox, padding=10):   # 带 padding 裁剪
    x1,y1,x2,y2 = bbox
    return image.crop((max(0,x1-padding), max(0,y1-padding),
                       min(image.width,x2+padding), min(image.height,y2+padding)))

region_images = {}          # region_id -> {image, base64, type, bbox}
for r in layout_regions:
    crop = crop_region(pil_image, r.bbox)
    region_images[r.region_id] = {'image': crop,
                                  'base64': image_to_base64(crop),   # 视觉 API 要 base64
                                  'type': r.region_type, 'bbox': r.bbox}
```

讲师提醒：即便如此，**VLM 的 localization 仍不强**，此法能提精度但要为各种 edge case 反复调 prompt。

## 5. 两个专用工具：AnalyzeChart / AnalyzeTable

VLM 用 `gpt-4o-mini`（成本考量）。每个工具的 prompt 三段式：**角色 + 抽取字段清单 + JSON 输出模板**——用模板逼 VLM 出结构化、可靠消费的输出。

```python
vlm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

CHART_ANALYSIS_PROMPT = """You are a Chart Analysis specialist.
Extract: chart_type / title / axes / key_data_points / trends / legend
Return JSON: {{ "chart_type":"...", "x_axis":{{...}}, "trends":"..." }}"""

def call_vlm_with_image(image_base64, prompt):
    msg = HumanMessage(content=[
        {"type":"text","text":prompt},
        {"type":"image_url","image_url":{"url":f"data:image/png;base64,{image_base64}"}}])
    return vlm.invoke([msg]).content

@tool
def AnalyzeChart(region_id: int) -> str:
    """图表区域分析：抽取图型/坐标轴/数据点/趋势，返回 JSON。"""
    if region_id not in region_images:
        return f"Error: Region {region_id} not found."
    data = region_images[region_id]           # 取裁剪好的 base64
    return call_vlm_with_image(data['base64'], CHART_ANALYSIS_PROMPT)
```

`AnalyzeTable` 同构，换成表格 prompt（列头/行标签/合并单元格/空单元格标 null，输出 `{table_title, column_headers, rows, notes}`）。`@tool` 装饰器把普通函数变成 Agent 可用工具。单测两个工具：图表工具**数据点接近但非 100% 准**（缺视觉推理与定位），表格工具在简单表上尚可，但复杂度上升会更难定位、易幻觉。

> **对比 Preprocessing Unstructured Data for LLM Applications**：那门课用 `unstructured` 库把文档 `partition` 成 NarrativeText / Title / Table / Image 等元素并给类型标签——和这里的 LayoutDetection 是同一层工作（元素分类 + 结构化），区别在于**处理策略**：`unstructured` 走「规则/模型分类 → 元素归一化」，本课走「分类 → 按类型路由到不同工具（文本走 OCR 上下文、图表走 VLM）」。后者把「按元素类型分派处理」显式做成了 Agent 的工具选择，代价是要自己维护路由逻辑与 prompt。

## 6. 组装 Agent

Agent 的 system prompt 就是它的「文档记忆」，由 helper 把数据结构拼成可读字符串：**角色定义 + 阅读顺序文本 + 版面区域清单(带 id/type) + 工具说明(何时用) + 指令(不同内容类型怎么处理)**。

```python
SYSTEM_PROMPT = f"""You are a Document Intelligence Agent.
## Document Text (in reading order)
{ordered_text_str}
## Document Layout Regions
{layout_regions_str}
## Your Tools
- AnalyzeChart(region_id): chart/figure 区域取数据点/坐标轴/趋势
- AnalyzeTable(region_id): table 区域取结构化数据
## Instructions
1. TEXT 区域 → 直接用上面 OCR 文本
2. TABLE 区域 → 调 AnalyzeTable
3. CHART/FIGURE 区域 → 调 AnalyzeChart
"""

tools = [AnalyzeChart, AnalyzeTable]
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT), ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")])
agent = create_tool_calling_agent(ChatOpenAI(model="gpt-4o-mini", temperature=0), tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)  # verbose 看推理过程
```

Agent 工作流：收到问题 → 读 system prompt（含全部 OCR 文本+版面）→ 判断能否仅凭文本回答，否则选工具 → 对图表/表格调对应工具 → 汇总成连贯回答。

**三个测试**印证分派逻辑：
- 「文档里有哪些内容类型？」→ 纯文本可答，**不调工具**；
- 「抽取表格数据」→ 定位 table 区域，调 `AnalyzeTable`；
- 「分析图表趋势」→ 调 `AnalyzeChart`（这些是 OCR 文本拿不到的视觉信息）。

## 7. 局限与收尾

管线能深理解复杂报告（表格/图/多栏/图注/叙事流），但讲师直白点出**规模化痛点**：文档越多样越易变，这类多 agent 管线开始崩——难维护、edge case 脆、难扩展，因为每个组件都要手动调优/监控/编排。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 三段式管线 | 文本抽取+阅读顺序 → 版面检测 → Agent 编排 |
| LayoutReader | LayoutLMv3 从 bbox 学阅读顺序，坐标归一化到 0-1000，会跳序 |
| region_id | 版面区域的唯一 id，是工具引用具体区域的钥匙 |
| 裁剪+base64 | 只把区域喂 VLM，聚焦/降噪/降本 |
| 工具 prompt 三段式 | 角色 + 抽取字段 + JSON 模板，逼结构化输出 |
| Agent 分派 | 文本走上下文、图表表格走 VLM 工具 |
| 核心局限 | 多组件手工编排，脆、难维护、难扩展 |

> **记忆点（引出 L7）**：本课手搓的「PaddleOCR + LayoutReader + LayoutDetection + 2 个 VLM 工具 + LangChain 编排」这一大坨，每一环都要自己训练/配置/调 prompt/监控。L7 会揭示 LandingAI 的 **Agentic Document Extraction（ADE）**——把版面分析、文本抽取、区域分割、阅读顺序重建、多模态推理、schema 抽取全部收进**单一 API**，本课的整条管线塌缩成一次 `client.parse()`。

## 与我的资产映射

- 观测·eval 层：`agent/skills/agent-selection/5-observability-eval.md`（长管线的可观测/根因定位税）
- 工具层：`agent/skills/agent-selection/4-tools.md`（VLM 工具化 + `@tool` 分派模式）
- 设计模式：`agent/skills/agent-selection/11-design-patterns.md`（router/分派：按内容类型选工具）
- 对比课程：`agent/courses/Preprocessing Unstructured Data for LLM Applications`（元素分类的另一路线）
- [[project_selection_matrix]]
