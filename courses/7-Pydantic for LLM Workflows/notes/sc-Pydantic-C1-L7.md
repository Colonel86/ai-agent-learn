# 第 7 课（彩蛋）：动手项目 + Jupyter AI 辅助编码

> 课程：Pydantic for LLM Workflows · Lesson 7（Bonus）
> 原文件：
> - `subtitles/sc-Pydantic-C1-L7.vtt`
> - `code/project.ipynb`（项目工作区 Notebook）

---

## 一、这节课是什么？

> ⚠️ **课程结束后新录的 Bonus Lesson**（讲师自嘲："I'm suddenly in a slightly different background and I got a haircut."）
>
> 核心是一个**可选的项目工作区（Project Workspace）**——让你用所学知识**真正动手做点东西**。

### 🎯 本课目标

- 熟悉项目环境（Jupyter Lab + Jupyter AI）
- 学会用 AI 辅助编码完成 LLM 响应验证工作流
- 也可以**完全抛开模板，做你自己的创意项目**

---

## 二、🧰 项目环境介绍

### 2.1 整体布局

```
┌──────────────────────────────────────────────────────────┐
│  Jupyter Lab                                             │
├──────────────┬───────────────────────────┬───────────────┤
│ 📂 文件面板  │  📓 project.ipynb          │ 💬 Jupyter AI │
│              │  （主工作区）              │    Chat       │
│ - docs.md    │                            │               │
│ - project.ipynb                           │  Jupyternaut  │
│              │                            │  (AI 助手)    │
└──────────────┴───────────────────────────┴───────────────┘
```

### 2.2 什么是 Jupyter AI？

> **Jupyter 官方团队出品的 AI 辅助编码框架**，让你在 Jupyter Lab 里直接使用 AI 助手写代码。

**类似工具**：
- Cursor
- Windsurf
- Antigravity
- Copilot

区别：**Jupyter AI 原生集成在 Jupyter 生态里**。

### 2.3 Jupyternaut：Jupyter AI 的"助手角色"

类似 Cursor 的 Chat Panel、VSCode 的 Copilot Chat——**在聊天里问问题、生成代码、解释代码**。

---

## 三、🎯 Jupyter AI 的核心操作

### 3.1 打开 Chat

1. 点击侧栏的 **chat icon（💬）**
2. 点击 **+ Chat** 新建会话
3. 开始和 Jupyternaut 对话

### 3.2 把生成的代码插入 Notebook

当 Jupyternaut 给出代码后：

| 按钮 | 作用 |
|------|------|
| **Insert below active cell** | 在当前 cell 下方插入新 cell |
| **Replace selection** | 替换当前选中的 cell |

### 3.3 🔑 用 `📎 paperclip` 图标**附加上下文**

这是让 AI 生成高质量代码的**核心技巧**——把**相关文件作为上下文**喂给它：

```
用户：帮我写一个电影推荐生成器，遵循 Pydantic 模型规范

📎 附加文件：
  ✅ docs.md（课程知识总结文档）
  ✅ project.ipynb（当前 Notebook）
```

**效果**：Jupyternaut 能**完全理解**课程中的 Pydantic 用法 + 项目当前状态，生成的代码和项目风格高度一致。

---

## 四、📄 核心文件 `docs.md`

### 🎯 这是整个项目最值钱的文件

> `docs.md` 是一份**简明的课程知识浓缩**——涵盖了从 Pydantic 基础模型到工具调用的所有关键点。

**它的两个作用**：

| 用途 | 说明 |
|------|------|
| **📖 课程复习笔记** | 课后可以带走继续看 |
| **🤖 AI 的"领域知识背景"** | 附给 Jupyternaut，让它"懂 Pydantic" |

---

## 五、📓 `project.ipynb` 项目结构

### 5.1 项目流程

```
Step 1: 定义 Pydantic 响应模型
         ↓
Step 2: 编写 prompt 让 LLM 返回符合 schema 的 JSON
         ↓
Step 3: 调 LLM
         ↓
Step 4: 用 Pydantic 验证响应
         ↓
（可选）Step 5: 失败则重试或错误处理
```

