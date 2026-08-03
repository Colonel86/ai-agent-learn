#!/usr/bin/env bash
# 一键启动 L3-L6 演示所需的两个服务（L1 不需要，裸 OpenAI SDK）：
#   127.0.0.1:8003  本地网关（fastembed embeddings + DeepSeek chat 转发关 thinking）
#   127.0.0.1:8283  Letta server（chat/embedding 都经 8003 网关）
# Ctrl-C 一并退出。
set -e
cd "$(dirname "$0")"

# 本机系统代理会劫持 localhost 流量，必须绕过
export NO_PROXY="localhost,127.0.0.1" no_proxy="localhost,127.0.0.1"

# 把 .env 显式导出给两个服务（OPENAI_API_KEY/OPENAI_BASE_URL/HF_ENDPOINT 等）
set -a; [ -f .env ] && source .env; set +a

.venv/bin/python gateway.py &
GATEWAY_PID=$!
trap 'kill $GATEWAY_PID 2>/dev/null' EXIT

exec .venv/bin/letta server --port 8283
