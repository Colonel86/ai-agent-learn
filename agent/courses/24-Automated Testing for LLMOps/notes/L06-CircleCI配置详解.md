# L06 CircleCI 配置详解（可选）（Exploring the CircleCI Config File）

> 原始代码：`code/L5_exploring-circleci-config-file.md`
> 本节为可选 lab，无对应视频字幕——内容来自课程提供的 step-by-step 教程。

---

## 一、配置即代码（Configuration as Code）

CircleCI 的流水线行为全部存在一个 YAML 文件里：项目 Git 仓库的 **`.circleci/config.yml`**。

每个 config 文件有三个核心组件：**jobs、commands、workflows**。

---

## 二、三大核心组件

### 1. Jobs（作业）
CI/CD 流水线里**自动化的基本单元**，每个 job 代表一个高层任务，包含要执行的命令。

- 每个 job 在自己的配置段里定义，并指定执行环境（如 Docker 镜像）。
- CircleCI 执行 job 时，在其基础设施上创建一个云执行环境，跑指定的镜像。
- 例：`run-hello-world` job 用 `cimg/python` 镜像，打印 "Hello World!"。

### 2. Commands（命令）
job 内**按顺序执行的单个步骤**。两种定义方式：
- **内联**：用 `run` 关键字直接写（`name` 决定 dashboard 里的显示名，`command` 决定实际执行的命令行）。
- **具名复用**：在 job 外定义、命名，多个 job 共用 —— 体现 DRY 原则。

常用内置/orb 命令：
- `checkout`：内置命令，检出含 config 文件的仓库代码
- `python/install-packages`：来自 Python orb，安装 `requirements.txt` 里的依赖
- 典型流程：`checkout` → 装依赖 → 用 PyTest 跑 `test_assistant.py`

### 3. Workflows（工作流）
用来**编排多个 job**。

- 可定义多个 workflow，在 push 到特定分支时触发，或按计划触发。
- workflow 把输出 log 到 CircleCI dashboard，**某个 job 失败时停止**，便于检查输出。
- 一个 workflow 里可放任意数量的 job；默认**并行**运行，也可配成串行或带条件。

---

## 三、进阶特性

### 条件工作流（Conditional Workflows）
用 if-statement 逻辑在不同条件下跑不同 workflow。

典型用法：
- push 到 **dev 分支** → 跑 pre-commit evals
- push 到 **main 分支** → 跑 pre-release evals

实现方式：通过 CircleCI API 传入 **pipeline parameters**（如 `eval-mode`），或基于 **pipeline values**（如 `pipeline.git.branch`）。

### 计划工作流（Scheduled Workflows）
前面的 workflow 都由 commit 触发（典型 CI）。但更全面的 evals 可能想按固定计划跑（持续交付/部署）——用标准 **cron 语法**设置，例如每晚触发。

---

## 四、其他用到的特性

| 特性 | 作用 |
|---|---|
| **Execution environments** | Docker 镜像、Linux/macOS/Windows VM、GPU executor、自托管 runner；同一 workflow 的不同 job 可跑在**不同机器**上（如 GPU 训模型、自有基础设施部署） |
| **Orbs** | 可共享的 CircleCI 配置包，类似软件库；有官方认证、社区、私有三类 |
| **Contexts** | 安全集中存储凭据（secrets），**不要把密钥写进 config 文件**（会随代码进仓库被暴露）；课程用的是 `dl-ai-courses` context |

---

## 五、本节要点速记

- CircleCI 是「配置即代码」，全部行为定义在 `.circleci/config.yml`。
- 三大组件：**job**（任务单元）、**command**（job 内的步骤，可内联或具名复用）、**workflow**（编排多个 job，失败即停）。
- 条件工作流按分支/参数跑不同评估（dev→per-commit，main→pre-release）；计划工作流用 cron 定时跑全面评估。
- 凭据用 **Contexts** 管理，绝不写进 config 文件。
- 这套 job/command/workflow 模型不止用于 LLM 测试，是构建任何 CI/CD 流水线的通用基础。
