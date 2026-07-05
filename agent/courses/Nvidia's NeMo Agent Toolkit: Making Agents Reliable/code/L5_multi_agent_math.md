# Lesson 5: Multi-Agent Integration Adding Math

In the previous lessons, you built a climate analysis agent with multiple tools. But what if you need capabilities that already exist in other frameworks? What if someone on your team built a specialized agent in LangGraph or CrewAI, and you want to use it without rewriting everything?

In this lesson, you'll learn how to integrate agents built with other frameworks into NAT and you'll add a LangGraph calculator agent to handle complex mathematical operations that your climate agent currently can't perform. Since NAT is framework-agnostic, you can use agents from different frameworks in a single config.<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 10px 0;">
<h4 style="margin-top: 0;">🎯 Learning Objectives</h4>
By the end of this lesson, you'll know how to:
<ul>
<li>Integrate a LangGraph agent as a NAT tool</li>
<li>Apply the "LLM Lifting" pattern to share LLM configs across frameworks</li>
<li>Compose multi-agent systems from different frameworks</li>
<li>Coordinate specialized agents for complex tasks</li>
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

Your climate agent can load data, calculate statistics, and create visualizations. But it struggles with complex multi-step mathematical operations.<div style="background-color: #ffebee; border-left: 6px solid #f44336; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">❌ Questions We Can't Answer Yet</h4><div style="background-color: white; padding: 12px; margin: 10px 0; border-radius: 5px;">
<strong>Question 1: Compound Annual Growth Rate (CAGR)</strong><br>
"If temperature rose from 14.2°C to 15.8°C over 43 years, what's the CAGR?"
<br><br>
<strong>Why it fails:</strong> Requires compound growth calculation formula
</div><div style="background-color: white; padding: 12px; margin: 10px 0; border-radius: 5px;">
<strong>Question 2: Population-Weighted Average</strong><br>
"Three countries: warming rates 0.15, 0.22, 0.18°C/decade; populations 320M, 1.4B, 125M. What's the population-weighted average?"
<br><br>
<strong>Why it fails:</strong> Multi-step calculation with weighted averages
</div><div style="background-color: white; padding: 12px; margin: 10px 0; border-radius: 5px;">
<strong>Question 3: Exponential Projection</strong><br>
"Renewable capacity: 800 GW → 3,100 GW in 12 years. When will we hit 10,000 GW?"
<br><br>
<strong>Why it fails:</strong> Exponential growth projection with solving for time
</div>
</div>
<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">⚠️ Why Current Tools Can't Handle This</h4>
<ul>
<li><strong>LLMs aren't calculators</strong> - They approximate math but make errors on complex calculations</li>
<li><strong>No calculator tool</strong> - Your agent has data analysis tools, not general-purpose math</li>
<li><strong>Multi-step reasoning required</strong> - Complex problems need to be broken down into sub-problems</li>
</ul>

## Solution: LangGraph Calculator Agent
We'll used a pre-built, battle-tested calculator instead of building one from scratch, and use LangGraph to integrate it. 


```python
# Import and visualize the calculator agent structure
import sys
sys.path.append('calculator_agent')
```


```python
import calculator_agent
print(calculator_agent.__doc__)
```

<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 What the Calculator Agent Does</h4>
<ul>
<li><strong>Multi-step reasoning</strong> - Breaks complex problems into steps</li>
<li><strong>Python code execution</strong> - Generates and runs code for calculations</li>
<li><strong>Error handling</strong> - Retries if calculations fail</li>
<li><strong>Explanation generation</strong> - Shows work for transparency</li>
</ul>
This is a complete LangGraph agent with its own reasoning loop, tools, and error handling. The full source code is located at: calculator_agent/calculator_agent.py
</div>

### Test Complex Calculation
Let's test the calculator agent in isolation before integrating it:


```python
# Test a complex multi-step problem
complex_question = """\
A country's emissions were 1,200 Mt in 2015. They reduced emissions by 2.5% annually until 2020, \
then accelerated reductions to 4% annually. What are the emissions in 2025?"""
```


```python
from calculator_agent import calculate
result = calculate(complex_question)
print(f"\nFinal Answer: {result['explanation']}")
```

<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">📐 Why This is Hard</h4>
<ol>
<li>Calculate emissions for 2015-2020 (5 years at 2.5% reduction)</li>
<li>Use that result as the starting point for 2020-2025</li>
<li>Calculate emissions for 2020-2025 (5 years at 4% reduction)</li>
<li>Apply compound reduction formula correctly</li>
</ol>
This requires precise multi-step calculation that LLMs typically can't do reliably.
</div>

