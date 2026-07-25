#!/usr/bin/env bash
# 一键启动 L5 演示所需的两个服务：
#   127.0.0.1:8003  本地 embedding 服务（fastembed, bge-small-en-v1.5, 384 维）
#   127.0.0.1:8283  Letta server（读取本目录 .env 拿 OPENAI_API_KEY 调 DeepSeek）
# Ctrl-C 一并退出。
set -e
cd "$(dirname "$0")"

# 本机系统代理会劫持 localhost 流量，必须绕过
export NO_PROXY="localhost,127.0.0.1" no_proxy="localhost,127.0.0.1"

.venv/bin/python embed_server.py &
EMBED_PID=$!
trap 'kill $EMBED_PID 2>/dev/null' EXIT

exec .venv/bin/letta server --port 8283
