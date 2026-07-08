# nba_sql_tuner · 本地复现《Improving Accuracy of LLM Applications》

DeepLearning.AI × Lamini 这门课的本地可跑版本。课程主线是一个 **NBA SQL Agent**,
用「**评估驱动的准确率提升阶梯**」把幻觉逐级压下去,阶梯的最后一级是 **memory tuning**。

课程跑在 Lamini 托管服务上(Llama-3-8B + 服务器端微调),本项目把这两块都换成**本地可跑**的:

- 推理:本地 HF transformers 小模型(可插拔,默认 `SmolLM2-360M`)
- 微调:用 **LoRA 在本地真跑**,并且**真跑两种**——标准 fine-tuning vs memory tuning,亲眼看差别

> 这门课真正的资产不是「memory tuning 这个技术」,而是**「先便宜后昂贵、每步都用 evaluation 卡住」的决策纪律**,以及 **fine-tuning 与 memory tuning 的本质区别**。本项目就是围绕这两点做的可运行实验台。

---

## 课程材料 ↔ 本项目对应

| 课程材料(不随 markdown 发布) | 本项目对应 | 说明 |
| --- | --- | --- |
| Lamini 托管 Llama-3-8B-Instruct | `backend.py`(HF transformers,可插拔) | `BASE_MODEL` 环境变量切换模型 |
| `util/make_llama_3_prompt.py`(L1) | `prompt.py::make_llama_3_prompt` | 忠实保留;base 模型另走 few-shot 纯文本 |
| `util/get_schema.py`(L2) | `schema.py`(贫乏版 + 丰富版) | 丰富版带 `$9,945,830`/`232 lbs` 示例值 |
| `nba_roster.db`(平台预置) | `db.py` 确定性合成 146 行 | 保留脏字符串格式,幻觉现场的根源 |
| `data/gold-test-set.jsonl` | `gold.py` 生成 15 条并逐条校验 | 参考 SQL 直接在库上跑得出答案,自洽 |
| L3 `GenerationPipeline`(QueryStage+ScoreStage) | `evaluate.py`(纯 Python 两段) | 有效SQL% / 正确SQL% 两个指标 |
| L5「working backwards」数据生成+过滤 | `generate_data.py` | seed 模式(默认)/ model 模式 |
| L5 `llm.train(...)`(派发到 Lamini) | `finetune.py`(本地 LoRA,真跑) | 预设 finetune / memory / memory_light(受控对照) |
| L5 加载 tuned model ID 看提升 | `backend.LLM(adapter=...)` | 加载本地训好的 LoRA |

---

## 快速开始

```bash
cd ".../projects/nba_sql_tuner"
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .            # torch/transformers/peft 等

# 一键跑完整条阶梯(约 10 分钟,含 memory tuning 15 epochs,CPU)
bash scripts/run_all.sh
```

或分步(推荐,能看清每一级):

```bash
python scripts/00_build_data.py      # 重建 nba_roster.db + gold-test-set
python scripts/01_agent_demo.py      # L1/L2:SQL Agent + 现场诊断幻觉
python scripts/02_baseline_eval.py   # L3:baseline 准确率基线
python scripts/03_generate_data.py   # L5:生成 + 过滤微调数据
python scripts/04_finetune.py both   # L5 核心:真跑 finetune + memory tuning
python scripts/05_compare.py         # 三方对比(准确率 + loss + 硬事实并排)
python scripts/06_plot.py            # ASCII loss 曲线 + 准确率阶梯
python scripts/07_fairness_probe.py  # 受控实验 + 泛化探针(诚实修正,见下)
```

---

## fine-tuning vs memory tuning:本项目怎么让你「感受到差别」

课程 L4 讲了区别,但真微调派发到 Lamini 服务器、本地看不到过程。本项目用 **LoRA 在同一个小模型上真跑两种训练**(`finetune.py` 里两个预设),差别体现在**三个可观测的地方**:

