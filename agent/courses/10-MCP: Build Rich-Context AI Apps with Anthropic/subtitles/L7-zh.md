本节为研究服务端添加**资源（Resources）**和**提示词模板（Prompts）**，并在聊天机器人客户端实现对应的用户界面。

---

**服务端新增代码**

**资源（只读数据，类似 GET 请求）**

```python
@mcp.resource("papers://folders")
def list_paper_folders():
    # 列出 papers 目录下所有文件夹
    ...

@mcp.resource("papers://{topic}")  # 模板资源
def get_papers_by_topic(topic: str):
    # 从 papers_info.json 读取指定主题的论文信息
    ...
```

**提示词模板**

```python
@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5):
    return f"""请搜索关于 {topic} 的 {num_papers} 篇论文，
    提取每篇论文的关键信息，并按相关性排序总结..."""
```

提示词模板存储在服务端，经过充分测试和优化后提供给用户，用户只需填入动态参数，无需自己做提示词工程。

---

**客户端更新**

连接服务端时，除了获取工具列表，现在还同时获取：

```python
await session.list_prompts()    # 获取提示词模板列表
await session.list_resources()  # 获取资源 URI 列表
```

**聊天界面的新命令**（UI 设计完全由开发者决定，这只是示例）：

- `@folders`：列出所有可用文件夹（访问资源 `papers://folders`）
- `@computers`：读取特定主题的论文数据（访问资源 `papers://computers`）
- `/prompts`：列出所有可用提示词模板
- `/prompt generate_search_prompt topic=math`：使用指定提示词模板并传入参数

---

**演示效果**

输入 `@folders` → 服务端返回已保存的论文文件夹列表（如 "computers"）

输入 `/prompts` → 显示可用模板：`generate_search_prompt`（研究服务端提供）和 `fetch_url`（Fetch 服务端提供）

输入 `/prompt generate_search_prompt topic=math` → 服务端生成完整提示词 → 模型调用 arXiv 工具搜索数学论文 → 结果保存到 math 文件夹 → 通过资源 `@math` 可直接读取（动态更新，无需再次调用工具）

---

**三大原语协同工作**

工具（主动操作）+ 资源（只读数据访问）+ 提示词模板（免提示词工程）组合在一起，让应用既能主动获取数据，也能高效读取已有数据，还能为用户提供最佳实践提示词。

下一节将介绍更强大的宿主界面——Claude Desktop。我们下节课见。