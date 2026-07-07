uv venv .venv-nat --python 3.13
source .venv-nat/bin/activate
uv pip install nvidia-nat
uv pip install "nvidia-nat[langchain]"
python src/main.py

source ~/.venvs/nat/bin/activate
set -a; source .env; set +a

nat serve --config_file config.yml

nat run \
  --config_file config.yml \
  --input "What is the difference between weather and climate?"
  
curl -s <http://localhost:8000/v1/chat/completions> \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"What causes El Nino?"}],"stream":false}'


cd "/Users/ming/Documents/ai-agent-learn/agent/courses/eval/Nvidia's NeMo Agent Toolkit/projects/FirstWorkflow"
source ~/.venvs/nat/bin/activate
set -a; source .env; set +a
nat serve --config_file config.yml --host 127.0.0.1

终端 2,等服务就绪后跑测试:

cd "/Users/ming/Documents/ai-agent-learn/agent/courses/eval/Nvidia's NeMo Agent Toolkit/projects/FirstWorkflow"
source ~/.venvs/nat/bin/activate
python src/test_api.py