| | 标准 fine-tuning | memory tuning |
| --- | --- | --- |
| LoRA rank / alpha | 8 / 16 | 32 / 64 |
| 训练轮数 | 5 epochs | 15 epochs |
| dropout | 0.05 | 0(不正则,故意让它背) |
| 调哪些层 | 只 q/v 注意力投影 | 所有线性层(含 MLP) |
| 可训练参数 | 0.8M | 17M |
| **训练 loss 收敛到** | 停在**平台** 0.12(学到风格,没背事实) | 逼到 **0.0004**(把事实背进权重) |
| **准确率(本机)** | 20%(甚至低于 baseline 33%) | 67%(翻倍) |
| 代价 | 便宜,但收益不稳、可能倒退 | 泛化下降(过拟合的另一面),训练更久 |

> ⚠️ **这张表把两个变量(容量 + 训练量)绑在了一起,所以不是干净的算法对比**。
> 我最初据此说「finetune 学风格、memory 背事实」——**后来用受控实验证明这个结论是错的**:
> memory 领先靠的是**容量**,不是「loss→0」;把 loss 训到 0 反而开始损泛化。
> 详见下面「**这个对比公平吗**」一节(`scripts/07_fairness_probe.py`)。这两个预设在
> `finetune.py::FINETUNE / MEMORY`,可自己改超参复现。

---

## 微调具体是怎么做的(实现机制)

课程 L5 一句 `llm.train(...)` 就把微调派发到 Lamini 服务器,你看不到里面发生了什么。
本项目把这一步**完全摊开在本地**(全在 `finetune.py`)。下面是端到端的机制。

### 1. 用什么技术:LoRA(不是全参数微调)

全参数微调要更新模型全部权重(360M 个),显存/算力都吃不消,还容易灾难性遗忘。
**LoRA** 只在选定的线性层旁挂一对小的低秩矩阵 `A·B`(rank=r),冻结原权重、只训这对小矩阵:

- finetune 预设:r=8、只挂在注意力的 q/v 投影上 → 只有 **0.8M** 个可训练参数(占 0.2%)
- memory 预设:r=32、挂在**所有** 7 个线性层(q/k/v/o + MLP 的 gate/up/down)→ **17M** 个(占 4.6%)

训练产物就是这对小矩阵,存成 `adapters/finetune/` 和 `adapters/memory/`(几 MB),
推理时加载回来和原模型合并(`merge_and_unload`)。对应课程里 `lamini.Lamini(model_name="<tuned-id>")`。

### 2. 训练数据长什么样:{question, sql} → completion-only 样本

`generate_data.py` 产出的每条训练数据是一对 `{question, sql}`(正确写法的 SQL)。
`finetune._build_examples` 把它拼成一条序列,**关键是只在 SQL 答案上算 loss**:

| 序列区段 | 内容 | labels | 是否算 loss |
| --- | --- | --- | --- |
| prompt | schema + `Q: 谁薪资最高?\nSQL:` | 全设 -100 | 否(掩掉) |
| answer | 前导空格 + `SELECT ... ;` + `<eos>` | 真实 token id | 是 |

这叫 **completion-only 掩码**:模型只被要求「学会生成 SQL」,而不是把 prompt 也背下来。
实现就是 `labels[:len(prompt_ids)] = -100`(HF 里 -100 表示该位置不计入交叉熵)。

> prompt 用**零样本**(只有 schema + 问题,没有 few-shot 示例):微调过的模型已经把
> Q→SQL 的映射内化进权重,不需要示例;而且训练格式必须和**微调后推理**的格式逐字一致
> (答案前那个空格都要对齐 `SQL:` 后),否则模型学到的映射和推理时对不上。

### 3. 训练循环:手写,不用 TRL

`finetune.train()` 是一个约 40 行的朴素 PyTorch 循环,没用 TRL 的 `SFTTrainer`。三个原因:

1. **不吃版本 API 变动**——transformers 5.x / peft / trl 的 Trainer API 变得很勤,手写循环不受影响;
2. **直接记录每步 loss**——这样才能画出「memory 把 loss 砸到 0」的曲线(这正是要展示的东西);
3. **完全控制 completion-only 掩码**和梯度裁剪。

循环本身:每个 epoch 打乱样本,逐条 `forward → loss.backward() → clip_grad_norm_(1.0) → optimizer.step()`
(batch=1,AdamW)。梯度裁剪是**必须的**:memory 预设 rank 大、LR 高、调所有层,不裁剪会在长训练里发散
(实测 loss 先降到 0.03、再冲到两位数、最后塌成退化的 0)。每 epoch 的平均 loss 存进 `train_summary.json`。

