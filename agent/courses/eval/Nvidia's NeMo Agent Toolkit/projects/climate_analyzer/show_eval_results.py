# 读取 nat eval 的输出并打印结果(课程 L6 的验证代码,适配本地路径与字段)
# 用法:在项目根目录跑  python show_eval_results.py
import json

# 课程路径是 .tmp/nat/climate_analyzer/eval/simple_test/;
# 我们的 eval_config.yml 里 output_dir 是 ./.tmp/eval_output
with open(".tmp/eval_output/answer_accuracy_output.json") as f:
    answer_accuracy_data = json.load(f)

print("📊 Evaluation Results")
print("=" * 50)
print(f"Average Score: {answer_accuracy_data['average_score']} / 1.0")
print()

for item in answer_accuracy_data["eval_output_items"]:
    r = item["reasoning"]
    print(f"❓ {r['user_input']}")
    print(f"✅ Expected: {r['reference']}")
    print(f"🤖 Got: {r['response']}")
    print(f"📈 Score: {item['score']}")
    print()
