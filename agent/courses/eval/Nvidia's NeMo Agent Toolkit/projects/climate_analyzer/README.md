# climate_analyzer · L3 本地复现(注册工具 + ReAct agent)

课程 L3 的本地可跑版本。课程平台的 `standalone_tools/`、`climate_analyzer/` 包和 NOAA 数据集不随 markdown 发布,此项目按同样结构重建:

| 课程材料 | 本项目对应 |
|---|---|
| NOAA CSV(课程预置) | `src/climate_analyzer/data/temperature_annual.csv`(合成数据,760 行 / 1950–2025 / 10 国,趋势设定:加拿大最快 0.35°C/十年、巴西最慢 0.15) |
| `climate_tools_simple.py`(Part 1 普通函数) | `src/climate_analyzer/climate_tools.py`(5 个函数:单一职责、返回 JSON、docstring 即工具说明) |
| `register.py`(Part 2 注册) | `src/climate_analyzer/climate_analyzer.py`(schema + Config + `@register_function` 三件套 ×5) |
| `configs/config.yml` | `src/climate_analyzer/configs/config.yml`(react_agent + 5 工具 + max_iterations/max_retries 围栏) |

骨架由 `nat workflow create climate_analyzer` 生成(pyproject entry point 自动接线)。

## 一步一步演示

```bash
# 0. 环境(包已 editable 安装进 ~/.venvs/nat;.env 已从 FirstWorkflow 复制)
cd ".../projects/climate_analyzer"
source ~/.venvs/nat/bin/activate
set -a; source .env; set +a

# 1.(Part 1)先证明普通函数能干活——不经过任何 LLM
python -c "
from climate_analyzer.climate_tools import *
df = load_climate_data()
print(calculate_statistics(df))
print(list_countries(df))"

# 2.(Part 3 · Q1 简单)单工具:全球趋势
nat run --config_file src/climate_analyzer/configs/config.yml \
  --input "What is the global temperature trend per decade?"

# 3.(Q2 中等)双工具串联:法国站点数 + 趋势
nat run --config_file src/climate_analyzer/configs/config.yml \
  --input "Tell me about France's climate data. How many stations does it have and what's the temperature trend?"

# 4.(Q3 中等)出图:升温最快的国家
nat run --config_file src/climate_analyzer/configs/config.yml \
  --input "Create a visualization showing which countries have the highest warming trends."
open climate_plot.png

# 5.(Q4 复杂)多步编排:两国对比 + 全球图
nat run --config_file src/climate_analyzer/configs/config.yml \
  --input "Compare the temperature trends of Canada and Brazil. Which one is warming faster? Also create a visualization of global trends."
```

看 verbose 输出里的 `Agent's thoughts / Calling tools / Tool's response`,就是 ReAct 的 Think→Act→Observe 循环。

## 本地复现时踩到的三个坑(课程 notebook 里不会遇到)

1. **Config 类的 `name=` 不要带包名前缀**。NAT 注册时自动拼 `包名/工具名`;写成 `name="climate_analyzer/calculate_statistics"` 会拼出 `climate_analyzer/climate_analyzer/...` 而注册失败。YAML 里引用时才写全称 `_type: climate_analyzer/calculate_statistics`;
2. **`FunctionInfo.from_fn` 的函数必须恰好一个参数**。单参数工具可以直接用原生参数(课程示例);多参数或零参数工具,wrapper 要接收**一个 schema 对象**:`async def _wrapper(params: MyInput) -> str`;
3. **`register.py` 的导入必须与实际符号一致**。它导入失败时 NAT **静默跳过**整个插件,报错只会说"tag 不匹配",不会提示 import error——排查方法:`python -c "import climate_analyzer.register"` 看真实异常。

## L4 演示:Phoenix 观测驱动的工具补缺

前置(已装好):`nvidia-nat[phoenix]`(发送端 exporter)+ `arize-phoenix`(服务器,提供 `phoenix serve`)——注意是两个包。

