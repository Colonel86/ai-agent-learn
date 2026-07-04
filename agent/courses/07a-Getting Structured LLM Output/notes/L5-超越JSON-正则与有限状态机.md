# L5 结构远不止 JSON:正则表达式 + 有限状态机

## Outlines 底层用的是正则表达式,不是"JSON 专用逻辑"

L4 的 logits 约束机制,底层依赖**正则表达式转换成有限状态机(FSM)**这套经典理论。任何正则能描述的格式,都能被 Outlines 用同一套机制约束生成——JSON 只是其中一种特例,不是全部。

## 为什么正则能转状态机,又为什么这对"生成"有用

正则可以等价转换成一个有限状态机:每个状态代表"已匹配到这里",每条边代表"下一个字符是什么就跳到哪个状态",到达终止状态且字符串用完就算匹配成功。

这套"匹配"逻辑反过来就是"生成"逻辑:Outlines 生成的每一步都知道当前处于状态机哪个状态,于是只看这个状态有哪些合法出边(哪些下一个 token 被允许),把其余 token 的 logits 清零。也就是说,**状态机把"整个字符串是否合法"这个全局判断,拆成了"每步只看当前状态允许什么"的局部判断**——这正是逐 token 生成场景下能高效约束的关键。

## 一个反直觉但重要的理论细节

通常认为上下文无关文法(CFG)比正则更强大(能表达括号嵌套这类正则无法表达的结构)。但只要**限制递归深度**,任意 CFG 都可近似表示成正则——这意味着即便是语法正确的编程代码这种复杂结构,理论上也能纳入这套约束解码框架。

## 课程展示的"JSON 之外"的应用(附代码)

**① 分类标签(choice)**——零样本/单样本分类最常用:

```python
chooser = outlines.generate.choice(model, ['positive', 'negative'], sampler=greedy())
chooser(prompt)   # 只可能返回 'positive' 或 'negative',比写正则省事
```

**② 电话号码 / 邮箱(regex)**——统一格式,数据抽取利器:

```python
phone_regex = r'\([0-9]{3}\) [0-9]{3}-[0-9]{4}'          # 强制 (XXX) XXX-XXXX
phone_gen = outlines.generate.regex(model, phone_regex, sampler=greedy())
# 输入 "206-555-1234" 也会被规整成 (206) 555-1234
```

**③ HTML 标签 / CSV / YAML**——建议对复杂正则先用 Python `re` 本地验证能否匹配目标样例,再喂给模型,避免正则写错却到推理阶段才发现:

```python
img_regex = r'<img src="\w+\.(png|jpg|gif)" alt="[\w ]+">'
assert re.search(img_regex, example)                     # 先本地验证
img_gen = outlines.generate.regex(model, img_regex)

csv_regex = r'Code,Amount,Cost\n([A-Z]{3},[0-9]+,[0-9]+\.[0-9]{2}\n){1,3}'
csv_out = outlines.generate.regex(model, csv_regex)(prompt)
pd.read_csv(StringIO(csv_out))                            # 直接从 LLM 输出灌进 pandas
```

**④ 带推理步骤的半结构化输出(对应 GSM8K 数学题评测)**——用 Outlines 的 DSL 拼,不用手写复杂正则:

```python
from outlines.types import sentence, digit
from outlines.types.dsl import to_regex

reasoning = "Reasoning: " + sentence.repeat(1, 2)    # 先 1~2 句推理
answer    = "So the answer is: " + digit.repeat(1, 4) # 再输出以固定短语开头的数字答案
gen = outlines.generate.regex(model, to_regex(reasoning + "\n" + answer), sampler=greedy())
```

这个模式对需要"先思考再给结构化结论"的 Agent 场景很有参考价值——**结构化不等于牺牲思维链,两者可以结合**。课程最后还留了个"hot dog / not a hot dog"的多模态(视觉)分类练习,让你把约束用到图像标注上,保证标签始终一致(小写、无句号)。

## 一句话总结这门课

三条路线不是替代关系,而是按"能否拿到 logits"和"对成本/延迟的敏感度"两维选型:能拿到 logits 就优先约束解码(零成本、零重试、格式不限);拿不到但要跨供应商就用重提示库(Instructor);只用单一供应商且追求最省事就用供应商原生结构化输出 API。