### 5.2 预置的 Prompt 模板

Notebook 里提供了现成的 **Movie Recommendation Generator** prompt 示例，核心结构：

```
You are a coding assistant.

I want to create a <具体的业务场景> that uses a Pydantic model
with the following requirements:

<详细描述你要的模型字段和约束>

Please use the course documentation (docs.md) and current notebook
state as context for generating code consistent with what I've learned.
```

> 🎯 **你可以**：
> - 原样使用（Movie Recommendation）
> - 改需求（做你自己的场景）
> - 完全重写（自由创作）

---

## 六、🚀 完整工作流示例

### 6.1 讲师演示的流程

```
① 打开 Chat（侧栏 → chat icon → + Chat）
   ↓
② 复制 Notebook 里的 prompt 模板
   ↓
③ 粘贴到 Chat 里
   ↓
④ 用 📎 附加 docs.md + project.ipynb
   ↓
⑤ 发送
   ↓
⑥ Jupyternaut 生成代码
   ↓
⑦ 在 Notebook 里选中目标 cell
   ↓
⑧ 点击 "Replace selection"
   ↓
⑨ 运行 cell，完成 Step 1
```

### 6.2 后续步骤

- Notebook 里还有 Step 2 ~ Step N，都是类似流程
- 讲师故意**不剧透完整项目**——希望你自己探索

---

## 七、💡 本课核心收获

### 7.1 一种全新的"课程后学习方式"

> 传统课程：看视频 → 做配套题 → 结束
>
> **有了 AI 助手**：课程文档本身可以变成**AI 的"讲义"**，让 AI 帮你 customize 到任何场景。

### 7.2 Prompt 中"附加上下文"的价值

- **只问问题** → AI 给通用答案
- **问题 + 附 docs.md** → AI 给**符合课程风格**的答案
- **问题 + 附 docs.md + 附 notebook** → AI 给**符合你当前项目状态**的答案

### 7.3 这是"AI-Native 学习"的示范

> **课程 + AI 助手 + 你自己的项目 = 个性化学习闭环**

---

## 八、🎯 动手建议

### 8.1 最保守：照着做

- 用默认的 Movie Recommendation Generator prompt
- 完整走完 Step 1 ~ Step N
- 熟悉 Jupyter AI 的用法

### 8.2 进阶：改需求

把 Movie Recommendation 换成**你自己感兴趣的场景**：

| 场景 | 模型示例 |
|------|----------|
| **菜谱推荐** | `RecipeRecommendation`（ingredients, steps, difficulty） |
| **书单生成** | `BookList`（titles, genres, reading_order） |
| **简历筛选** | `ResumeScreening`（match_score, concerns, recommendations） |
| **Bug 报告分析** | `BugReport`（severity, category, suggested_fix） |

### 8.3 自由发挥：完全自创

- 设计一个**你工作中真实需要**的 Pydantic 工作流
- 作为课程学习的**毕业作品**
- 真的能用的话，就部署到生产

---

## 九、📝 Jupyter AI 速查

| 操作 | 路径 |
|------|------|
| 打开 Chat | 侧栏 `💬` → `+ Chat` |
| 附加文件 | Chat 输入框 `📎` |
| 插入代码 | Chat 输出下方 `Insert below active cell` |
| 替换代码 | 选中 cell → Chat 输出下方 `Replace selection` |
| 关闭侧栏 | 点击 `×` 收起 lesson sidebar 或文件面板 |

---

## 🎓 🏁 完整课程收官

至此，Pydantic for LLM Workflows 全部 7 节课的学习文档全部整理完成：

| Lesson | 主题 |
|--------|------|
| L0 | 课程介绍 |
| L1 | 路线图：朴素 vs Pydantic 专业 |
| L2 | Pydantic 基础 |
| L3 | Prompt + Validate + Retry（手搓） |
| L4 | 把模型直接传给 API |
| L5 | Tool Calling 完整流水线 |
| L6 | 结语 |
| **L7** | **🎁 Bonus：项目实操 + Jupyter AI** |

🚀 **Now go build something!**