**关键第三包:`nvidia-nat[profiler]`**。NAT 1.8 把 LLM 级插桩(每次 LLM 调用的 span、token 计数、评测推理步骤)模块化进了这个插件;不装它,`workflow_builder` 里的挂载逻辑会**静默降级为空操作**(try/except ImportError),Phoenix 里只有 workflow/function/tool span、没有 LLM span 和 token,`nat eval` 输出里 `retrieved_contexts` 为空——且无任何警告。Total Cost 仍需在 Phoenix Settings → Models 手动录入 NIM 模型单价。

```bash
# 终端 1:起 Phoenix(常驻,UI 在 http://localhost:6006)
source ~/.venvs/nat/bin/activate
phoenix serve

# 终端 2:baseline(config.yml 已加 telemetry 节,project=climate_analyzer_baseline;
#         工具表里故意没有 station_statistics)
cd .../projects/climate_analyzer
source ~/.venvs/nat/bin/activate
set -a; source .env; set +a
nat run --config_file src/climate_analyzer/configs/config.yml --input "What is the warming rate for Canada?"
nat run --config_file src/climate_analyzer/configs/config.yml --input "What is the second coldest year in the dataset?"
nat run --config_file src/climate_analyzer/configs/config.yml --input "Which country has the most weather stations in our data?"

# 浏览器看 http://localhost:6006 → climate_analyzer_baseline 项目:
# 前两条 trace 短而直,第三条(station)长而绕——工具缺口的形状

# 终端 2:修复版(config_updated.yml:+station_statistics 工具,project 换名对照)
nat run --config_file src/climate_analyzer/configs/config_updated.yml --input "Which country has the most weather stations in our data?"

# 回 Phoenix 对比两个项目的 latency / token / 调用链长度
```

实测对比:baseline 对 station 问题 **4 次工具调用**(有次跑甚至触顶 max_iterations);修复版 **1 次直达**,答案正确(United States)。

## L5 演示:跨框架组合(LangGraph agent 包成 NAT 工具)

新增文件:`src/climate_analyzer/calculator_agent.py`(独立 LangGraph agent,自带 4 个数学工具,对 NAT 零依赖)+ `climate_analyzer.py` 里的 `calculator_agent_tool` 注册(两处 L5 新语法:`framework_wrappers=[LANGCHAIN]` + `builder.get_llm("calculator_llm")` 即 LLM Lifting)+ `configs/config_calculator.yml`(双 LLM + 7 工具)。

```bash
cd .../projects/climate_analyzer && source ~/.venvs/nat/bin/activate
set -a; source .env; set +a
Q="Get the temperature statistics for India and find its trend per decade. If India's temperature continues to increase at this rate, what will the temperature be in 2050?"

# 1. 孤立测试 LangGraph agent(不经过 NAT)
python -c "
import asyncio, os
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from climate_analyzer.calculator_agent import create_calculator_agent, calculate_with_agent
llm = ChatNVIDIA(model='meta/llama-3.1-70b-instruct', base_url=os.environ['NVIDIA_BASE_URL'],
                 api_key=os.environ['NVIDIA_API_KEY'], temperature=0.0)
print(asyncio.run(calculate_with_agent('If 1200 Mt emissions drop 2.5% annually for 5 years then 4% for 5 more, what remains?', create_calculator_agent(llm))))"

# 2. 失败演示:无计算器的 config,agent 心算投影 → 数字不可信
nat run --config_file src/climate_analyzer/configs/config_updated.yml --input "$Q"

# 3. 成功(机制上)演示:带计算器的 config,看委托链
nat run --config_file src/climate_analyzer/configs/config_calculator.yml --input "$Q"
```

**实测记录(比课程预期更有教益)**:step 3 的委托链完全正确(calculate_statistics → 提炼数学问题 → calculator_agent 工具精确计算),但主 agent 出题时把"2.5 个十年"写成了 0.25——**计算精确地算了一道错题**。组合解决了"算不准",没解决"问不对";这正是 L6 evaluation 的引子:委托链的对错,肉眼在 verbose 日志里根本看不出来。