### 4. 两种预设的差别在哪(以及它到底意味着什么)

同一份 22 条数据、同一个基座,只改这几个超参(都在 `finetune.py::FINETUNE / MEMORY`):

- **finetune**:低 rank(8)、少 epoch(5)、带 dropout、只调注意力两层 → loss 停在 **0.12 平台**。
- **memory**:高 rank(32)、多 epoch(15)、无 dropout、调所有 7 层 → loss 逼到 **0.0004**。

**注意:这两个预设同时变了「容量」和「训练量」两个变量,所以它不是干净的算法对比。**
我最初据此下的结论(finetune 学风格、memory 背事实)是**错的**——`07_fairness_probe.py` 的受控实验
证明:准确率的差主要来自**容量**(rank/层数),把 loss 训到 0 几乎不涨准确率、反而开始损泛化。
真正的 Lamini「memory tuning(MoME)」不是「训得更狠」,而是**多专家 + 路由**的架构,用来在
「记忆 loss→0」的同时不牺牲泛化——这一层本项目**没有复现**。详见「这个对比公平吗」一节。

### 5. 训练在哪跑:强制 CPU

`train()` 里 `device = config.train_device()`,默认 **CPU**——在 Apple Silicon 上用 MPS 跑这种
长时间重载训练会把整机搞崩重启(踩坑第 5 条)。M1 Max CPU 跑 360M LoRA 很稳:finetune ~1min、memory ~4.5min。

---

## 结果(本机实测,SmolLM2-360M / M1 Max / CPU 训练)

准确率(gold 评估集,15 题):

```text
baseline █████████████···························  33.3%   (few-shot prompt,无训练)
finetune ████████································  20.0%   (轻量 LoRA r8/5ep)
memory   ███████████████████████████·············  66.7%   (激进 LoRA r32/15ep,loss→0)
```

训练 loss 曲线:

```text
finetune  1.08 █▄▂▁▁ 0.122         低容量(r8/2层),loss 停在平台
memory    0.67 █▂▁▁▁▁▁▁▁▁▁▁▁▁▁ 0.0004  高容量(r32/7层),loss 一路砸到 ~0
```

(注:loss 差这么多,但准确率的差主要来自**容量**不是 loss 高低——见下节受控实验。)

**怎么读这三个数:**

- **memory 把准确率翻倍(33% → 67%),finetune 反而从 33% 掉到 20%。**
- 直觉上会说「memory 把 loss 逼到 0、把事实背进了权重,所以更强」——**但这个直觉是错的**,
  下一节用两个受控实验证明:memory 领先靠的是**容量**,不是「loss→0」;而且把 loss 训到 0
  其实**开始伤害泛化**。

> ⚠️ **重要修正**:我最初把 finetune/memory 的差归功于「loss 平台 vs loss→0」,这是**记错了账**。
> 见下一节「这个对比公平吗」。`data/results/comparison.md` 是三方逐题对比,
> `data/results/fairness_probe.md` 是修正实验。

---

## 这个对比公平吗?受控实验 + 泛化探针(重要修正)

上面 finetune(r8/2层/5ep)和 memory(r32/7层/15ep)**容量和训练量都不同**,所以「plateau vs loss→0」
至少一半是训练强度的差。为了搞清到底是什么在起作用,`scripts/07_fairness_probe.py` 做了两个受控实验。

### A. 受控实验:容量相同,只变 epoch

`memory_light` 预设和 `memory` **容量完全相同**(都 r32 / 全 7 层),只把 epoch 从 15 砍到 3:

| 模型 | 配置 | final loss | 正确率(gold 15 题) |
| --- | --- | --- | --- |
| memory_light | r32 / 全7层 / **3** epoch | 0.0662 | **66.7%** |
| memory | r32 / 全7层 / **15** epoch | 0.0004 | **66.7%** |

**epoch 3→15 让 loss 从 0.066 砸到 0.0004,准确率却纹丝不动(都 66.7%)。**
所以「把 loss 逼到 0」对准确率几乎没帮助——memory 比 finetune 高那一截,**真正的功臣是容量**
(rank 32 vs 8、调全 7 层 vs 只调 q/v),不是「训到 loss→0」。

### B. 泛化探针:记忆 vs 泛化(matched pairs)

