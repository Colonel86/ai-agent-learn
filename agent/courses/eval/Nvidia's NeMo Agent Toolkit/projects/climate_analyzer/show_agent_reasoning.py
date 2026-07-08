# 查看评测中 agent 的推理步骤(课程 L6 的第二段验证代码,适配 NAT 1.8)
# 用法:在项目根目录跑  python show_agent_reasoning.py
#
# 课程版解析 retrieved_contexts 里的 '**Step N' 文本块;NAT 1.8 的 react_agent
# 不再发出 LLM_END 事件(与 L4 中 Phoenix 缺 token 是同一个上游回归),
# 所以 retrieved_contexts / intermediate_steps 均为空。本脚本:有数据就按课程
# 方式解析;没有就明确告知,并指到 Phoenix(eval_config.yml 已挂 telemetry)。
import json

with open(".tmp/eval_output/answer_accuracy_output.json") as f:
    data = json.load(f)

item = data["eval_output_items"][0]
r = item["reasoning"]

print("🤖 AGENT'S DECISION PROCESS")
print("=" * 60)
print(f"Question: {r['user_input']}")
print(f"Expected: {r['reference']}")
print("=" * 60)

contexts = r.get("retrieved_contexts") or []

# 兜底再看 workflow_output.json 里的 intermediate_steps
if not contexts:
    try:
        wf = json.load(open(".tmp/eval_output/workflow_output.json"))
        steps = (wf[0] if isinstance(wf, list) else wf).get("intermediate_steps") or []
        contexts = [json.dumps(s, ensure_ascii=False) for s in steps]
    except FileNotFoundError:
        pass

if contexts:
    for i, context in enumerate(contexts):
        context = str(context)
        if context.startswith("**Step"):
            print(context.strip().split("\n")[0])
            if "Thought:" in context:
                t = context[context.find("Thought:") + 8:]
                t = t[:t.find("\n\nAction:")] if "\n\nAction:" in t else t
                print(f"💭 Thought: {t.strip()}")
            if "Action:" in context and "Action Input:" in context:
                a = context[context.find("Action:") + 7:context.find("\nAction Input:")]
                ai = context[context.find("Action Input:") + 13:]
                print(f"🛠️  Tool: {a.strip()}")
                print(f"📥 Input: {ai.strip()[:100]}")
            if "Final Answer:" in context:
                print(f"✅ Final Answer: {context[context.find('Final Answer:') + 13:].strip()}")
            # 没有 Thought/Action 的步骤是工具返回(TOOL_END),正文通常是 JSON
            body = context.split("\n", 1)[1].strip() if "\n" in context else ""
            if body and "Thought:" not in context:
                print(f"📤 Response: {body[:200]}")
            print()
        else:
            print(f"[{i}] {context[:160]}")
else:
    print()
    print("(NAT 1.8 的评测输出不含推理步骤——react_agent 不发 LLM_END 事件,")
    print(" 与 Phoenix 缺 token 统计同源。推理过程请到 Phoenix 查看:")
    print(" http://localhost:6006 → climate_analyzer_eval 项目,")
    print(" 每条评测问题一条 trace,可钻取每次工具调用的入参/出参。)")

print("\n" + "=" * 60)
print(f"实际回答: {r['response']}")
print(f"📊 Score: {item['score']}")
