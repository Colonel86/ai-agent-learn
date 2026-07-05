# Lesson 6: Evaluation - Finding and Fixing Bugs with NAT Eval

In previous lessons, you built, traced, and integrated agents. But how do you know if they actually work? Manual testing catches obvious errors, but subtle bugs hide in edge cases. A tool might work 80% of the time and fail silently the other 20%.

In this lesson, you'll create evaluation datasets with ground truth answers, run systematic tests, discover a hidden bug in your climate agent, fix it, and verify the improvement. This transforms agent development from manual testing into a data-driven engineering process.
<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 10px 0;">
<h4 style="margin-top: 0;">🎯 Learning Objectives</h4>
By the end of this lesson, you'll know how to:
<ul>
<li>Create evaluation datasets with ground truth answers</li>
<li>Run systematic tests to discover unexpected agent behaviors</li>
<li>Use evaluation results to identify and fix bugs</li>
<li>Verify improvements with before/after comparisons</li>
</ul>
</div>

## Setup


```python
import os
from dotenv import load_dotenv
load_dotenv()

# Verify it loaded
print("API key set:", "Yes" if os.getenv('NVIDIA_API_KEY') else "No")
```


```python
%%capture
# Install the climate analyzer package
!cd climate_analyzer && pip install -e . && cd ..
```

## Evaluation Dataset
An evaluation dataset consists of questions paired with ground truth answers. The agent's responses are compared against these known-correct answers to calculate accuracy.


```python
# run once to update the JSON file and view output
%load climate_analyzer/data/simple_eval.json
```

<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 Evaluation Dataset Structure</h4>
Each test case contains:
<ul>
<li><strong>user_input</strong> - The question to ask the agent</li>
<li><strong>reference</strong> - The ground truth answer (what the agent should return)</li>
<li><strong>metadata</strong> - Additional context (like expected tool calls)</li>
</ul>
<br>
<strong>Example:</strong>
<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 3px; margin: 10px 0;">
{
  "user_input": "What was Austria's average temperature in 1980?",
  "reference": "6.80°C"
}
</pre>
</div>

### Verify Ground Truth
Before evaluating your agent, verify your ground truth answers are actually correct. Otherwise, you're testing against wrong answers.


```python
!grep "^[^,]*,1980,[^,]*,Austria" ../resources/climate_data/temperature_annual.csv
```

<div style="background-color: #f5f5f5; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin: 15px 0; font-family: monospace;">
<strong>Raw Data for Austria 1980:</strong>
<pre style="margin: 10px 0; white-space: pre-wrap;">
Austria,1980,01,7.994166666666666
Austria,1980,02,7.631666666666667
Austria,1980,03,4.766666666666667
</pre>
</div>


```python
# Calculate the average to confirm our ground truth:
temps = [7.994166666666666, 7.631666666666667, 4.766666666666667]
average = sum(temps) / len(temps)
print(f"\nAverage temperature for Austria in 1980: {average:.2f}°C")
```

Add an eval section to your NAT config to define your test dataset and metrics:
<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">📋 Evaluation Configuration</h4>
<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 3px; margin: 10px 0;">
eval:
  eval_dataset_file_path: data/simple_eval.json  # Test questions + answers
  eval_name: simple_test                          # Name for this eval run
  eval_output_folder_path: .tmp/nat/climate_analyzer/eval  # Where to save results
  eval_metrics:
    - _type: answer_accuracy                      # Metric: compare answers
      model_name: meta/llama-3.1-70b-instruct    # LLM judges accuracy


```python
# Run once to update and view the entire config file
%load climate_analyzer/src/climate_analyzer/configs/eval_config.yml
```

## Run Evaluation

</pre>
</div>
<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 How Answer Accuracy Works</h4>
<ol>
<li>Your agent processes each test question</li>
<li>NAT captures the agent's response</li>
<li>An LLM judge compares the response to the reference answer</li>
<li>The judge assigns a score (0.0 = wrong, 1.0 = correct)</li>
<li>NAT calculates average score across all test cases</li>
</ol>
<br>
<strong>Why use an LLM judge?</strong> Exact string matching is too brittle. "6.80°C" and "6.8 degrees Celsius" are the same answer but different strings. An LLM can judge semantic equivalence.
</div>



```python
!cd climate_analyzer && nat eval --config_file src/climate_analyzer/configs/eval_config.yml
```

<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">🔄 What's Happening</h4>
<ol>
<li>NAT loads your test dataset</li>
<li>For each test case, it runs your agent with the question</li>
<li>Captures the agent's reasoning steps and final answer</li>
<li>Sends both the agent's answer and reference answer to the LLM judge</li>
<li>Collects scores and saves detailed results to JSON files</li>
</ol>
</div>

