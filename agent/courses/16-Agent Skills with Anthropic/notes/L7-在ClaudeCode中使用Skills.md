# L7 在 Claude Code 中使用 Skills —— 代码、测试、审阅 + 子 Agent

切到 Claude Code。本节把 Skill 用于**代码生成、代码审阅、测试**，并配合**子 agent**搭建一套高效工作流。

## 示例项目

一个用 Python 写的命令行任务管理应用：

- **CLI 框架**：Typer
- 数据模型：dataclasses
- 终端美化：Rich
- 持久化：JSON 文件
- 依赖管理：uv

架构：

```
src/task/
├── __init__.py        # 注册所有 commands
├── commands/
│   ├── add.py
│   ├── done.py
│   └── list.py
├── models.py          # Task / Priority dataclass
├── storage.py         # 序列化/反序列化
├── display.py         # 终端展示
└── tests/
```

### CLAUDE.md

> `CLAUDE.md`（项目根）用 `/init` 或手写。**始终在上下文中**，描述代码栈、约定、架构，Claude 每次对话都能参考。

CLAUDE.md 里写清楚：用 Typer、dataclasses、Rich、JSON 持久化、uv 管理依赖、命令文件结构等。

## 项目目标：新增 `edit` 命令

按现有代码风格添加 `edit` 命令——但要**遵守工作流**：放对位置、注册正确、用 Annotated 类型、用 `display.success/info` 显示信息、destructive 命令要确认等等。

为此准备两个**项目级 Skill**和一套子 agent。

## Skill 1：adding-cli-command

项目级 Skill 放在：

```
.claude/skills/adding-cli-command/SKILL.md
```

> Skill 也可放在用户 home 目录（user 作用域）。本例用 project 作用域。

主体内容包括：

- **识别工作流**：在 `commands/` 下创建文件，在 `__init__.py` 注册
- **命令样式约定**：使用 `Annotated` 类型注解参数（Typer 的多种写法中**选最现代的**）
- **不要直接 print**：调用 `display` 对象的方法（success / info）
- **flag 约定**：长短名、help text
- **类型注解、默认值、返回值**写法
- **subcommand 与组管理**：版本/迁移类的展示
- **destructive 命令**（如 hard delete）：先确认再执行
- 注册单命令 vs 命令组的方式
- 通用约定：docstring 要求、exit codes、constants

> 不必把"所有通用约定"都塞进 CLAUDE.md。**子集化的约定就放到对应 Skill 里**，按需加载。
> 这个 Skill 命名通用（CLI app 而不是 task）—— **跨项目可复用**。

## Skill 2：generating-cli-tests

```
.claude/skills/generating-cli-tests/SKILL.md
```

为 Typer 命令生成 pytest 测试。

要点：

- **触发条件**显式（"当用户要求 write tests / 加测试覆盖时使用"）
- **fixture 优先**：临时存储、sample data、mocking
- **AAA 结构**：Arrange / Act / Assert
- 按命令类型（read/add/...）列出例子
- **覆盖 edge cases**：非法输入、状态、确认、未找到
- 包含 checklist
- 运行命令：怎么跑 verbose、跑单文件

## Skill 3：reviewing-cli-command

封装一份"完成功能后的自检"清单：

- 文件位置、装饰器、注册是否正确
- 是否用了 Annotated 等约定
- 给**正反例**（用 Annotated vs 不用）
- 错误处理与输出
- 输出格式：含 summary + suggested fixes

> **不是教 Claude 怎么写代码，而是验收 Claude 写的代码**。相当于在另一个 Skill 上加了一层评估。

## 在 Claude Code 中加载 Skill

- 用 `/skills` 列出 project + user Skill
- **新建 Skill 后要关掉 Claude Code 再开**才能识别
- `/skills` 也会显示**name + description 占用的 token 数**

## 实战 1：让 Skill 帮你写 edit 命令

提示词："新增 edit 命令，可编辑 title 与 priority，传入 id 校验。"

Claude Code 会：

1. 提示使用 `adding-cli-command` Skill
2. 读取既有 commands 风格做模式匹配
3. 创建 `edit.py`，在 `__init__.py` 注册
4. 你试跑命令、加任务、edit、查看效果

如果想跑全套 edge case 测试，会消耗大量 token 与时间。**改用子 agent**。

## 引入子 Agent

两个子 agent：

- **code-reviewer**：评审代码（主 agent 专注开发）
- **test-generator-runner**：生成并执行测试

> **子 agent 不会继承父 agent 的 Skill。必须显式声明**。

> **传递方式**：在子 agent 的配置里写 skills 字段（或者从 Skill 本身指定 agent 名）。

### 创建 code-reviewer

用 `/agents` 命令创建（manual configuration）：

- name：`code-reviewer`
- description：说明何时调用
- 选择**最小必要工具**：Bash、Glob、Grep、Read（不需要 Write/Edit）
- model：继承父级
- color：purple
- 保存后在 `.claude/agents/` 出现 `code-reviewer.md`
- **手动加上 `skills:` 字段**，值 `reviewing-cli-command`

### 子 Agent 中的 Skill 行为差异

> 子 agent 一旦被派发，对应 Skill 的**整份 `SKILL.md` 会被预加载**进上下文——不像主 agent 那样仅加载 name + description。**后续的渐进式披露（读其他文件、跑命令）正常进行**。

### 创建 test-generator-runner

- 工具：Bash、Glob、Grep、Read、**Write、Edit**（要写测试文件）
- model：继承父级
- color：yellow
- skills：`generating-cli-tests`

## 整合工作流

### 场景 A：edit 命令的完整闭环

1. 用 `code-reviewer` 子 agent 评审 `edit.py`：列出 warnings 与建议修复
2. 用 `test-generator-runner` 子 agent 为 `edit.py` 生成 pytest 测试
3. 运行 `uv run` + verbose 跑所有测试，确认绿色

### 场景 B：修一份不合规的 `clear.py`

假设另一位团队成员加了 `clear.py`，没遵循规范。

1. **code-reviewer** 找出 6 个严重问题 + 4 个 warning（误用方法、flag 格式不对、exit code 错等）
2. 主 agent 读取问题并**逐条修复**：用 `display`、改 flag、修 exit code、在 `__init__.py` 注册
3. **test-generator-runner** 生成 clear 命令的测试
4. 跑测试，全部通过

> 主 agent **不存储**评审/测试的细节上下文，只接收子 agent 的产出，把上下文窗口用在主线开发上。

## 关键收获

- 项目级 Skill 放在 `.claude/skills/`
- 不同 Skill 各管一事，**比一个大 Skill 更可控**
- 子 agent **必须显式配置 Skill**
- 子 agent 调用时**整份 `SKILL.md` 被预加载**
- 子 agent + Skill 是**上下文高效**的关键模式

下一节切到 **Claude Agent SDK**，自己用相同的 harness 搭一个研究 agent。
