# L8 · ADE 的 Parse + Extract 两步法与疑难文档（Lab 4 练习一、二）

> 课程：Document AI: From OCR to Agentic Doc Extraction（DeepLearning.AI × LandingAI）
> 本课任务（Lab 4，Andrea）：用 ADE 的 Python 库跑通 **Parse → Extract 两步法**——先把水电账单解析成带 chunk id / bbox / 每格 grounding 的结构化输出，再用 JSON schema 抽出 10 个可回溯的 KV 字段；然后用**同一个 API** 挑战六份各有难点的文档。

## 0. 建立客户端

```python
from landingai_ade import LandingAIADE
from landingai_ade.types import ParseResponse, ExtractResponse
_ = load_dotenv(override=True)     # 从 .env 读 API key
client = LandingAIADE()            # 一行完成鉴权
```

三个练习各自拆成小步骤；一批 helper 函数（画 bbox、显示文档）只为让 notebook 干净，可自行 inspect。

## 1. 练习一 · Parse：一次调用理解整份文档

对象是一张圣地亚哥的**燃气+电合并账单**（含各自的当月费用 + 用量历史）。解析就是一句话——指定文档路径和模型：

```python
parse_result: ParseResponse = client.parse(
    document=Path("utility_example/utility_bill.pdf"),
    model="dpt-2-latest")          # dpt-2 约月更，结果可能与讲师略异

print(parse_result.metadata.job_id)          # 可回溯的作业 id
print(len(parse_result.splits))              # 页数 = 1
print(len(parse_result.markdown))            # ~6000 字符
print(len(parse_result.chunks))              # 24 个 chunk
```

### 1.1 Parse 输出的结构

`draw_bounding_boxes` 把结果叠回原图：不同 chunk 类型用不同颜色框（logo 浅绿、text 中绿、table、margin 紫、figure 等），**每个 chunk 有唯一 id + type**。关键细节：**table chunk 内部的每个单元格也各有自己的 id**（后面 visual grounding 靠它）。

JSON 顶层元素两块：`chunks` 和 `markdown`。

```python
parse_result.chunks[0].id                  # chunk 唯一 id（chunk 0 = 左上角 logo）
parse_result.chunks[0].type                # 类型
parse_result.chunks[0].grounding.page      # 页码
parse_result.chunks[0].grounding.box       # 坐标

# 结构化到能做简单聚合：数各类型 chunk 数量
counts = {}
for c in parse_result.model_dump()["chunks"]:
    counts[c["type"]] = counts.get(c["type"], 0) + 1
```

`markdown` 有两层：**顶层整篇 markdown**，以及**每个 chunk 各自的 markdown**（`parse_result.chunks[9].markdown`）。第 9 个恰是表格，能直接 `display(HTML(...))` 渲染，且原始 markdown 里能看到每个 table cell 的 id——「这对后面的 visual grounding 很关键，抽到一个值后能指回具体的某个单元格」。

## 2. 练习一 · Extract：Markdown + Schema → 可回溯字段

Extract 步骤 = **parse 出的 markdown + 一个 schema**。为账单定义 10 个属性的 JSON schema（可嵌套、可布尔/字符串/数值）：

```python
schema_dict = {
  "type": "object",
  "properties": {
    "account_summary": {            # 嵌套对象
      "properties": {
        "current_charges": {"type":"number","description":"当期费用"},
        "total_amount_due":{"type":"number","description":"应付总额"}}},
    "gas_summary": {
      "properties": {
        "gas_usage_chart":{"type":"boolean","description":"是否含历史用气图表？"},
        "gas_max_month": {"type":"string","description":"历史用气最高的月份，只返回月名"}}},
    # electric_summary ...
  }}
```

**字段的 description 越丰富，抽取越可能拿到想要的结果**（讲师反复强调）。然后调用：

```python
extraction_result: ExtractResponse = client.extract(
    schema=schema_json,
    markdown=parse_result.markdown,     # 用 parse 出的顶层 markdown
    model="extract-latest")

extraction_result.extraction            # 10 个值：数值/布尔/字符串
extraction_result.extraction_metadata   # 每个值来自哪 —— references 是 chunk id
```

结果亮点：`current_charges = $155.15`（= 应付总额）；布尔告知「有用量图表」；`gas_max_month=January`、电最高在 August——**这是从柱状图里读出来的**（可回原图对峰值验证）。`extraction_metadata` 里的 `0-a`、`0-d` 是 chunk 9 的**表格单元格 id**；较长的 chunk reference 通常来自 figure/文本块（非表格）。

> **架构师视角**：Parse 与 Extract **刻意解耦**是这套 API 最值得抄的设计。Parse 一次、贵一点（跑视觉模型），产出可复用的 markdown+grounding；Extract 便宜、可对同一 parse 结果反复换 schema 跑（L9 就一份 parse 配多套 schema）。这把「理解文档」和「按需求取字段」分成了两个独立可缓存、可迭代的阶段——对应 `3-retrieval.md` 里「摄取/解析是一次性重活，检索/抽取是高频轻活」的分层原则。别把两者揉进一次调用，你会失去缓存与迭代的自由度。

