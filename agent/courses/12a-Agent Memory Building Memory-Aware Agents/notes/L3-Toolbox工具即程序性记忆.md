# L3 · Toolbox 模式：工具即可检索的程序性记忆

## 1. 核心洞察：工具是一种记忆

传统做法把所有工具定义**一股脑塞进上下文**。本课的反直觉主张：**工具是程序性记忆（procedural memory），应该像知识一样被语义检索出来，而不是全量塞进 context**。

存工具时，把 **工具名 + 描述 + 参数** 嵌入成向量，存进 `TOOLBOX_MEMORY`；用的时候拿当前 query 做相似度检索，**只取 top-k 个相关工具**给 LLM。

## 2. 为什么"工具太多"是个真问题

| 危害 | 说明 |
|---|---|
| **上下文混淆/膨胀** | 几十个工具定义占满窗口，挤掉真正的信息 |
| **工具选择能力退化** | 选项越多，LLM 选错概率越高 |
| **延迟与 token 成本** | 每次调用都带全量工具定义，线性烧钱 |

> **架构师视角**：这是 MCP 时代非常现实的痛点。当你接了一堆 MCP server、暴露上百个工具，全量塞进去必然翻车。Toolbox 模式给了标准解法——**工具检索层（tool retrieval）**：把工具当可检索资产，按需注入。这是 [[project_selection_matrix]] 工具层应该补进去的一个模式，也是我面试包里"工具治理"话题的实证案例。当有人问"MCP 工具太多怎么办"，答案就是这套语义检索 + 动态注入。

## 3. Toolbox 的注册与检索

用装饰器注册工具，`augment=True` 开启文档增强：

```python
@toolbox.register_tool(augment=True)
def search_tavily(query: str, max_results: int = 5):
    """Use this function to search the web and store the results in the knowledge base."""
    ...

@toolbox.register_tool(augment=False)   # 已有详尽 docstring，无需增强
def arxiv_search_candidates(query: str, k: int = 5) -> str:
    """Search arXiv and return a JSON list of candidate papers with IDs + metadata..."""
    ...
```

检索侧就是一个"工具即工具"的自举设计——连**检索工具本身**都是注册进 toolbox 的一个工具：

```python
@toolbox.register_tool(augment=True)
def read_toolbox(query: str, k: int = 3) -> list[str]:
    """Search the toolbox for functions that can help solve a problem...
    Use this tool when: 遇到错误需要换方法 / 现有工具不够用 / 想发现有哪些能力可用..."""
    return memory_manager.read_toolbox(query, k=k)
```

> **记忆点**：`read_toolbox` 是"能找工具的工具"——这让智能体在 agent loop 里遇到瓶颈时，能**自己去检索还有什么工具可用**，而不是被启动时给定的固定工具集锁死。这是"自更新智能体"的一块拼图。

## 4. Memory Unit Augmentation（记忆单元增强）

这是本课一个精巧的点：**开发者写的 docstring 往往只有一行、语义可分性（separability）差**，导致工具检索不准。解法是**让 LLM 读取「原始 docstring + 函数源码」，生成一份增强版描述**再去嵌入。

```python
fn = toolbox._tools_by_name["search_tavily"]
source = inspect.getsource(fn)                       # 连源码一起喂给 LLM
augmented = toolbox._augment_docstring(original, source)
# LLM 产出更丰富、更可区分的描述 → 嵌入质量更高 → 检索更准
```

> **架构师视角**：这是"用 LLM 优化 LLM 系统的输入"的典型套路——**离线预处理阶段花一次 LLM 成本，换在线检索的长期准确率**。同样的思路可迁移到：知识库 chunk 的自动摘要、实体的规范化描述。值得抽象成一条通用模式记进 [[project_asset_reuse]]：「用 LLM 增强被检索对象的可分性」。成本-收益是一次性 vs 持续，通常划算。

## 5. 本课注册的实用工具

| 工具 | 作用 | augment |
|---|---|---|
| `search_tavily` | Web 搜索并写回知识库 | True |
| `arxiv_search_candidates` | 搜 arXiv 返回候选论文 JSON | False |
| `get_current_time` | 返回当前时间 | True |
| `read_toolbox` | 语义检索其它工具 | True |

配套用了 `ArxivRetriever`（`load_max_docs=8`, `doc_content_chars_max=4000`）和文本切分。注意 `search_tavily` 不只是搜——它**顺手把结果写回知识库**（带 metadata：title/url/score/source_type/timestamp），实现"搜索即积累语义记忆"。

> **架构师视角**：`search_tavily` 这个"检索 + 写回"的设计体现了 Agent Memory 相对 RAG 的增量——**工具执行的副产物自动沉淀为长期记忆**。下次问相似问题，可能直接命中知识库，不必再搜。这就是 L1 说的"从经验中学习"的微观实现。
