"""L1 · 从概率分布看幻觉 (本地化: DeepSeek 替代 Lamini 托管 Llama-3-8B)

课程叙事: LLM 是 next-token 概率模型, 幻觉 = 分布上"合理"但事实上错误的延伸;
问题越冷门/越复杂, 分布越平, 越容易编造。

运行: cd L1 && ../.venv/bin/python main.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_stack import MODEL, banner, ds_generate
from util.make_llama_3_prompt import make_llama_3_prompt


def main():
    banner("①", "Llama-3 prompt 模板长什么样 (课程 util 原样保留)")
    print(make_llama_3_prompt("Tell me a joke about birthday cake", "You are a helpful assistant."))
    print(f"""  说明: Lamini 直连 base 模型要手工拼 <|begin_of_text|> 等特殊 tag;
  chat API ({MODEL}) 由服务端套模板, 我们只传 messages —— 概念相同, 层次不同""")

    banner("②", "简单问题: 分布尖锐, 不易幻觉")
    print(ds_generate(
        "Given an arbitrary table named `sql_table`, "
        "write a query to return how many rows are in the table.",
        max_tokens=150,
    ))

    banner("③", "难度递增: average -> p95, 看模型何时开始'编'")
    print("--- average height (标准 SQL 有现成写法):")
    print(ds_generate(
        "Given an arbitrary table named `sql_table`, "
        "help me calculate the average `height` where `age` is above 20.",
        max_tokens=150,
    ))
    print("\n--- p95 height (sqlite 没有 percentile 函数, 课程时代 Llama-3-8B 会编一个):")
    print(ds_generate(
        "Given an arbitrary table named `sql_table`, "
        "Can you calculate the p95 `height` where the `age` is above 20?",
        max_tokens=250,
    ))
    print("\n--- 明确要求 sqlite 后:")
    print(ds_generate(
        "Given an arbitrary table named `sql_table`, "
        "Can you calculate the p95 `height` where the `age` is above 20? Use sqlite.",
        max_tokens=250,
    ))

    banner("④", "本课结论")
    print("""  幻觉不是 bug 是概率延伸: 模型永远给出"分布上最顺"的答案。
  提升准确率的路线图(本课主线): prompt 加信息 -> 评估定位 -> 微调改分布。
  注: deepseek 比课程当年的 Llama-3-8B 强, ③ 可能直接给出正确的
  order by/limit/offset 写法 —— 这本身就是"模型能力也是准确率变量"的证据""")


if __name__ == "__main__":
    main()