seen 与 unseen **逐条难度配平**——同一种查询,只差实体:seen 用训练过的队/学院,
unseen 用 Suns/Spurs/Mavericks/Kansas/Nets(**从没进过训练**)。差就纯粹反映「记忆 vs 泛化」。
(这是两个各 6 题、难度配平的**专用集**,和上面 gold-15 不是同一批题,数值不要横向比。)

| 模型 | seen(训练实体) | unseen(新实体) | 差(过拟合缺口) |
| --- | --- | --- | --- |
| baseline | 33.3% | 33.3% | 0 |
| finetune | 66.7% | 66.7% | 0 |
| memory_light(loss 0.066) | 100% | 100% | 0 |
| memory(loss 0.0004) | 100% | 83.3% | **+16.7** |

结果和「过拟合=背下来」的直觉相反,但更真实:

- **finetune、memory_light 的 seen=unseen(差 0)**:它们学到的是**结构规律**(薪资 REPLACE、
  AVG(AGE)、median offset、按学院 COUNT),能**迁移到从没见过的新队**——是**泛化**,不是死记。
- **只有训到 loss≈0 的 memory 出现缺口**(seen 100% > unseen 83%):多训的 12 个 epoch 没提高准确率,
  反而**开始背具体训练实体、牺牲对新实体的泛化**——这就是**过拟合的代价**,被干净地量化出来。
- **memory_light(loss 0.066)才是甜点**:seen/unseen 都满分;继续训到 loss 0.0004 是**训过头**了。

### 这三点合起来说明什么

1. 「fine-tuning vs memory tuning」我那组预设的差,主要是**容量**,其次才是训练量,**几乎不是「loss→0」**;
2. 把 loss 一路逼到 0(激进过拟合)**不但不涨准确率,还开始损泛化**——这正是标准微调的核心取舍:
   **记忆(loss→0)迟早以泛化为代价**;
3. 而真正的 Lamini **memory tuning(MoME:多专家 + 路由)** 就是为绕开这个取舍而生的——把不同事实
   分到不同专家,理论上**既能把事实背到 loss→0,又不牺牲泛化**。**这一层(多专家+路由)本项目没有复现**,
   本地单适配器只能在「记忆 ↔ 泛化」的取舍线上移动。这是本项目最重要的诚实边界。

> 换句话说:本项目忠实复现的是「评估驱动地爬准确率阶梯 + 微调的记忆/泛化取舍」,
> 但**没有复现 MoME 如何用架构手段打破这个取舍**——那需要多专家+路由,是 Lamini 的核心 IP。
>
> 另一条诚实边界:360M + 22 条样本,最长的几条 SQL(嵌套 REPLACE 的薪资、SUBSTR 的体重)在
> gold 15 题里 memory 也背不下来(free generation 因 exposure bias 前几个 token 岔开就崩),
> 所以 gold 上封顶 66.7%;换 `Qwen2.5-0.5B-Instruct` 或更大模型可解。

---

## 目录结构

```text
nba_sql_tuner/
├── src/nba_sql_tuner/
│   ├── config.py         # 路径 + 后端配置(BASE_MODEL 切换)
│   ├── schema.py         # 贫乏版 / 丰富版 schema(L2)
│   ├── prompt.py         # Llama-3 模板(L1) + base 模型 few-shot 纯文本
│   ├── db.py             # 确定性合成 nba_roster(脏字符串格式)
│   ├── gold.py           # gold-test-set,逐条校验
│   ├── backend.py        # LLM 适配层(chat / 补全 / 加载 LoRA)
│   ├── evaluate.py       # 评估流水线(QueryStage+ScoreStage,L3)
│   ├── generate_data.py  # 合成数据 + 过滤(L5)
│   └── finetune.py       # LoRA 训练:finetune / memory / memory_light 预设(L5 核心)
├── scripts/00..07 + run_all.sh   # 07 = 受控实验 + 泛化探针
├── data/                 # 运行时生成:db / gold / training_data / results
└── adapters/             # 运行时生成:finetune/ 和 memory/ 两个 LoRA
```

---

## 本地复现踩到的坑(课程 notebook 里不会遇到)