<div style="background-color: #f5f5f5; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin: 15px 0; font-family: monospace;">
<strong>Expected Output:</strong>
<pre style="margin: 10px 0; white-space: pre-wrap;">
Step 1: Calculate emissions in 2020
2015 * (1 - 0.025)^5 = 1120.91 Mt
Step 2: Calculate emissions in 2025
1120.91 * (1 - 0.04)^5 = 1043.51 Mt
Final Answer: The country's emissions in 2025 are approximately 1043.51 Mt CO2e
</pre>
</div>
<div style="background-color: #e8f5e9; border-left: 6px solid #4CAF50; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">✅ Calculator Agent Success</h4>
The LangGraph agent:
<ul>
<li>Broke the problem into logical steps</li>
<li>Applied the correct compound reduction formula</li>
<li>Generated Python code to compute the result</li>
<li>Showed all work for verification</li>
</ul>
Now let's integrate this capability into your climate analyzer.
</div>

## See Current Workflow Fail
First, let's demonstrate that your current climate agent can't handle this type of question:


```python
# Variant of complex question above using a specific country from our data
complex_nat_question = """\
Get the temperature statistics for India and find its trend per decade. If India's temperature \
continues to increase at this rate, what will the temperature be in 2050?"""
```

<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">📊 What This Question Requires</h4>
<ol>
<li><strong>Data retrieval</strong> - Get India's temperature statistics (agent can do this)</li>
<li><strong>Identify trend</strong> - Extract trend_per_decade value (agent can do this)</li>
<li><strong>Project forward</strong> - Calculate temperature in 2050 using the trend (agent CAN'T do this reliably)</li>
</ol>
This is a perfect test case: the agent has the tools to get the data, but lacks the math capabilities.
</div>


```python
!cd climate_analyzer && nat run --config_file src/climate_analyzer/configs/config.yml --input "$complex_nat_question"
```

<div style="background-color: #ffebee; border-left: 6px solid #f44336; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">❌ What Happens</h4>
<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd; width: 40px; text-align: center;">✅</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Retrieves temperature data correctly</strong> - Uses calculate_statistics tool</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 12px; border: 1px solid #ddd; width: 40px; text-align: center;">✅</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Identifies values needed</strong> - Knows it needs the trend rate</td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd; width: 40px; text-align: center;">❌</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Can't do the projection math</strong> - No tool for complex calculations</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 12px; border: 1px solid #ddd; width: 40px; text-align: center;">❌</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>May hallucinate the answer</strong> - LLM approximates the math incorrectly</td>
    </tr>
</table>
<br>
<strong>The gap:</strong> Your agent needs a calculator tool to bridge data analysis and mathematical projection.
</div>

## Integration Pattern: LLM Lifting

The key to integrating external agents is the LLM Lifting pattern. Instead of hardcoding the LLM inside the calculator agent, you "lift" it to NAT's config. This lets you:

- Use the same LLM config across all agents
- Change models without touching code
- Let NAT handle LLM initialization and management

<div style="background-color: #f9f9f9; border: 2px solid #ddd; padding: 20px; border-radius: 8px; margin: 20px auto; max-width: 700px; text-align: center;">
<h4 style="margin-bottom: 30px;">LLM Lifting Pattern</h4>
<div style="display: inline-flex; align-items: center; gap: 30px; flex-wrap: wrap;">
    <div>
        <div style="background-color: #f44336; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; width: 180px;">
            <strong>❌ Without Lifting</strong>
        </div>
        <div style="font-size: 14px;">LLM hardcoded in agent</div>
        <div style="font-size: 12px; color: #666;">Changes require code edits</div>
    </div>
    <div style="font-size: 24px;">→</div>
    <div>
        <div style="background-color: #4CAF50; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; width: 180px;">
            <strong>✅ With Lifting</strong>
        </div>
        <div style="font-size: 14px;">LLM from NAT config</div>
        <div style="font-size: 12px; color: #666;">Changes via YAML only</div>
    </div>
</div>
</div>

### Register the LangGraph Agent
Here's how you register the calculator agent with LLM lifting (**you don't need to run this cell**):

