"""
Tactic 6: Instruct the model to work out its own solution before rushing to a conclusion
策略六：先让模型自己推理，再对比结论

⭐ 这是第二集最重要的对比实验 ⭐

问题背景：
  一个太阳能装置的财务计算题，学生答案有误：
  - 土地费用：100x ✓
  - 太阳能板费用：250x ✓
  - 维护费用：学生写了 100,000 + 100x ✗（应该是 100,000 + 10x）
  - 学生总计：450x + 100,000 ✗（正确答案：360x + 100,000）

演示：
  A. 错误方式：让模型直接判断 → 模型会认同错误答案
  B. 正确方式：让模型先自己解题 → 模型发现错误
"""
from config import get_completion, print_section

QUESTION = """
I'm building a solar power installation and I need \
 help working out the financials.
- Land costs $100 / square foot
- I can buy solar panels for $250 / square foot
- I negotiated a contract for maintenance that will cost \
me a flat $100k per year, and an additional $10 / square \
foot
What is the total cost for the first year of operations
as a function of the number of square feet.
"""

STUDENT_SOLUTION = """
Let x be the size of the installation in square feet.
Costs:
1. Land cost: 100x
2. Solar panel cost: 250x
3. Maintenance cost: 100,000 + 100x
Total cost: 100x + 250x + 100,000 + 100x = 450x + 100,000
"""

# 注意：学生的维护费用写成了 100x（每平方英尺 $100），
# 实际上合同里是 $10/平方英尺，所以应该是 10x。
# 正确总计：100x + 250x + 10x + 100,000 = 360x + 100,000


def demo_wrong_approach():
    """错误方式：直接让模型评判，模型会被学生答案带偏。"""
    print_section("A. ❌ 错误方式：直接判断（模型会说'正确'）")

    prompt = f"""
Determine if the student's solution is correct or not.

Question:
{QUESTION}

Student's Solution:
{STUDENT_SOLUTION}
"""
    response = get_completion(prompt)
    print(f"[Response]\n{response}")
    print("\n⚠️  注意：模型认为学生答案正确，但学生其实算错了！")


def demo_correct_approach():
    """正确方式：强制模型先自己解题，再对比。"""
    print_section("B. ✅ 正确方式：先自行推理，再对比（模型发现错误）")

    prompt = f"""
Your task is to determine if the student's solution \
is correct or not.
To solve the problem do the following:
- First, work out your own solution to the problem including the final total.
- Then compare your solution to the student's solution \
and evaluate if the student's solution is correct or not.
Don't decide if the student's solution is correct until
you have done the problem yourself.

Use the following format:
Question:
```
question here
```
Student's solution:
```
student's solution here
```
Actual solution:
```
steps to work out the solution and your solution here
```
Is the student's solution the same as actual solution \
just calculated:
```
yes or no
```
Student grade:
```
correct or incorrect
```

Question:
```
{QUESTION}
```
Student's solution:
```
{STUDENT_SOLUTION}
```
Actual solution:
"""
    response = get_completion(prompt)
    print(f"[Response]\n{response}")
    print("\n✅ 模型先自行计算，得到 360x + 100,000，再发现学生答案有误。")


# ── 自由练习区 ───────────────────────────────────────────────────────────────
def your_turn():
    """
    TODO: 设计一个新的数学题，在学生答案里故意埋一个细微错误，
    验证"先自行推理"策略是否能稳定发现。

    提示：错误越隐蔽越好，比如符号错误、漏掉某项费用等。
    """
    print_section("C. 自由练习：自己出一道有误的题")

    MY_QUESTION = """
    一个停车场有 3 个区域：A 区 50 个车位，B 区 80 个车位，C 区 40 个车位。
    每个车位每天收费 $5。
    问：停车场满场运营 30 天的总收入是多少？
    """

    # 故意算错：用了 160 个车位（漏掉了 10 个）
    MY_STUDENT_SOLUTION = """
    总车位 = 50 + 80 + 40 = 160
    每天收入 = 160 × 5 = $800
    30 天总收入 = 800 × 30 = $24,000
    """
    # 正确答案：170 × 5 × 30 = $25,500

    prompt = f"""
Your task is to determine if the student's solution is correct or not.
First, work out your own solution. Then compare.

Question: {MY_QUESTION}
Student's solution: {MY_STUDENT_SOLUTION}
Actual solution:
"""
    response = get_completion(prompt)
    print(f"[Response]\n{response}")


if __name__ == "__main__":
    demo_wrong_approach()
    demo_correct_approach()
    # your_turn()
