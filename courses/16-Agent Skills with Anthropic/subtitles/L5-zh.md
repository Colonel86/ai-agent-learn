# L5 Skill 结构与最佳实践

本节聚焦：

- Skill 的结构规范
- 编写 Skill 的最佳实践
- 用 skill-creator 对两个自定义 Skill（生成练习题、时序数据分析）做"代码评审"
- 怎么为 Skill 写单元测试

## 复习：每个 Skill 必备的结构

```
your-skill/
├── SKILL.md          # 必填，含 YAML frontmatter
├── references/       # 可选
├── scripts/          # 可选
└── assets/           # 可选
```

`SKILL.md` 必含 YAML frontmatter，至少有 `name` 和 `description`。

## name 与 description 的最佳实践

> 这是 mission critical 的两个字段——既让 Claude 理解 Skill 干什么，也让它知道**何时该用**。

### name

- 有字符上限
- 只能用**小写字母、数字、短横线**
- 推荐 "动词 + ing" 的形式（如 `analyzing-...`、`generating-...`）

### description

- 既说**做什么**，也说**什么时候用**
- 想让 agent 触发，**显式写出关键词**

### 可选字段

规范还支持可选字段：

- license
- compatibility
- 任意自定义 key-value metadata

> 注意：规范仍在演进中，你会遇到**不完全遵循规范**的 Skill（包括 Anthropic 自家的）。这是正常的。

## 主体内容（body）最佳实践

frontmatter 之后没有强制格式，但建议：

- **分步骤、清晰、有顺序**
- **明确标注边界情况（edge cases）**
- 若某步可跳过，**写清楚为什么可跳过**
- **不要超过 500 行**——长内容拆到外部文件，按需引用
- 跨平台兼容：**路径一律用正斜杠 `/`**，即便在 Windows 也是

### 自由度（Degree of Freedom）的取舍

- **低自由度**：要求严格遵循最佳实践
- **高自由度**：创作型场景，多颜色、多风格、多字体

### 不要一个 Skill 吃下所有事

复杂工作流应**拆成多个 Skill**串联，而不是写一个超大 Skill。系统可以承载 100+ Skill，关键是**命名清晰、不混淆、流程可预测**。

## 可选目录约定

- **`scripts/`**：需要读取与执行的代码；要有错误处理和清晰文档
- **`references/`**：额外的文档/参考文件；如果某个 reference 很长，**指示 Skill 读取全文**
- **`assets/`**：输出模板、图片、Logo、数据文件、schema 等

> 这些目录名是 Skills 规范的约定，但目前生态里仍有许多 Skill 用了其他名称。规范快速演进，建议新建 Skill 跟随规范。

## 两个 Skill 实例剖析

### Skill 1：generating-practice-questions

**描述**：基于讲义生成教学练习题。

主体结构：

1. **支持的输入格式**（用哪些库提取）
2. **问题结构**：明确的顺序（True/False → 解释题 → 编程题 → 实战应用）
3. 每类问题的子准则
4. **输出格式**：依赖用户请求；不在 `SKILL.md` 里塞所有模板，而是**引用 `assets/markdown_template.md`、`assets/latex_template.md`**
5. 领域示例放在 `references/`

> 始终保持 < 500 行；任何长内容都用 reference 文件承接，配合渐进式披露，**只在用到对应格式时**才被加载。

### Skill 2：analyzing-time-series

**描述**：分析 CSV 时序数据特征，准备预测。

特点：**强确定性工作流，依赖三个 Python 脚本**。

`scripts/` 下：

- 可视化脚本：时序图、直方图、滑动统计、箱线图……
- 自相关 / 分解（autocorrelation / decomposition）绘图
- `diagnose.py`：数据质量、分布、平稳性、季节性、趋势、自相关、变换建议

`SKILL.md` 主体：

- **输入格式**：列名、类型严格定义
- **工作流**：显式指定脚本运行的精确顺序（先 diagnose、再视情况生成图、再呈现）
- 可选 flags
- 输出目录树（文本文件、图像各自归位）
- 外部 references
- **依赖说明**：列出 Python 库，确保脚本能跑

## 用 skill-creator 评估自己的 Skill

可以在 Claude Desktop 做，本节示范在 **Claude Code** 中做。

### 在 Claude Code 安装 skill-creator

Claude Code 不内置 skill-creator，要从 marketplace 安装：

1. 进入 **Marketplaces**，add `anthropic/skills`
2. 这个仓库有两个集合：
   - **document-skills**（Excel/PowerPoint/Word/PDF）
   - **example-skills**（含 skill-creator）
3. **project 作用域**安装
4. 重启 Claude Code
5. 项目的 `.claude/settings.json` 会包含 `enabledPlugins`
6. 用 `/skills` 命令确认 skill-creator 出现

### 并行 sub-agent 评估

让 Claude Code 用两个**并行 sub-agent**分别评估两个自定义 Skill。结果示例：

- generating-practice-questions：**9/10**，简洁度可改进，给出改进建议
- analyzing-time-series：**满分**，去重、frontmatter 质量、简洁度都不错

> 把 skill-creator 当"自动评审员"是一种很好的初步评估手段。

## 给 Skill 写单元测试

最佳实践类比软件单测：搭建测试桩（harness）。

### 给 generating-practice-questions 写测试

测试用例覆盖：

- 生成并保存到 Markdown / LaTeX / PDF
- 输入文件格式正确
- 期望行为：用对了 PDF 解析库、抽取了学习目标、生成各类题型且符合准则
- 输出结构和模板正确（参照 `assets/`）
- LaTeX 能成功编译
- 输出文件路径与格式正确
- **加入人工反馈**
- **跨模型测试**

### 给 analyzing-time-series 写测试

假设三个 Python 脚本已用传统单测覆盖。skill 层级再测：

- 传入 CSV → 视化脚本 / diagnose 按正确顺序运行
- 若请求绘图，**可选步骤**被包含
- 返回 summary、解读结论
- **输出目录结构**与文件位置严格符合 Skill 规范
- 跨模型测试、加入人工反馈

下一节，我们把这两个 Skill 拿到 Jupyter Notebook，通过 **Claude Messages API + Code Execution Tool** 程序化运行。