```python
# Import the necessary framework enum for LangChain/LangGraph
from nat.builder.framework_enum import LLMFrameworkEnum

# Register the calculator agent with NAT, specifying it requires LangChain framework for LLM interactions
@register_function(config_type=CalculatorAgentConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def calculator_agent_tool(config: CalculatorAgentConfig, builder: Builder):
    """Register the LangGraph calculator agent as a NAT tool."""
    
    # Get the LLM from NAT's builder (the config file)
    # The "calculator_llm" refers to the LLM defined in config.yml
    llm = await builder.get_llm("calculator_llm", wrapper_type=LLMFrameworkEnum.LANGCHAIN)
    
    calculator_agent = create_calculator_agent(llm)
    
    async def _wrapper(question: str) -> str:
        result = calculate_with_agent(question, calculator_agent)
        
        response = {
            "calculation_steps": result["steps"],
            "final_result": result["final_result"],
            "explanation": result["explanation"]
        }
        return json.dumps(response, indent=2)
    
    yield FunctionInfo.from_fn(
        _wrapper,
        input_schema=CalculatorInput,
        description=(
            "Calculates compound growth rates, percentage changes, weighted averages, "
            "projections, and multi-step calculations. Shows all calculation steps. "
            "Does not have access to climate data. If calculations need to be performed on climate data, "
            "be sure to acquire that data with other tools before including it in the input question to this tool."
        )
    )
```

<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 Key Registration Components</h4>
<ol>
<li><strong>framework_wrappers=[LANGCHAIN]</strong> - Tells NAT this tool needs LangChain-compatible LLMs</li>
<li><strong>await builder.get_llm("calculator_llm", ...)</strong> - Gets the LLM from NAT's config, not hardcoded</li>
<li><strong>create_calculator_agent(llm)</strong> - Initializes the LangGraph agent with NAT's LLM</li>
<li><strong>FunctionInfo description</strong> - Critical: tells the main agent when to use this tool and what data it needs</li>
</ol>
</div>
<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">🎯 Why the Description Matters</h4>
The description tells your climate agent:
<ul>
<li><strong>"Does not have access to climate data"</strong> - So it knows to get the data first</li>
<li><strong>"Shows all calculation steps"</strong> - Helps agent trust the results</li>
<li><strong>What it can calculate</strong> - Growth rates, projections, weighted averages, etc.</li>
</ul>
Without this description, your agent won't know when to use the calculator or what data to provide.
</div>

<!-- #endregion -->


### Configure Two LLMs
Now your config has been updated to define both LLMs and register the calculator agent:

```yaml
llms:
  # Existing climate LLM for general analysis
  climate_llm:
    _type: nim
    model_name: meta/llama-3.1-70b-instruct
    base_url: https://integrate.api.nvidia.com/v1
    api_key: $NVIDIA_API_KEY
    temperature: 0.0
    top_p: 0.95
    max_tokens: 2048
  
  # New: Dedicated LLM for the calculator agent
  calculator_llm:
    _type: nim
    model_name: meta/llama-3.1-70b-instruct
    base_url: https://integrate.api.nvidia.com/v1
    api_key: $NVIDIA_API_KEY
    temperature: 0.0  # Low temperature for consistent math
    max_tokens: 1024  # Sufficient for calculations

functions:
  # ... existing functions ...
  
  # New: Register the calculator agent as a function
  calculator_agent:
    _type: climate_analyzer/calculator_agent
    description: "Perform complex mathematical calculations for climate data analysis"

workflow:
  _type: react_agent
  tool_names:
    - list_countries
    - calculate_statistics
    - filter_by_country
    - find_extreme_years
    - create_visualization
    - station_statistics
    - calculator_agent  # Add to available tools
  llm_name: climate_llm
  verbose: true
  max_iterations: 5
  parse_agent_response_max_retries: 2
  max_tool_calls: 30
```


### Integration Pattern Summary:
<div style="background-color: #e3f2fd; border: 2px solid #2196F3; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h4 style="color: #1976d2; margin-top: 0;">🔑 Three Key Integration Patterns</h4>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #4CAF50; margin-top: 0;">1. LLM Lifting</h4>
<strong>Instead of:</strong> Hardcoding LLM in the agent code<br>
<strong>Do:</strong> Get LLM from NAT's builder via <code>await builder.get_llm("calculator_llm")</code><br>
<strong>Benefit:</strong> Change models via config, not code
</div>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #2196F3; margin-top: 0;">2. Framework Wrapper</h4>
<strong>What:</strong> <code>framework_wrappers=[LLMFrameworkEnum.LANGCHAIN]</code><br>
<strong>Why:</strong> Tells NAT this tool needs LangChain-compatible LLM objects<br>
<strong>Benefit:</strong> NAT handles framework compatibility automatically
</div>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #9C27B0; margin-top: 0;">3. Standard Tool Registration</h4>
<strong>Key insight:</strong> To NAT, external agents are just another tool<br>
<strong>Registration:</strong> Same FunctionInfo pattern as regular tools<br>
<strong>Benefit:</strong> Consistent integration regardless of framework
</div>
</div>

