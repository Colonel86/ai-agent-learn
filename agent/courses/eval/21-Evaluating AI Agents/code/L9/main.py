"""L9 · Lab 4: 轨迹与收敛度评估 (本地化: arize-phoenix-client 2.x experiments + DeepSeek)

思路: 同一个意图换 17 种问法, 理想情况下 agent 应走一样短的路径。
convergence = 最优路径长度 / 实际路径长度 (越接近 1 越收敛)。

课程原版 phoenix.experiments.run_experiment -> 新版挂在 Client().experiments 下:
- px.Client().upload_dataset          -> Client().datasets.create_dataset
- run_experiment(dataset, task)       -> Client().experiments.run_experiment(dataset=, task=)
- @create_evaluator + evaluate_experiment -> 普通函数 + Client().experiments.evaluate_experiment

运行: cd L9 && ../.venv/bin/python main.py  (需要本地 phoenix serve 已启动)
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from local_stack import PHOENIX_ENDPOINT, banner, phoenix_client

from utils import PROJECT_NAME, run_agent  # noqa: E402  (副作用: 注册 tracer)

px_client = phoenix_client()

convergence_questions = [
    "What was the average quantity sold per transaction?",
    "What is the mean number of items per sale?",
    "Calculate the typical quantity per transaction",
    "What's the mean transaction size in terms of quantity?",
    "On average, how many items were purchased per transaction?",
    "What is the average basket size per sale?",
    "Calculate the mean number of products per purchase",
    "What's the typical number of units per order?",
    "What is the average number of products bought per purchase?",
    "Tell me the mean quantity of items in a typical transaction",
    "How many items does a customer buy on average per transaction?",
    "What's the usual number of units in each sale?",
    "What is the typical amount of products per transaction?",
    "Show the mean number of items customers purchase per visit",
    "What's the average quantity of units per shopping trip?",
    "How many products do customers typically buy in one transaction?",
    "What is the standard basket size in terms of quantity?",
]


def format_message_steps(messages):
    """把 messages 轨迹转成可读的步骤列表"""
    steps = []
    for message in messages:
        role = message.get("role")
        if role == "user":
            steps.append(f"User: {message.get('content')}")
        elif role == "system":
            steps.append("System: Provided context")
        elif role == "assistant":
            if message.get("tool_calls"):
                for tool_call in message["tool_calls"]:
                    steps.append(f"Assistant: Called tool '{tool_call['function']['name']}'")
            else:
                steps.append(f"Assistant: {message.get('content')}")
        elif role == "tool":
            steps.append(f"Tool response: {message.get('content')}")
    return "\n".join(steps)


def run_agent_and_track_path(input):
    """实验 task: 跑 agent 并记录路径长度 (input = example 的 input 字段)"""
    messages = [{"role": "user", "content": input.get("question")}]
    ret = run_agent(messages)
    return {"path_length": len(ret), "messages": format_message_steps(ret)}


def main():
    banner("①", f"上传数据集: 同一意图的 {len(convergence_questions)} 种问法")
    convergence_df = pd.DataFrame({"question": convergence_questions})
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dataset = px_client.datasets.create_dataset(
        name=f"convergence_questions-{now}",
        dataframe=convergence_df,
        input_keys=["question"],
    )
    print(f"  dataset id={dataset.id}, {dataset.example_count} 条")

    banner("②", f"跑实验: 每个问法跑一遍 agent, 记录路径长度 (project={PROJECT_NAME})")
    experiment = px_client.experiments.run_experiment(
        dataset=dataset,
        task=run_agent_and_track_path,
        experiment_name="Convergence Eval",
        experiment_description="Evaluating the convergence of the agent",
        timeout=600,
    )

    banner("③", "计算最优路径长度")
    outputs = [run.get("output") for run in experiment["task_runs"]]
    path_lengths = [o.get("path_length") for o in outputs if o and o.get("path_length")]
    optimal_path_length = min(path_lengths)
    print(f"  路径长度分布: {sorted(path_lengths)}")
    print(f"  最优路径长度: {optimal_path_length}")

    banner("④", "收敛度评估: optimal / actual, 回写实验")

    def convergence_eval(output) -> float:
        if output and output.get("path_length"):
            return optimal_path_length / float(output.get("path_length"))
        return 0.0

    px_client.experiments.evaluate_experiment(
        experiment=experiment, evaluators=[convergence_eval], timeout=600
    )

    banner("⑤", "完成")
    print(f"  到 {PHOENIX_ENDPOINT}datasets 查看实验与 convergence 分数")


if __name__ == "__main__":
    main()
