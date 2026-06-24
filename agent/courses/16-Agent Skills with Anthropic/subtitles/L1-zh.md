# L1 在 Claude AI 中创建你的第一个 Skill

> **核心定义**：Skill 是一个**指令文件夹**，用于打包重复工作流、专业知识或新能力。如果你发现自己在多个对话中反复输入同样的提示词，就该把它转成 Skill。

本节通过一个营销活动分析的真实场景，演示从"反复粘贴提示词"到"打包成可复用 Skill"的完整迁移过程。

## 场景：每周营销活动分析

假设你每周都要做一份营销活动复盘，手头有一份 CSV：包含日期、活动名称、曝光（impressions）、点击、转化等指标。

### 没有 Skill 时的做法

每次新对话，都要把同一套指令复制粘贴一遍：

1. **第一轮提示**：上传 CSV，说明输入数据结构，要求做数据质量检查（Data Quality Check）、漏斗分析（Funnel Analysis）、给出基准指标（点击率、转化率），并指定输出格式
2. **第二轮提示**：要求计算 ROAS（广告投入回报）、CPA（获客成本）、净利润等效率指标，再指定一种输出格式
3. **第三轮提示**：上传"预算再分配规则"文档，要求按规则给出加预算 / 维持 / 减预算建议

问题：

- 每次都得把整套上下文重粘一遍
- 所有信息一次性塞进上下文，**即便很多场景下根本用不到**（例如不涉及预算再分配时）
- 难以分享给团队成员、难以维护迭代

## 解决方案：打包成 Skill

把这套工作流封装为一个文件夹（Skill），就能做到：

- 自己复用，无需重复粘贴
- 团队成员可共享
- 按需加载，节省上下文

## SKILL.md 文件

Skill 的核心是一个名为 `SKILL.md` 的 markdown 文件。它包含两部分：

### 1. YAML Frontmatter（必填）

```yaml
---
name: analyzing-marketing-campaign
description: 用于每周营销活动数据的复盘分析……
---
```

- **name**：Skill 的唯一标识，agent 触发它的依据，也会出现在 UI 中
- **description**：让模型判断"该不该用这个 Skill"的关键依据

> 每个 Skill **都必须**有 name 和 description。

### 2. 主体内容

与之前粘贴的提示词高度相似，但更结构化：

- 输入要求（Input Requirements）
- 数据质量检查
- 漏斗分析与历史基准
- 效率分析
- 输出格式
- **预算再分配说明**：在主文件中只放一句"用户问到预算再分配时，再读 `references/budget_reallocation_rules.md`"

这就是渐进式披露的体现——只有用户提到预算再分配时，那份长文档才会被读入上下文。

## Skill 文件夹结构

```
analyzing-marketing-campaign/
├── SKILL.md
└── references/
    └── budget_reallocation_rules.md
```

### 命名规则

- **小写字母**
- **单词间用短横线**（dash）
- **不要使用保留关键字**，如 `claude`、`anthropic`

### references 文件夹

`references/` 是 Skill 标准中**约定的子目录名**，用来存放 Skill 引用的外部文档。在 `SKILL.md` 里引用时直接写 `references/budget_reallocation_rules.md`。

## 上传到 Claude AI

1. 把整个 Skill 文件夹**打包成 zip**
2. 进入 Claude AI 的 **Settings → Capabilities → Skills**
3. 点击 Add，拖入 zip 文件
4. 上传完成后能看到 Skill 名称和描述

## 实战效果

新开一个对话，附上同样的 CSV，简短提一句"分析这周的营销数据"——Claude 会：

1. 读取 `SKILL.md` 确认遵循正确指令
2. **只在涉及预算再分配时**，才去读 `references/budget_reallocation_rules.md`
3. 执行数据分析（你可以展开查看底层运行的代码）
4. 给出漏斗分析、效率分析、再分配建议

无需任何提示词来回粘贴。

## 组合：与内置 Skill 协作生成 Excel 报告

接着让 Claude 把分析结果生成一份 Excel 报告（带颜色编码）。这里用到了**Claude 内置的 Excel Skill**——创建电子表格、执行必要代码的能力本身就是一个 Skill。

你能在过程中看到：

- 自定义 Skill 分析数据
- 内置 Excel Skill 执行代码生成 `.xlsx`
- 包含 Executive Summary、Funnel Analysis、Efficiency Analysis 等 sheet
- 可在 Google Drive 中打开，也可下载

## 关键收获

- **集中化**：把数据和指令打包到一个可复用的文件夹
- **上下文高效**：渐进式披露，只加载必要内容
- **可移植**：Skills 是开放标准，可在 Codex、Gemini CLI 等其他环境中通用
- **可组合**：自定义 Skill + 内置 Skill 一起用，从 CSV 直达多格式可执行成果

下一节我们将更深入地理解 Skill 的结构、工作原理，以及它在整个 AI 生态中的定位。
