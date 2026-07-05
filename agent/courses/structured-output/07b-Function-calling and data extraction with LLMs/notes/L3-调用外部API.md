# L3 调用外部 API:让 function calling LLM 接入 Web 服务

## 核心问题

前几课调的都是本地 Python 函数,但外面有一整个 Web 服务的世界(RESTful API)。怎么让 function-calling 模型用上它们?

## 核心手法:适配器(adapter)模式

模型不能直接调外部 API,你要**写一个 Python 工具把外部 endpoint 包起来**。这个工具做的事:把模型生成的 Python 参数,转换成外部 API 需要的参数格式(URL 拼接、query 参数、header 等),发请求,取回结果。

课程两个例子:
1. **简单 REST**:一个笑话 API——写个 `get_joke(category)` 工具,把 category 拼进 URL,发 GET,返回 setup + delivery。
2. **OpenAPI 规范驱动**:open-meteo 天气 API——下载它的 OpenAPI(YAML)规范 → 转成 JSON → 用 openapi-python 生成器**自动把规范转成能查 endpoint 的 Python 代码** → 再用 `inspect` 自动生成工具描述喂给模型。

## 为什么这个模式重要

**"写工具去包 API"本质是在统一异构接口。** 外部资源用各种各样的 API 规范(OpenAPI 只是其中一种),你通过写一层工具适配器,把它们都统一成"模型能调的函数"这一种形态。

这正是 **MCP 要解决的同一个问题**——把五花八门的外部系统统一成模型能理解的工具接口。这门课手工做的"适配器 + OpenAPI 转工具",在今天很大程度上被 MCP server 标准化了:你不用每个 API 手写适配器,而是套 MCP 协议。对应你已学的 `10-MCP` 和面试包 `03-mcp-gateway`——**这一课可以看成"MCP 出现之前,大家是怎么手工干这件事的",理解了痛点,就理解了 MCP 为什么值钱。**

## 一个值得记的细节

从 OpenAPI 规范自动生成工具时,课程还是要**手工修一些数据类型**(YAML 里的 int/float 转换),说明"规范自动转工具"不是完全无缝的。这也是为什么后来需要 MCP 这种更规整的协议层来吃掉这些脏活。