## Check Results

<div style="background-color: #f5f5f5; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin: 15px 0; font-family: monospace;">
<strong>Generated Files:</strong>
<pre style="margin: 10px 0; white-space: pre-wrap;">
answer_accuracy_output.json  ← Detailed results with scores
eval_summary.json           ← High-level metrics
</pre>
</div>

### Score Summary
Now you can open the results files and see how your agent performed: 


```python
import json

with open('climate_analyzer/.tmp/nat/climate_analyzer/eval/simple_test/answer_accuracy_output.json', 'r') as f:
    answer_accuracy_data = json.load(f)
```


```python
print(f"📊 Evaluation Results")
print(f"=" * 50)
print(f"Average Score: {answer_accuracy_data['average_score']} / 1.0")
print()

for item in answer_accuracy_data['eval_output_items']:
    r = item['reasoning']
    print(f"❓ {r['user_input']}")
    print(f"✅ Expected: {r['reference']}")
    print(f"❌ Got: {r['response']}")
    print(f"📈 Score: {item['score']}")
    print()
```

<div style="background-color: #ffebee; border-left: 6px solid #f44336; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">❌ Initial Results - Something's Wrong</h4>
<pre style="background-color: white; padding: 10px; border-radius: 3px; margin: 10px 0;">
📊 Evaluation Results
==================================================
Average Score: 0.0 / 1.0
❓ What was Austria's average temperature in 1980?
✅ Expected: 6.80°C
❌ Got: 8.08°C
📈 Score: 0.0
</pre>
<br>
<strong>The agent got the wrong answer!</strong> Let's investigate why.
</div>

### Inspect Agent Reasoning
Let's examine exactly what the agent did to understand where it went wrong. This code is just parsing the output JSON file. 


```python
# Extract the reasoning steps
item = answer_accuracy_data['eval_output_items'][0]
contexts = item['reasoning']['retrieved_contexts']

print("🤖 AGENT'S DECISION PROCESS")
print("=" * 60)
print(f"Question: {item['reasoning']['user_input']}")
print(f"Expected: {item['reasoning']['reference']}")
print("=" * 60)
print()

# Parse each step
for i, context in enumerate(contexts):
    if context.startswith('**Step'):
        # Extract step number and content
        lines = context.strip().split('\n')
        step_header = lines[0]
        
        print(f"{step_header}")
        
        # Look for Thought
        if 'Thought:' in context:
            thought_start = context.find('Thought:') + 8
            thought_end = context.find('\n\nAction:') if '\n\nAction:' in context else len(context)
            thought = context[thought_start:thought_end].strip()
            print(f"💭 Thought: {thought}")
        
        # Look for Action (tool call)
        if 'Action:' in context and 'Action Input:' in context:
            action_start = context.find('Action:') + 7
            action_end = context.find('\nAction Input:')
            action = context[action_start:action_end].strip()
            
            input_start = context.find('Action Input:') + 13
            input_end = context.find('\n\n', input_start) if '\n\n' in context[input_start:] else len(context)
            action_input = context[input_start:input_end].strip()
            
            print(f"🛠️  Tool: {action}")
            print(f"📥 Input: {action_input}")
        
        # Look for tool response (usually JSON)
        if i + 1 < len(contexts) and contexts[i + 1].startswith('{'):
            print(f"📤 Response: {contexts[i + 1][:100]}..." if len(contexts[i + 1]) > 100 else f"📤 Response: {contexts[i + 1]}")
        
        # Look for Final Answer
        if 'Final Answer:' in context:
            answer_start = context.find('Final Answer:') + 13
            final_answer = context[answer_start:].strip()
            print(f"✅ Final Answer: {final_answer}")
        
        print()

print("\n" + "=" * 60)
print(f"❌ Actual answer given: {item['reasoning']['response']}")
print(f"📊 Score: {item['score']}")
```

<div style="background-color: #f5f5f5; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin: 15px 0; font-family: monospace;">
<strong>Agent's Reasoning Trace:</strong>
<pre style="margin: 10px 0; white-space: pre-wrap;">
🤖 AGENT'S DECISION PROCESS
============================================================
Question: What was Austria's average temperature in 1980?
Expected: 6.80°C
============================================================
Step 1
💭 Thought: I need to get temperature data for Austria in 1980
🛠️  Tool: calculate_statistics
📥 Input: {"country": "Austria", "start_year": 1980, "end_year": 1980}
📤 Response: {"mean_temperature": 8.08, "years_analyzed": "1950-2025", ...}
✅ Final Answer: 8.08°C
============================================================
❌ Actual answer given: 8.08°C
📊 Score: 0.0
</pre>
</div>

