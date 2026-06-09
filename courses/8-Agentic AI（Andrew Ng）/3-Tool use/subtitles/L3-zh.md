让我们来看看如何编写代码，让 LLM 实现工具调用。

**使用 AISuite 库**

这里介绍一个叫做 **AISuite** 的开源库，它简化了调用多个 LLM 提供商的过程。代码语法与 OpenAI 的标准语法非常相似：

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=[get_current_time],
    max_turns=5
)
```

几个关键参数说明：
- `tools`：提供给 LLM 可调用的工具列表
- `max_turns`：限制 LLM 连续调用工具的最大次数，防止陷入无限循环。实际上很少触及这个上限，设为 5 即可

**AISuite 如何描述工具给 LLM**

AISuite 会自动读取函数的**文档字符串（docstring）**，生成一份 JSON Schema，告诉 LLM：
- 函数的名称
- 函数的用途描述
- 函数的参数及其含义

对于带参数的函数（如含时区参数的 `getCurrentTime`），JSON Schema 还会描述参数的格式（如 `America/New_York` 或 `Pacific/Auckland`），让 LLM 知道应该传入什么值。

有些 API 需要你手动构建这份 JSON Schema，而 AISuite 自动完成了这一切。

**完整流程一步搞定**

使用 AISuite 时，一次函数调用就能处理完整流程：
1. 判断 LLM 是否想调用工具
2. 如果是，自动调用对应函数
3. 将函数返回值反馈给 LLM
4. 重复上述过程，直到达到 `max_turns` 上限

你无需手动处理中间步骤，全部由这一个函数调用封装完成。

**特别值得关注：代码执行工具**

在所有可以给 LLM 的工具中，有一个格外特殊——**代码执行工具**。告诉 LLM"你可以编写代码，我会帮你执行"，这会带来极其强大的能力，因为代码几乎可以做任何事情。下一个视频，我们将专门深入探讨代码执行工具。我们下个视频见。