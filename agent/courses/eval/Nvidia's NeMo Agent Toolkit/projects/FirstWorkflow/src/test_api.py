# 测试 nat serve 起的 API —— 这是客户端,前提是服务端已在另一个终端运行
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",   # OpenAI 兼容端点
    headers={"Content-Type": "application/json"},
    json={
        "messages": [
            {
                "role": "user",
                "content": "What causes El Nino and how does it affect global weather?",
            }
        ],
        "stream": False,
    },
)

if response.status_code == 200:
    result = response.json()
    print(result["choices"][0]["message"]["content"])
else:
    print(f"Error: {response.status_code}")
    print(response.text)