### Test Enhanced Workflow
Now run the same question that failed before:


```python
!cd climate_analyzer && nat run --config_file src/climate_analyzer/configs/config_calculator.yml --input "$complex_nat_question"
```

<div style="background-color: #e8f5e9; border-left: 6px solid #4CAF50; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">✅ What Happens Now</h4>
<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd; width: 40px; text-align: center;">1</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Agent calls calculate_statistics</strong> - Gets India's temperature data and trend</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 12px; border: 1px solid #ddd; width: 40px; text-align: center;">2</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Agent formulates math question</strong> - "If temperature increases at X°C/decade, what will it be in 2050?"</td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd; width: 40px; text-align: center;">3</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Agent calls calculator_agent</strong> - Passes the question with extracted data</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 12px; border: 1px solid #ddd; width: 40px; text-align: center;">4</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Calculator performs calculation</strong> - Breaks down the projection math</td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd; width: 40px; text-align: center;">5</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Agent synthesizes answer</strong> - Combines data context with calculation result</td>
    </tr>
</table>
</div>
<div style="background-color: #f5f5f5; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin: 15px 0; font-family: monospace;">
<strong>Expected Output:</strong>
<pre style="margin: 10px 0; white-space: pre-wrap;">
Based on India's climate data:
- Current mean temperature: 25.3°C
- Warming trend: 0.18°C per decade
- Years from now to 2050: 25 years (2.5 decades)
- Projected temperature increase: 0.18 × 2.5 = 0.45°C
- Projected temperature in 2050: 25.3 + 0.45 = 25.75°C
India's temperature is projected to reach approximately 25.75°C by 2050 if current warming trends continue.
</pre>
</div>

## Clean Up


```python
!pip uninstall climate_analyzer -y
```

## Summary
<div style="background-color: #e3f2fd; border: 2px solid #2196F3; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h3 style="color: #1976d2; margin-top: 0;">🎉 What You Accomplished</h3>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #4CAF50; margin-top: 0;">✅ Integration Success</h4>
You integrated a LangGraph calculator agent with minimal changes:
<ul>
<li><strong>No code rewrite</strong> - Used existing LangGraph agent as-is</li>
<li><strong>LLM config lifted</strong> - Moved from hardcoded to NAT's config</li>
<li><strong>Standard registration</strong> - Same pattern as regular tools</li>
<li><strong>New capability</strong> - Can now handle complex mathematical projections</li>
</ul>
</div>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #2196F3; margin-top: 0;">🔧 What Changed</h4>
<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    <tr style="background-color: #2196F3; color: white;">
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Component</th>
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Change</th>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Config</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Added calculator_llm, registered calculator_agent function</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Registration</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Added @register_function with LANGCHAIN wrapper</td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Agent Code</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Zero changes—reused existing LangGraph agent</td>
    </tr>
</table>
</div>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #9C27B0; margin-top: 0;">🌟 Key Insights</h4>
<ul>
<li><strong>Framework-agnostic</strong> - NAT orchestrates agents from any framework (LangGraph, CrewAI, custom)</li>
<li><strong>Reuse existing work</strong> - Don't rebuild specialized agents, integrate them</li>
<li><strong>Config-driven flexibility</strong> - Change models, frameworks, or agents without code changes</li>
<li><strong>Separation of concerns</strong> - Climate analysis agent doesn't need to know math, just how to delegate</li>
</ul>
</div>
<div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="margin-top: 0;">🚀 Next Lesson: Evaluation and Testing</h4>
Now that your agent has more capabilities, you need to ensure it works correctly. In the next lesson, you'll:
<ul>
<li>Create evaluation datasets to test agent behavior</li>
<li>Measure accuracy, tool usage, and response quality</li>
<li>Find and fix bugs systematically</li>
<li>Track improvements over time</li>
</ul>
Evaluation turns agent development from guesswork into a data-driven process.
</div>
</div>
