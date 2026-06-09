# L3 基础：工具使用 chatbot（Chatbot Example）

本讲是动手前的"地基课"——还没引入 MCP，先用**普通的 Anthropic tool use** 搭一个能搜 arXiv 论文的 chatbot。后面所有 MCP 改造都基于这套代码。

> 对应代码：`code/L3.ipynb`

## 整体结构

```
用户输入
  ↓
Claude（带 tools 列表）
  ↓ 决定调工具
本地 Python 函数（search_papers / extract_info）
  ↓ 返回结果
Claude 综合结果给最终答复
```

## 两个工具函数

### `search_papers(topic, max_results=5)`

- 用 `arxiv` SDK 按主题搜论文。
- 抽取每篇论文的：title、authors、summary、pdf_url、published。
- 把结果写到 `papers/<topic>/papers_info.json`（按主题分目录）。
- 返回所有 paper ID 列表。

```python
PAPER_DIR = "papers"

def search_papers(topic: str, max_results: int = 5) -> List[str]:
    client = arxiv.Client()
    search = arxiv.Search(
        query=topic,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    papers = client.results(search)

    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    file_path = os.path.join(path, "papers_info.json")
    # ... 合并已有 JSON，写回
    return paper_ids
```

### `extract_info(paper_id)`

- 遍历 `papers/` 下所有主题目录，找到含该 ID 的 JSON 条目。
- 返回 JSON 字符串；找不到则返回提示。

## Tool Schema（给 Claude 看的描述）

```python
tools = [
    {
        "name": "search_papers",
        "description": "Search for papers on arXiv based on a topic and store their information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "The topic to search for"},
                "max_results": {"type": "integer", "default": 5}
            },
            "required": ["topic"]
        }
    },
    {
        "name": "extract_info",
        ...
    }
]
```

> 重点：**模型只是"请求调用"**，真正执行函数还是开发者的 Python 代码做。

## Tool Mapping（把名字派发到真实函数）

```python
mapping_tool_function = {
    "search_papers": search_papers,
    "extract_info": extract_info,
}

def execute_tool(tool_name, tool_args):
    result = mapping_tool_function[tool_name](**tool_args)
    # 统一序列化为字符串
    if isinstance(result, list):
        result = ', '.join(result)
    elif isinstance(result, dict):
        result = json.dumps(result, indent=2)
    return str(result) if not isinstance(result, str) else result
```

## chat 主循环：`process_query`

核心逻辑：

1. 发起第一次 `client.messages.create(...)`，带上 `tools=tools`。
2. 遍历 response.content：
   - **text** → 直接打印。
   - **tool_use** → 提取 `tool_id` / `tool_name` / `tool_args`，本地 `execute_tool` 执行，把结果作为 `tool_result` 追加到 messages，再次调用模型继续生成。
3. 当模型只返回纯 text，循环结束。

注意：模型用的是 `claude-sonnet-4-6`（原视频是已弃用的 `claude-3-7-sonnet`）。

## chat_loop 与无记忆

```python
def chat_loop():
    while True:
        query = input("Query: ").strip()
        if query.lower() == 'quit':
            break
        process_query(query)
```

⚠️ **每次 query 都是新的 messages 列表，会话间不持久化记忆**。所以让它"提取论文 X 的信息"时，要把 ID 显式带在 prompt 里。

## 试运行

例子查询：

- `Search for 2 papers on "LLM interpretability"` → 触发 `search_papers`，写到本地 JSON。
- `extract info on the first two and summarize` → 模型自己把上一步的 ID 当作参数调 `extract_info`。

## 与下一讲的衔接

本讲展示的所有"工具定义 + schema + 执行"逻辑，**全部都会被搬到 MCP server 里**。chatbot 之后只通过 MCP client 拿 schema、转发调用——这就是 MCP 重构的核心。
