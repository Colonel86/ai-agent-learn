# L1 · 快速上手:最小闭环

## 本课目标

跑通 mem0 记忆的完整生命周期,建立对三件事的体感:

1. **add() 不是存对话,是存"LLM 蒸馏后的事实"**——对话三句话进去,出来的是几条独立事实;
2. **矛盾信息触发消解**——"搬到上海"应该 UPDATE 掉"住在杭州",看 event 字段验证;
3. **history 表是写路径的显微镜**——每条记忆的 ADD/UPDATE/DELETE 事件全程可追溯(但注意:向量库里只有最新值,时间轴只在 history 这张旁路表里,这就是"无时间轴"批评的准确含义)。

## 运行

```bash
cd "agent/courses/memory/12c-Mem0 Hands-On/code"
source .venv/bin/activate
python L1/main.py --reset
```

首次运行 fastembed 会经 hf-mirror 下载 `bge-small-zh-v1.5`(约 100MB,一次性)。

## 观察点(跑的时候对照)

| 步骤 | 看什么 | 对应的纸面判断 |
|---|---|---|
| ① add | 3 句对话变成几条事实?"手冲 + 浅烘埃塞"拆成一条还是两条? | 框架现状.md §2.2 抽取阶段 |
| ③ search | 换了问法("有什么讲究")还能命中吗?score 多少? | §2.3 读路径 |
| ④ 矛盾 add | event 是 UPDATE 还是错误地 ADD 并存?这是消解质量的第一个样本 | §2.2 消解阶段 + §2.7 待验证① |
| ⑤ history | UPDATE 前后的 old_memory/new_memory 都在事件流里 | §七 "无时间轴"的准确边界 |
| ⑥ update/delete | 不经 LLM 的确定性写入——这就是 L5"写入分流"里走确定性那一路的原型 | 6-memory.md 写入分流 |

## 记时间和成本

add() 每次多烧 1–2 次 DeepSeek 调用(§2.7 待验证②)。跑的时候留意每个 add 的耗时体感,L7 会正式测。

## 练习

1. 把 `user_id` 换成别人再 `search`,确认查不到 ming 的记忆(L4 预演);
2. 打开 `history.db`(`sqlite3 L1/history.db 'select * from history;'`)看事件表结构;
3. 故意 add 一句废话("今天天气不错"),看会不会产生记忆(NOOP 的抽取端表现)。

## 已知坑位

- `DEEPSEEK_API_KEY` 没配 → 初始化就报错,先 `cp .env.example .env`;
- 若 mem0 对 DeepSeek 的 json 输出解析报错(理论上 json_object 模式没问题),记录报错原文——那就是 12 系列"坑 1"的 mem0 变体,处理经验在 `env-local-llm-stack` 备忘里。