Looking at Step 1, you can see that the agent passed the correct country, but failed to provide the year 1980. In the following steps, the agent tried to work around the incomplete input by calculating the average temperature for Austria across all the years it had data for, coming up with the wrong answer. 

The entire output can be found at `climate_analyzer/.tmp/nat/climate_analyzer/eval/simple_test/answer_accuracy_output.json`

## Bug Discovery!
<div style="background-color: #ffebee; border: 2px solid #f44336; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h3 style="color: #c62828; margin-top: 0;">🐛 Critical Bug Identified</h3>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
<h4 style="color: #f44336; margin-top: 0;">The Problem</h4>
<strong>The tool ignores year parameters!</strong>
<br><br>
<table style="width: 100%; border-collapse: collapse;">
    <tr style="background-color: #e8f5e9;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>✅ Agent Did Right</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Passed correct parameters: <code>country='Austria', start_year=1980, end_year=1980</code></td>
    </tr>
    <tr style="background-color: #ffebee;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>❌ Tool Did Wrong</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Returned data for ALL years (1950-2025), not just 1980</td>
    </tr>
    <tr style="background-color: #fff3cd;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>📊 Result</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Wrong answer: 8.08°C (average across 75 years) instead of 6.80°C (1980 only)</td>
    </tr>
</table>
</div>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #f44336; margin-top: 0;">Root Cause</h4>
The <code>calculate_statistics</code> function accepts <code>start_year</code> and <code>end_year</code> parameters but doesn't actually filter the data by them. The function signature has the parameters, but the implementation doesn't use them.
<br><br>
<strong>This is why systematic evaluation matters</strong> - manual testing might never catch this edge case, but automated evaluation found it immediately.
</div>
</div>

## The Fix
Add year filtering logic to the calculate_statistics function:
<div style="background-color: #e8f5e9; border-left: 6px solid #4CAF50; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">✅ The Solution</h4>
<strong>Before (broken code):</strong>
<pre style="background-color: white; padding: 10px; border-radius: 3px; margin: 10px 0;">
def calculate_statistics(df, country=None, start_year=None, end_year=None):
    # Filter by country
    if country:
        df = df[df['country_name'] == country] # BUG: Never filters by year!
    return calculate_stats(df)
</pre>
<strong>After (fixed code):</strong>
<pre style="background-color: white; padding: 10px; border-radius: 3px; margin: 10px 0;">
def calculate_statistics(df, country=None, start_year=None, end_year=None):
    # Filter by country
    if country:
        df = df[df['country_name'] == country]
        if start_year is not None: # ✅ FIX: Actually filter by year when specified
            df = df[df['year'] >= start_year]
        if end_year is not None:
            df = df[df['year'] <= end_year]
        return calculate_stats(df)
</pre>
</div>
<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 Why This Bug Existed</h4>
<ul>
<li><strong>Interface vs. Implementation</strong> - The function signature promised year filtering, but the body didn't deliver</li>
<li><strong>Silent failure</strong> - No error was thrown; the function just returned wrong data</li>
<li><strong>Hard to catch manually</strong> - "Show me Austria's temperature" works fine. Only specific year queries fail.</li>
<li><strong>Evaluation caught it</strong> - Systematic testing with ground truth revealed the bug immediately</li>
</ul>
</div>

## Test the Fix


```python
# Run evaluation with the fixed tool
!cd climate_analyzer && nat eval --config_file src/climate_analyzer/configs/eval_config_fixed.yml
```

## Verify Results
Now that the logic has been updated, check the results again to see if the score improved: 


```python
import json

with open('climate_analyzer/.tmp/nat/climate_analyzer/eval/fixed_test/answer_accuracy_output.json', 'r') as f:
    answer_accuracy_data = json.load(f)
```


```python
print(f"📊 Evaluation Results")
print(f"=" * 50)
print(f"Average Score: {answer_accuracy_data['average_score']} / 1.0")
print()

for item in answer_accuracy_data['eval_output_items']:
    r = item['reasoning']
    print(f"❓ {r['user_input']}")
    print(f"✅ Expected: {r['reference']}")
    print(f"❌ Got: {r['response']}")
    print(f"📈 Score: {item['score']}")
    print()
```

<div style="background-color: #e8f5e9; border-left: 6px solid #4CAF50; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">✅ Fixed Results - Success!</h4>
<pre style="background-color: white; padding: 10px; border-radius: 3px; margin: 10px 0;">
📊 Evaluation Results
==================================================
Average Score: 1.0 / 1.0
❓ What was Austria's average temperature in 1980?
✅ Expected: 6.80°C
✅ Got: 6.80°C
📈 Score: 1.0
</pre>
<br>
<strong>Perfect score!</strong> The agent now correctly filters by year and returns accurate results.
</div>

