# L4 内置 Skills、skill-creator 与端到端工作流

L1 中我们看到 Claude 用 Excel Skill 生成报表。Excel 只是 Anthropic 预置 Skill 之一，还有 PowerPoint、Word、PDF，以及一个"创建 Skill 的 Skill" —— **skill-creator**。

本节先逛一圈这些预置 Skill，重点剖析 skill-creator；然后把"自定义 Skill + 内置 Skill + MCP" 串成一个端到端工作流。

## Anthropic 官方 Skill 仓库

仓库地址：`github.com/anthropic/skills`

里面分两类：

- **document-skills**：PowerPoint、Excel、Word、PDF —— **始终内置**于 Claude AI / Claude Desktop
- **example-skills**：可选 Skill，默认关闭（**例外**：skill-creator 默认开启）

## 案例 1：PowerPoint Skill

打开 PowerPoint Skill 文件夹，结构与之前一致：

- `SKILL.md`（YAML frontmatter + 主体内容）
- 其他参考文件与脚本

`SKILL.md` 主要内容：

- 用户可能要求"创建、编辑、分析 PowerPoint"
- 阅读与解析的方式
- 必要时执行的脚本（按需加载，不会一上来全部加载）
- 设计原则、要求、配色 palette（用户未指定时由 Claude 挑选）

虽然这份 `SKILL.md` 很长，但运行时只在真正需要的环节调用底层脚本，从而产出像样的演示稿。

## 案例 2：skill-creator —— 创建 Skill 的 Skill

这是一个"元 Skill"：用它**自动生成新 Skill 的目录结构与 `SKILL.md`**。

### 内部结构

`SKILL.md` 里包含：

- name + description
- Skill 的整体说明
- **最佳实践清单**（next lesson 会详细讲）
- 明确的创建步骤（步骤越显式越好）
- 先看具体示例 → 规划复用内容 → 初始化骨架

### scripts/ 下有三个 Python 脚本

- `init_skill.py`：根据模板填充 frontmatter 和占位符，生成基础骨架
- `package_skill.py`：把 Skill 打成 zip
- `validate_skill.py`：校验 `SKILL.md` 是否存在、YAML 是否合法、文件结构是否正确

### 在 Claude AI 中的位置

进入 **Settings → Capabilities → Skills**，能看到示例 Skill 列表。默认 skill-creator 是**唯一开启**的。

> 即使有了 skill-creator，**你给的提示词与上下文质量仍是关键**，它不会替你设计 Skill。

## 端到端实战：MCP + 自定义 Skill + 内置 Skill

目标：

1. 把 L1 的"营销分析"Skill 升级，从读 CSV 改为查 **BigQuery**
2. 新建一个"品牌规范" Skill（颜色、字体、Logo）
3. 组合上述两个自定义 Skill + 内置 PowerPoint Skill，生成符合品牌的演示稿

### 准备 BigQuery 的 MCP Server

用 Claude Desktop 时，在 **Settings → Developer** 中查看/配置本地 MCP Server：

- 启动命令、参数、环境变量、凭据路径
- 配置文件指定启动时连接哪些 server

> 你不一定要用 BigQuery，任意外部数据源都可以。本例只是演示 Skills + MCP 协作。

### Step 1：升级"营销分析"Skill 改用 BigQuery

先用 MCP 工具验证：

- 问："列出 BigQuery 中的表" → 成功返回 `marketing` 数据集与一张表
- 问："给我看这张表的 schema" → 返回字段结构

然后让 Claude **用 skill-creator 改写**现有的 `analyzing-marketing-campaign` Skill：

- 数据源由 CSV 改成 BigQuery 表
- 把 schema 写进 Skill
- **保留**原本对 `budget_reallocation_rules` 的引用
- 遵循最佳实践（例如：避免使用模糊日期范围，或全量范围；要求用户澄清日期；示例 SQL 显式带日期范围）

Skill 生成后，再让 Claude **保存为后续对话可用的 Skill**。

### Step 2：新建"品牌规范"Skill

新对话中：

1. 上传品牌规范文档（color palette、辅助色、字体）和 Logo
2. 让 Claude 用 skill-creator 生成 Skill
3. skill-creator 会读取现有 Skill 的模式，确保新 Skill 与它们协作良好
4. 运行 `init_skill.py` 生成骨架
5. 把 logos、规范文件归入 `assets/` 子目录
6. 生成 `SKILL.md`，里面带颜色、字体、文档/演示稿布局规则

完成后**保存**该 Skill。

### Step 3：组合生成品牌化 PowerPoint

在新对话中：

> "用本周 BigQuery 数据做营销分析，按品牌规范生成一份 PowerPoint。"

执行链路：

1. 读取自定义"营销分析"Skill 与"品牌规范"Skill
2. 准备好 PowerPoint Skill 与品牌样式
3. 用 BigQuery MCP 执行 SQL 拉取数据
4. 根据品牌 Skill 写出 HTML/CSS 风格的幻灯片
5. 调用内置 PowerPoint Skill 生成 `.pptx`
6. 出错时模型会**回溯修正**，保证最终产出合规

最终产物：

- Executive Summary、Funnel Analysis、Efficiency Analysis 三类 sheet
- 带品牌色、字体、Logo
- 可在 Google Drive 打开或下载

## 关键收获

- **document-skills** 始终内置；example-skills 默认关闭，skill-creator 默认开启
- **skill-creator** = 程序化生成 Skill + 内置最佳实践
- 真实工作流通常是：**MCP 拉数据 → 自定义 Skill 编排 → 内置 Skill 落地输出**
- 模型可以基于 Skill 自我校验、回溯，产出更可靠

下一节我们会聊 Skill 的最佳实践，并把两个 Skill 喂给 skill-creator 自评。