> **对比 3-retrieval.md 的数据摄取解析**：`3-retrieval.md` 把 RAG 上游拆成 load → parse → chunk → embed，其中 parse 质量是「garbage in, garbage out」的总闸门。ADE 的 Parse 正是这一层的托管实现，且多给了两样自建管线难做的东西——**每 chunk / 每单元格的 bbox grounding** 和 **figure 的语义 caption**。也就是说 ADE 不只做「解析成文本」，还把「这段文字在原图哪里」一并结构化，这正是可回溯 RAG（L10）与人审 UI 的地基。

## 3. 练习二 · 同一 API 打六份疑难文档

一个通用函数 `parse_document(path, model, display_option)` 反复调 Parse 并打印输出。六份文档、各有难点，**同一个底层 DPT 全部搞定**：

| 文档 | 难点 | ADE 表现 |
|---|---|---|
| Investor Presentation p7 | 图表+流程图 | 9 chunk，正确识别所有 figure；柱状图读出「平均倍数 4.3x」的水平参考线 |
| HR 流程图 | 箭头四处指、空间关系强 | 整体识别为**一个大 figure**（正确，它是一个视觉单元）；能追出「Good reference? → yes → Select candidate」的逻辑流——传统 OCR 做不到，因为 Select candidate 在页面上其实**高于** Good reference |
| 病毒学 p2 | 无线表格（无行列分隔线 + 大量空白） | 整段识别为 table，空单元格也被理解（规整的 cell 阵列），HTML 渲染出所有空格 |
| 销售量「mega table」 | 上千个单元格 + 行列都有合并单元格 | 全部解析，可存 CSV；讲师点破：**LLM 直接抽这种巨表极易幻觉——上千数字塞不进 context window，这正是 agentic 路线关键价值所在** |
| 病患登记表 | 手写 + 勾选框 + 圈选 | markdown 检出勾选框（「Do you have a Pacemaker?」）、7 处被圈的 No、4 个既往病史圈选（Asthma/circulation/Eye/Urinary）——「配 LLM 就能可靠抽医疗信息」 |
| 微积分手写答卷 | 手写 + 数学公式 | 每题独立 bbox；markdown 渲染函数与根号，末尾正确给出 √(√2/2) |
| IKEA 组装图 | 纯插图无文字 | 用 `dpt-1-latest`（figure 描述更长）；3 个 figure chunk，给出「建议在软垫/地毯上组装以防损伤」的图注 |
| IKEA 信息图 | infographic 混排 | figure/text/logo/table chunk 都稳 |
| 原产地证书 | 印章 + 签名（曲线文字+背景干扰） | 出现 **attestation** chunk 类型（专给印章签名，青绿色框）；签名可读、印章文字可读，两处都还原到 markdown |

```python
parse_document("difficult_examples/hr_process_flowchart.png", display_option="HTML")
parse_document("difficult_examples/ikea-assembly.pdf",
               model="dpt-1-latest",              # 换 DPT-1 拿更长 figure 描述
               display_option="Raw Markdown")
```

核心讯息：**跨文档、跨难点的复杂度，ADE 无需任何额外动作或输入即可处理**——所以能可靠用于会遇到真实世界复杂性与多变性的生产管线。这与 L6 手搓管线「每种文档都要调 prompt/fine-tune」形成直接对照。

## 本课总结

| 要点 | 一句话 |
|---|---|
| 两步法 | Parse（文档→markdown+chunks+grounding）→ Extract（markdown+schema→字段） |
| 一行调用 | `client.parse(document=..., model="dpt-2-latest")` 替代整条 L6 管线 |
| 双层 markdown | 顶层整篇 + 每 chunk 各自；table chunk 连单元格都有 id |
| grounding | 每 chunk / 每单元格带 bbox，抽出值可指回原文精确位置 |
| Extract=md+schema | schema 的 description 越丰富，抽取越准；结果带 extraction_metadata 溯源 |
| 解耦 | Parse 一次可复用，Extract 换 schema 反复跑 |
| mega table | 上千单元格/合并单元格，agentic 路线避开 LLM 幻觉 |
| 同一 API 通吃 | 手写/公式/印章/无线表/纯插图/信息图，零额外配置 |

> **记忆点（引出 L9）**：练习一、二都是「单份文档、已知类型」。L9（Lab 4 续）升级成**真实混合文档管线**——银行贷款场景：一堆命名混乱（uploadA、image456）、类型未知的财务文件。先 `parse(split="page")` 逐页解析，用**首页 markdown + 分类 schema** 判断文档类型，再按类型路由到对应的 **Pydantic schema** 抽字段，最后做跨文档校验（姓名一致?年份一致?资产汇总）。schema 从「抽字段的模板」升格为「路由的分类器」。

## 与我的资产映射

- 检索层：`agent/skills/agent-selection/3-retrieval.md`（摄取/解析 = RAG 上游总闸门；ADE 是托管实现）
- 工具层：`agent/skills/agent-selection/4-tools.md`（Parse/Extract 作为可组合的原子能力）
- 成本经济层：`agent/skills/agent-selection/8-cost-economics.md`（Parse 贵而可缓存、Extract 廉而高频的分层计费直觉）
- 面试包：Field/KV 抽取 + visual grounding，可回溯性是合规行业卖点
- [[project_selection_matrix]]