## Summary
<div style="background-color: #e3f2fd; border: 2px solid #2196F3; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h3 style="color: #1976d2; margin-top: 0;">🎉 What You Accomplished</h3>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #4CAF50; margin-top: 0;">✅ The Evaluation → Fix → Verify Loop</h4>
<div style="display: flex; justify-content: space-around; align-items: center; margin: 15px 0; flex-wrap: wrap;">
    <div style="text-align: center; margin: 10px;">
        <div style="background-color: #2196F3; color: white; padding: 12px; border-radius: 8px;">
            <strong>1. Create Tests</strong>
        </div>
        <small>Ground truth dataset</small>
    </div>
    <div style="font-size: 20px;">→</div>
    <div style="text-align: center; margin: 10px;">
        <div style="background-color: #ff9800; color: white; padding: 12px; border-radius: 8px;">
            <strong>2. Run Evaluation</strong>
        </div>
        <small>Found score: 0.0</small>
    </div>
    <div style="font-size: 20px;">→</div>
    <div style="text-align: center; margin: 10px;">
        <div style="background-color: #f44336; color: white; padding: 12px; border-radius: 8px;">
            <strong>3. Discover Bug</strong>
        </div>
        <small>Year filter missing</small>
    </div>
    <div style="font-size: 20px;">→</div>
    <div style="text-align: center; margin: 10px;">
        <div style="background-color: #9C27B0; color: white; padding: 12px; border-radius: 8px;">
            <strong>4. Fix Code</strong>
        </div>
        <small>Add year filtering</small>
    </div>
    <div style="font-size: 20px;">→</div>
    <div style="text-align: center; margin: 10px;">
        <div style="background-color: #4CAF50; color: white; padding: 12px; border-radius: 8px;">
            <strong>5. Verify Fix</strong>
        </div>
        <small>Score: 1.0 ✅</small>
    </div>
</div>
</div>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #2196F3; margin-top: 0;">📊 Before vs. After</h4>
<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    <tr style="background-color: #2196F3; color: white;">
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Metric</th>
        <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Before Fix</th>
        <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">After Fix</th>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Evaluation Score</strong></td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd; color: #f44336;"><strong>0.0 / 1.0</strong></td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd; color: #4CAF50;"><strong>1.0 / 1.0</strong></td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Answer for 1980</strong></td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd; color: #f44336;">8.08°C (wrong)</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd; color: #4CAF50;">6.80°C (correct)</td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Year Filtering</strong></td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd; color: #f44336;">❌ Broken</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd; color: #4CAF50;">✅ Working</td>
    </tr>
</table>
</div>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #9C27B0; margin-top: 0;">🔑 Key Insights</h4>
<ul>
<li><strong>Evaluation finds silent bugs</strong> - No errors thrown, just wrong answers</li>
<li><strong>Ground truth is essential</strong> - You need known-correct answers to test against</li>
<li><strong>Systematic beats manual</strong> - Automated evaluation catches edge cases you'd miss</li>
<li><strong>Reasoning traces debug bugs</strong> - Seeing what the agent tried helps identify where it went wrong</li>
<li><strong>Verify fixes work</strong> - Re-run evaluation to confirm the bug is actually fixed</li>
</ul>
</div>
<div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="margin-top: 0;">⚡ Why This Matters in Production</h4>
Without systematic evaluation:
<ul>
<li>This bug would have made it to production</li>
<li>Users asking about specific years would get wrong answers</li>
<li>You'd only discover it through user complaints</li>
<li>You wouldn't know how widespread the problem is</li>
</ul>
<br>
With evaluation:
<ul>
<li>Caught the bug before deployment</li>
<li>Fixed it with confidence (verified the fix works)</li>
<li>Can now test regression (make sure future changes don't break it again)</li>
<li>Have metrics to track improvements over time</li>
</ul>
</div>
<div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="margin-top: 0;">🚀 Next Lesson: Deploy with UI</h4>
Your agent is now:
<ul>
<li>✅ Functional (has data analysis tools)</li>
<li>✅ Observable (Phoenix tracing shows decisions)</li>
<li>✅ Enhanced (LangGraph calculator for complex math)</li>
<li>✅ Tested (evaluation ensures correctness)</li>
</ul>
<br>
In the final lesson, you'll:
<ul>
<li>Deploy your agent with a production-ready UI</li>
<li>Add authentication and rate limiting</li>
<li>See how everything comes together in a real application</li>
<li>Share your agent with users</li>
</ul>
</div>
</div>
