# FirstWorkflow · L2 最小 NAT 工作流本地复现

课程 L2 的动手项目:一份最小 YAML 配置(`llms` + `workflow` 两节)构成的气候问答助手——`nat run` 本地跑通,`nat serve` 变成 OpenAI 兼容 API。它是后续 climate_analyzer(L3-L7)的起点。

## 文件说明

| 文件 | 用途 |
|---|---|
| `config.yml` | 全部"代码":定义 LLM 连接(NIM/llama-3.1-70b)+ chat_completion 工作流 |
| `.env`(不进 git) | `NVIDIA_API_KEY` + `NVIDIA_BASE_URL`,从 build.nvidia.com 申请 |
| `src/test_env.py` | 验证 .env 能被读到(打印 API key loaded: Yes/No) |
| `src/test_api.py` | API 客户端测试:向 `nat serve` 起的服务发一条聊天请求 |

## 前置(一次性)

虚拟环境统一放在 `~/.venvs/nat`(Python 3.13 + `nvidia-nat[langchain]`),**不要建在本项目目录下**——本课程路径含冒号,会把 PATH 劈裂导致 venv 激活失效(详见下方踩坑记录)。

## 快速开始

```bash
cd ".../projects/FirstWorkflow"
source ~/.venvs/nat/bin/activate     # ① 激活环境(每个新终端都要做)
set -a; source .env; set +a          # ② 把 .env 导入 shell(nat 是 CLI,不会自动读 .env)

# 单次运行
nat run --config_file config.yml \
  --input "What is the difference between weather and climate?"
```

## 部署为 API 并测试(两个终端)

```bash
# 终端 1:起服务(常驻,Ctrl+C 停止;自带 /docs 文档和健康检查)
nat serve --config_file config.yml --host 127.0.0.1

# 终端 2:当客户端(同样先激活环境;客户端不需要 .env,密钥在服务端)
python src/test_api.py
# 或用 curl:
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What causes El Nino?"}],"stream":false}'
```

## 踩坑记录(本地环境 vs 课程平台)

1. **路径含冒号 → venv 必须外置**:本课程目录名带 `:`(原名)或空格,PATH 以冒号分隔条目,venv 建在这种路径下激活后命令找不到。解法:venv 放 `~/.venvs/nat`;
2. **环境变量插值语法**:NAT 1.8 的 config 里要写 `${NVIDIA_API_KEY}`(带花括号),课程平台老版本的 `$NVIDIA_API_KEY` 会被当字面字符串,报 `InvalidUrlClientError`;
3. **`.env` 缺 `NVIDIA_BASE_URL`**:课程平台预设了它,自己环境要补 `https://integrate.api.nvidia.com/v1`;
4. **改完 `.env` 要重新 source**:插值读的是进程环境变量,不是文件;每个终端、每次改动后都要 `set -a; source .env; set +a`;
5. **端口被旧进程占用**:`nat serve` 起不来或响应异常时,先 `lsof -nP -iTCP:8000 -sTCP:LISTEN` 看是谁在接请求,`pkill -f "nat serve"` 清理。

## 局限(引出 L3)

这个 agent 只是一次 LLM 调用:无外部数据、来源可能过时或幻觉。需要真实数据的问题(如"2023 年最暖的 5 个国家")它答不可靠——L3 在 `../climate_analyzer` 里给它装上真数据和工具。