## L6 演示:nat eval 抓住"自信的错答案"

前置:`nvidia-nat[ragas]` + `nvidia-nat[profiler]`(后者决定评测输出里有没有推理步骤,见 L4 一节)。新增:`data/simple_eval.json`(QA 对,ground truth 从 CSV 手工验证:France 1980 = 0.886°C)+ `configs/eval_config.yml`(顶层 `eval` 节:general.dataset + evaluators.ragas.AnswerAccuracy;另挂 telemetry → Phoenix `climate_analyzer_eval` 项目)。

查看结果的两个脚本(项目根目录):`show_eval_results.py`(分数与答案对比)、`show_agent_reasoning.py`(解析 `retrieved_contexts` 里的 Thought/Action/Final Answer 步骤——需 profiler 插件)。

为复现课程剧情,曾把课程的 bug 种进 `calculate_statistics`:schema 声称支持 `start_year/end_year`,实现却忽略(接口承诺 ≠ 实现交付,静默失败)。

```bash
cd .../projects/climate_analyzer && source ~/.venvs/nat/bin/activate
set -a; source .env; set +a

nat eval --config_file src/climate_analyzer/configs/eval_config.yml
# 带 bug 时:0/1 —— agent 自信地答 1.208°C(全区间均值),期望 0.886°C(1980)
# 读 .tmp/eval_output/answer_accuracy_output.json 里的 reasoning 定位:年份参数被工具吞掉

# 修复(climate_tools.py 里补上两行年份过滤)后重跑:1/1
```

实测剧本与课程完全一致:错误答案语气自信、数字不离谱(1.208 vs 0.886),verbose 日志肉眼扫不出问题——只有 grounded eval 能拦截。修复动作是**改工具实现**,eval config 一字未动,重跑即复验。

## L7 演示:nat serve 部署 + 官方 UI(收官)

UI 仓库 clone 在课程仓库外:`~/Documents/NeMo-Agent-Toolkit-UI`(node_modules 不进笔记仓库)。

```bash
# 终端 1:API(用带计算器的完整配置)
cd .../projects/climate_analyzer && source ~/.venvs/nat/bin/activate
set -a; source .env; set +a
nat serve --config_file src/climate_analyzer/configs/config_calculator.yml --host 127.0.0.1 --port 8000
# 自带:OpenAI 兼容端点 /v1/chat/completions、文档 /docs、WebSocket、健康检查

# 终端 2:UI(Next.js dev server,起在 :3000)
cd ~/Documents/NeMo-Agent-Toolkit-UI
NEXT_TELEMETRY_DISABLED=1 npm run dev

# 终端 3(可选):Phoenix 还开着的话,UI 对话的 trace 会进 climate_analyzer_multi_agent 项目
```

浏览器打开 `http://localhost:3000`,设置(齿轮)里把 HTTP 端点指向 `http://127.0.0.1:8000/chat/stream`(流式)或 `/v1/chat/completions`。试题(课程建议,由易到难):Mexico 1990-2000 vs global → France 完整分析 → top-5 升温国出图 → 0.18°C/decade 投影到 2050(走 calculator agent)。

收尾:两个终端各 Ctrl+C;或 `pkill -f "nat serve"; pkill -f "npm run dev"`。

## 观察点(对照 L3 笔记)

- Q1 运行中大概率能看到课程 5 节的原版踩坑复现:agent 第一次不带参数调用 → 工具报错 → agent 读错误信息后改传 `{"country": ""}` 重试成功——`max_retries` 围栏的价值;
- Q4 是 ReAct 编排的完整展示:2× calculate_statistics + create_visualization,最后合成结论(Canada 0.349 vs Brazil 0.156 °C/十年,与数据设定一致)。
