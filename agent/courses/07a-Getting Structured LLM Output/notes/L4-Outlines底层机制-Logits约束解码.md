# L4 Outlines 底层机制:直接操作 logits 实现零重试的结构化生成

## 从"检查输出"到"约束生成过程"的范式转变

前两课(OpenAI 原生 / Instructor)本质都是"先让模型自由生成,再检查是否合法",不合法就重来。Outlines 代表的约束解码走的是完全不同的路:**在每一步生成 token 之前,直接修改模型给出的 logits,把不满足目标结构的 token 概率清零**,这样无论采样器怎么选,选出来的序列都必然合法——不需要"生成完再检查",从根源排除了非法输出。

## 代码骨架

```python
import outlines
from pydantic import BaseModel

model = outlines.models.transformers("HuggingFaceTB/SmolLM2-135M-Instruct")  # 需能拿到 logits→用开源模型

class Person(BaseModel):
    name: str
    age: int

generator = outlines.generate.json(
    model, Person,
    sampler=outlines.samplers.greedy(),   # 贪心采样:每步取概率最高的合法 token,保证结果可复现
)
person = generator(prompt)                 # -> Person(name=..., age=...),100% 合法
```

注意 Outlines 不像多数 SDK 自动加聊天模板的特殊 token,需要手动套模板(课程用 `utils.template(...)`)——这是刻意的,底层管理 prompt 换来对生成过程更强的控制。

## 具体怎么工作(以生成 `{"name": ..., "age": ...}` 为例)

1. 模型在每个位置正常输出一个 logits 分布(对所有可能的下一个 token 打分)。
2. Outlines 知道当前目标结构处于哪个阶段(如"现在该输出字段名 name 的开头引号"),于是**只保留符合这个阶段的 token,其余概率清零、再重新归一化**。
3. 采样器(贪心或按概率采样)只能从被允许的候选里选。
4. 逐 token 重复,直到整个 JSON 生成完毕。

课程用可视化展示(`plot_token_distributions`,蓝条=无约束概率,橙条=约束后概率):第一个位置,模型本来最想输出自然语言(如 "Here" "I"),约束后这些 token 概率被清零,只剩花括号、引号这些合法 JSON 起始符有非零概率。这解释了为什么约束解码"关掉了模型说自然语言的倾向"。字段名位置(如 `name`)约束后概率接近 99.7%,而字符串值内部(如名字 John)约束前后概率几乎一致——因为那里本来就没什么格式约束。

## 为什么几乎零额外开销

只是在模型正常前向传播产出的 logits 上做一次掩码(mask),不需要额外模型调用、不需要重试、不需要把错误拼回 prompt 重新推理。相比 Instructor"失败了整个 prompt 重发一次"的重试成本,约束解码的开销可以忽略。

## 唯一门槛:必须拿得到 logits

只能用在:开源模型(课程用极小的 SmolLM2-135M,CPU 就能跑),或自己托管的专有模型。如果只能通过 API 调别人的闭源模型(如直接调 OpenAI 而非自托管),拿不到中间 logits,这条路走不通,只能退回 L2/L3。这是选型最关键的分界线。

## `Literal` 在约束解码下的表现

```python
class EmployedPerson(BaseModel):
    name: str
    age: int
    job: Literal['Doctor', 'Basketball Player', 'Welder', 'Dog catcher']
```

到 `job` 字段时,不在列表里的选项(如模型本想说的 "software")会被约束直接掐掉,只在给定几个职业里选——这正是"约束在生成时强制生效"的直观体现。