1. **HF 的大文件 CDN 在部分网络下被「只放行 header、掐掉 body」**。所有 instruct 模型
   (Qwen2.5-0.5B-Instruct 等)现都重定向到 `us.aws.cdn.hf.co`(xet 后端),本机
   `curl` 拿得到 302/200 和 `content-length`,但 body 传 0 字节就断(exit 18/92)。
   直连、hf-mirror、HTTP/1.1、range 请求全试过,同样结果——这是网络环境层的封锁,不是脚本问题。
   **对策**:默认退回本机 HF 缓存里唯一权重完整的生成模型 `SmolLM2-360M`;网络允许时
   `export BASE_MODEL=Qwen/Qwen2.5-0.5B-Instruct` 一行升级(它更强且自带 chat 模板)。

2. **base 模型不能 zero-shot 出 SQL,必须 few-shot 纯文本补全**。`SmolLM2-360M` 是 base(非
   instruct),套 chat 模板会输出 `<|im_start|>` 之类**未训练的特殊 token → 满屏乱码**。
   改成纯文本 few-shot(`prompt.plain_fewshot_prompt`)后立刻正常出 SQL——而且 few-shot 只
   示范简单查询,模型在薪资/体重上照样幻觉,**反而更忠实复现了课程 L2 的幻觉现场**。

3. **few-shot 示例的选择直接决定 baseline 会不会幻觉**。如果 few-shot 里就示范了
   `REPLACE(SALARY...)`,baseline 会照抄、幻觉消失,阶梯就没有起点了。所以 few-shot 故意
   只放计数/按 AGE 排序/分组这类**不泄露技巧**的例子,把「薪资要 REPLACE、体重要 SUBSTR」
   留给微调去教。

4. **transformers 5.x 的 `apply_chat_template` 默认返回 dict 不是 tensor**。要
   `return_dict=True` 再取 `["input_ids"]`,否则 `.shape` 报 `KeyError`。

5. **⚠️ 在 Apple Silicon 上,长时间重载的 LoRA 训练不要跑 MPS(苹果 GPU),会把整机搞到重启**。
   实测激进 memory 预设(rank 64、调所有层、长跑)在 MPS float32 下触发
   `kIOGPUCommandBufferCallbackErrorSubmissionsIgnored`(GPU 命令缓冲错误)→ 内核 panic → **重启**
   (本机中招两次)。**对策:训练强制走 CPU**(`config.train_device()` 默认 CPU;`04_finetune.py`
   用它)。M1 Max CPU 跑 360M LoRA 很稳:finetune ~1min、memory ~4.5min。推理/评估是短任务,
   继续用 MPS 没问题。想冒险用 MPS 训练:`export TRAIN_DEVICE=mps`(不建议)。

6. **memory 预设必须加梯度裁剪,否则会发散**。rank 大、LR 高、调所有层,不裁剪时 loss 会先降到
   0.03、再冲到两位数、最后塌成退化的 0.0000(模型直接输出 EOS,推理时全空)。
   加 `clip_grad_norm_(max_norm=1.0)` 后曲线才干净地一路降到 ~0。

7. **tuned 模型走零样本、baseline 走 few-shot —— 各在自己的「工作点」评估才公平**。baseline 没
   few-shot 拐杖根本不出 SQL;而微调过的模型已把映射内化,再喂 few-shot 的简单示例反而把它
   往简单/错误答案带偏(实测 memory 从 67% 掉到 40%)。训练格式必须与各自的推理格式一致
   (`finetune.py` base 分支用 `plain_prompt(..., fewshot=False)`,答案前留一个空格对齐 `SQL:` 之后)。

8. **小模型 + 长 SQL 有 exposure bias 上限**。teacher-forced 命中率 91% 的模型,free generation
   仍会在前几个 token 岔开(`NAME`→`SME`、`CAST`→`SAST`)后整句崩掉。所以硬事实里最长的几条
   (嵌套 REPLACE)memory 也背不下来——这是模型容量问题,换更大模型即可。

---

## 与我的资产映射

- 观测与评估:`agent/skills/agent-selection/5-observability-eval.md`——evaluation 作为准确率提升流水线的**控制阀**,不是事后验收(本项目 `evaluate.py` 就是每一级的卡点)
- 选型矩阵:`[[project_selection_matrix]]`——「prompt → RAG → fine-tune → memory tune」是模型/微调层的成本-收益选型主线,本项目把最贵的两级(fine-tune / memory tune)做成了可对比的实验
