# L6 用 Claude API 调用 Skills —— Code Execution 与 Files API

L1 中我们看到 Claude AI 里用 Skill。本节切换到 **Claude Messages API**，用 L5 的两个自定义 Skill 程序化运行。

## 两个关键前置

### 1. Skill 不跨产品共享

> Claude AI / Claude Desktop 里创建的 Skill **不会**同步到 Claude API 或 Claude Code。它们是独立的 Skill 库。

### 2. Skill 运行需要执行环境

Skills 需要：

- 执行代码
- 创建/编辑文档、演示稿、PDF、报告
- 访问文件系统

Claude AI / Claude Desktop **自带容器化环境**（在 Settings → Capabilities 中可以看到 "Code execution and file creation" 开关，默认开启）。Skills 依赖它，关掉则 Skill 无法使用。

但用 **API 时，你必须手动启用**这套能力。

## API 上的两个核心工具

### Code Execution Tool

让 Claude 在**沙箱化的容器**里跑 bash / shell：

- 创建、查看、编辑文件
- 写代码并执行
- 独立隔离的环境

限制（Messages API 下）：

- RAM、磁盘、CPU 限额
- **无互联网连接**（这是 API 独有，Claude AI / Claude Desktop 下可以联网装包）
- 预装的库有限

容器同时提供文件系统，可以挂目录。

### Files API

用于上传/下载文件，配合 Code Execution Tool 使用。比如：

- 用户上传输入文件
- 容器读取并处理
- 生成产物再下载

Skill 也是放在容器中的某个目录下，被 Code Execution Tool 读取。

> **API 使用 Skill 时，必须同时启用 Code Execution Tool。**

## 实战 1：generating-practice-questions Skill

在 Jupyter Notebook 中：

### 上传 Skill

```python
# 上传 Skill 目录，配合 beta headers
# 返回 skill_id
```

需要的 beta headers：

- skills 相关
- code execution
- files API

### 查看自己的 Skill 列表

```python
client.beta.skills.list(source="custom")
```

加 `source="custom"` 避免拉所有内置 Skill。

### 上传输入文件（LaTeX 讲义）

用 Files API 上传 `.tex` 文件，得到 file 对象。

### 发起请求

```python
client.beta.messages.create(
    model="claude-sonnet-...",
    # betas: skills + code execution + files
    container={"skills": [{"skill_id": ..., "version": "latest"}]},
    tools=[{"type": "code_execution_..."}],
    messages=[{"role": "user", "content": "用我上传的 LaTeX 讲义生成练习题"}]
)
```

### 响应过程（按时间顺序）

1. 模型说"我可以基于讲义生成题目，先读 Skill 文件 + 讲义"
2. **检测到 Skill**，只读 `SKILL.md`（先不读 assets/references）
3. 阅读输入 LaTeX
4. 因要 Markdown 输出 → **渐进式披露**：读 `assets/markdown_template.md`
5. 用 Code Execution Tool 生成 Markdown 文件
6. 拷贝到 output 目录，通过 Files API 得到 `file_id`
7. 程序化下载到本地

下载得到的 `notes04.md` 严格符合 Skill 定义的顺序：True/False → 解释题 → 编程题 → 实战应用。

### 删除 Skill

要先**列出所有版本**并逐个删除，最后才能删除 Skill 本身。

## 实战 2：analyzing-time-series + 内置 docx Skill 组合

### 上传自定义 Skill + 上传 CSV 输入

```python
# 上传 analyzing-time-series Skill → skill_id
# 用 Files API 上传零售销售 CSV
```

调用 `client.beta.skills.list()` 不加 source 时，能看到内置 Skill（Excel、PowerPoint、Word、PDF 等）。

### 同时使用自定义 Skill 与内置 docx Skill

```python
container={
    "skills": [
        {"skill_id": ..., "version": ...},   # 自定义
        {"type": "anthropic", "name": "docx"} # 内置
    ]
}
```

### 执行流程

1. 读 `SKILL.md`（自定义） + `SKILL.md`（docx）
2. 看 CSV 前 20 行了解 schema
3. 按 Skill 指示运行 `diagnose.py` + 可视化脚本
4. 读取 `summary.txt`（脚本产物）
5. **渐进式披露**：从 docx Skill 只读取生成 Word 文档所需的部分
6. 把 markdown 内容生成 `.docx`
7. 通过 Files API 得到 `file_id` 并下载

最终 Word 文档包含：发现、概览、统计、图表、统计分析——全部由两个 Skill 组合产出。

## 关键收获

- **API 必须显式开启** code execution + files API + skills beta
- **Skill 库分两类**：自定义（你上传的）、内置（Anthropic 提供）；可以组合使用
- 同样的 **渐进式披露**机制依然生效
- 删除 Skill 需先删所有版本
- 通过这套 API，你可以**全自动、可编程**地跑 Skill 流水线

下一节切到 **Claude Code**，看怎么把 Skill 放在 `.claude/skills/` 下，并在命令行应用里使用。
