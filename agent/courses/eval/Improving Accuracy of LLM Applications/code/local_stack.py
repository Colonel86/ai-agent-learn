"""本地化适配层：DeepSeek 兼容 API 替代 Lamini 托管 Llama-3-8B。

课程原版: lamini.Lamini(model_name="meta-llama/Meta-Llama-3-8B-Instruct"),
llm.generate(prompt, output_type={...}) 做结构化输出, llm.train() 派发服务端微调。
本地化:
- 推理: DeepSeek (openai SDK); output_type -> json_object 模式 + 手动解析
- 微调: 本地 LoRA 实验台见 ../projects/nba_sql_tuner (真跑 finetune vs memory tuning)
"""

import json
import os
import sqlite3
import time
from pathlib import Path

from dotenv import load_dotenv

_CODE_DIR = Path(__file__).resolve().parent
load_dotenv(_CODE_DIR / ".env")

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI

MODEL = os.getenv("MODEL", "deepseek-v4-flash")
client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
)
DS_EXTRA_BODY = {"thinking": {"type": "disabled"}}


def ds_generate(user: str, system: str = "", json_mode: bool = False, max_tokens: int = 600) -> str:
    """对应课程的 llm.generate(prompt); json_mode 对应 output_type 结构化输出"""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    for attempt in range(4):
        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0,
                max_tokens=max_tokens,
                extra_body=DS_EXTRA_BODY,
                **kwargs,
            )
            return r.choices[0].message.content
        except (APIConnectionError, APITimeoutError, InternalServerError):
            if attempt == 3:
                raise
            time.sleep(2**attempt)


def ds_json(user: str, system: str = "", max_tokens: int = 600) -> dict:
    return json.loads(ds_generate(user, system, json_mode=True, max_tokens=max_tokens))


def run_sql(db_path, sql: str):
    """执行 SQL 返回 pandas DataFrame (course: pd.read_sql + sqlite engine)"""
    import pandas as pd

    conn = sqlite3.connect(db_path)
    try:
        return pd.read_sql(sql, con=conn)
    finally:
        conn.close()


def banner(step: str, title: str):
    line = "=" * 64
    print(f"\n{line}\n{step} {title}\n{line}")
