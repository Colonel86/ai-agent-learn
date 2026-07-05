# Lesson 4: Observability with Phoenix Tracing

In Lesson 3, you built a ReAct agent with multiple tools that can analyze climate data. But when your agent makes mistakes or takes too long to respond, you weren't able to see why. Without observability, you don't know which tools your agent considered, what data it processed, or where it got stuck.

In this lesson, you'll add observability to your agent using OpenTelemetry tracing through the Phoenix web UI. Phoenix captures every step of your agent's reasoning process—which tools it calls, what data flows between them, and how long each operation takes. This visibility lets you identify problems and make data-driven improvements.
<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 10px 0;">
<h4 style="margin-top: 0;">🎯 Learning Objectives</h4>
By the end of this lesson, you'll know how to:
<ul>
<li>Set up Phoenix for real-time tracing of your NAT workflows</li>
<li>Use trace data to identify performance bottlenecks and inefficiencies</li>
<li>Make data-driven improvements based on observed agent behavior</li>
<li>Compare agent performance before and after optimizations</li>
</ul>
</div>


```python
from dotenv import load_dotenv
import os
load_dotenv()

# Verify it loaded
print("API key set:", "Yes" if os.getenv('NVIDIA_API_KEY') else "No")
```


```python
# uncomment to install in your own environment
# !pip install "nvidia-nat[phoenix]"
```

## Start Phoenix

Phoenix is an open-source observability platform that captures and visualizes traces from your agent. It runs as a local web server that collects trace data and provides an interactive UI for analysis.
<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">🚀 Production vs. Notebook Setup</h4>
<strong>In production,</strong> you'd simply run in a terminal:
<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 3px; margin: 10px 0;">
phoenix serve
</pre>
<strong>In Jupyter,</strong> you'll use <code>subprocess</code> to start Phoenix in the background.
</div>


```python
import subprocess
import time
import sys

# Start Phoenix 
phoenix_process = subprocess.Popen(
    ["phoenix", "serve"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Read initial output
print("Starting Phoenix...")
start_time = time.time()
while time.time() - start_time < 3:
    line = phoenix_process.stdout.readline()
    if line:
        print(line.strip())

print("\n✅ Phoenix is running silently in the background!")
```

<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 What Phoenix Does</h4>
<ul>
<li><strong>Captures traces</strong> - Every agent decision, tool call, and LLM interaction</li>
<li><strong>Stores telemetry</strong> - Timing data, token usage, success/failure status</li>
<li><strong>Provides visualization</strong> - Interactive UI to explore traces and find patterns</li>
<li><strong>Runs locally</strong> - Your data never leaves your machine (default port: 6006)</li>
</ul>
</div>

## Access Phoenix UI
The following codeblock is just some quick html to get the URL for your Phoenix server: 


```python
from IPython.display import HTML, display

html = """
<div style="padding: 15px; background-color: #e8f4f8; border-radius: 8px; margin: 10px 0;">
    <h4 style="margin: 0 0 10px 0;">🔍 Phoenix Observability Dashboard</h4>
    <p>Click the button to open Phoenix (it will auto-detect the correct URL):</p>
    <button onclick="
        var url = window.location.origin.replace(/p\\d+/, 'p6006');
        window.open(url, '_blank');
    " style="padding: 10px 20px; background-color: #0066cc; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px;">
        🚀 Open Phoenix UI
    </button>
    <p style="margin-top: 10px; font-size: 12px; color: #666;">
        If the link doesn't work, manually replace the port in your browser URL from p8888 to p6006
    </p>
</div>
"""

display(HTML(html))
```

<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">🖥️ What You'll See in Phoenix</h4>
The Phoenix UI shows:
<ul>
<li><strong>Traces list</strong> - Every agent execution, sorted by time</li>
<li><strong>Trace timeline</strong> - Visual representation of tool calls and duration</li>
<li><strong>Span details</strong> - Inputs, outputs, and metadata for each operation</li>
<li><strong>Performance metrics</strong> - Token usage, latency, error rates</li>
</ul>
<strong>Keep this tab open—you'll use it to analyze your agent's behavior.</strong>
</div>

## Setup Climate Analyzer


```python
%%capture
# Install the package so it's ready for all subsequent cells
!cd climate_analyzer && pip install -e . && cd ..
```

## Phoenix Configuration
To enable Phoenix tracing, you add a `telemetry section` to your NAT config. This tells NAT where to send trace data.
<div style="background-color: #f9f9f9; border: 2px solid #ddd; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h4 style="text-align: center;">Phoenix Configuration Structure</h4>
<pre style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 10px 0;">
general:                                              # Global workflow settings
  telemetry:                                          # Monitoring and metrics
    tracing:                                          # Distributed tracing config
      phoenix:                                        # Phoenix-specific settings
        _type: phoenix                                # Use Phoenix provider
        endpoint: http://localhost:6006/v1/traces     # Where to send data
        project: climate_analyzer_baseline            # Project name in UI
</pre>
</div>
<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 Key Configuration Fields</h4>
<ul>
<li><strong>endpoint</strong> - Phoenix trace collector URL (must match where Phoenix is running)</li>
<li><strong>project</strong> - Groups traces together in the UI. Use different names to compare versions (e.g., "baseline" vs. "optimized")</li>
<li><strong>_type: phoenix</strong> - NAT supports multiple tracing backends; this specifies Phoenix</li>
</ul>
</div>
Run the code below once- the updated YAML file will display below after the telemetry section has been added. 


```python
%load climate_analyzer/src/climate_analyzer/configs/config.yml
```

## Run Test Queries
Now run some queries with tracing enabled. These queries are designed to expose different behaviors—some will work well, others will reveal inefficiencies.


```python
queries = [
    "What is the warming rate for Canada?",
    "What is the second coldest year in the dataset?",
    "Which country has the most weather stations in our data?"
]
```

<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">🧪 Test Query Design</h4>
<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    <tr style="background-color: #ffc107; color: black;">
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Query</th>
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">What It Tests</th>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 10px; border: 1px solid #ddd;">Canada warming rate</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Country-specific statistics (should work well)</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 10px; border: 1px solid #ddd;">Second coldest year</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Extreme value queries (should work well)</td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 10px; border: 1px solid #ddd;">Most weather stations</td>
        <td style="padding: 10px; border: 1px solid #ddd;">Station metadata (might struggle—no dedicated tool)</td>
    </tr>
</table>
</div>


```python
# run each query in the list 
for query in queries:
    print(f"\nRunning: {query}")
    !nat run --config_file climate_analyzer/src/climate_analyzer/configs/config.yml --input "$query"
    print("-" * 60)
```

<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">📊 Refresh Phoenix and Watch For</h4>
As these run, Phoenix captures:
<ul>
<li>Which tools the agent calls</li>
<li>How many attempts it makes</li>
<li>How long each operation takes</li>
<li>Whether it gets the right answer</li>
</ul>
</div>

## What Phoenix Shows

<div style="background-color: #ffebee; border-left: 6px solid #f44336; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">🔍 Problem Identified: Station Query Inefficiency</h4>
<p>In Phoenix, you'll notice the third query ("Which country has the most weather stations?") behaves differently:</p>
<ul>
<li><strong>Multiple tool calls</strong> - Agent tries several tools to find station data</li>
<li><strong>Longer execution time</strong> - Wasted time calling irrelevant tools</li>
<li><strong>Unclear reasoning</strong> - Agent isn't sure which tool has station info</li>
</ul>
<br>
<strong>Root cause:</strong> No dedicated tool for station statistics. The agent has to improvise, calling <code>filter_by_country</code> multiple times or trying
<code>calculate_statistics</code> hoping it returns station counts.
</div>

<div style="background-color: #f9f9f9; border: 2px solid #ddd; padding: 20px; border-radius: 8px; margin: 20px auto; max-width: 700px;">
<h4 style="text-align: center; margin-bottom: 20px;">Before Optimization: Station Query Behavior</h4>
<div style="display: flex; justify-content: center; align-items: center; gap: 15px; flex-wrap: wrap;">
    <div style="text-align: center;">
        <div style="background-color: #f44336; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; width: 150px;">
            <strong>5-7 Tool Calls</strong>
        </div>
        <small>Agent tries multiple tools</small>
    </div>
    <div style="font-size: 24px;">→</div>
    <div style="text-align: center;">
        <div style="background-color: #ff9800; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; width: 150px;">
            <strong>3-5 Seconds</strong>
        </div>
        <small>Wasted time searching</small>
    </div>
    <div style="font-size: 24px;">→</div>
    <div style="text-align: center;">
        <div style="background-color: #f44336; color: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; width: 150px;">
            <strong>Sometimes Wrong</strong>
        </div>
        <small>Inconsistent answers</small>
    </div>
</div>
</div>

<div style="background-color: #e8f5e9; border-left: 6px solid #4CAF50; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 The Fix: Add a Dedicated Station Tool</h4>
Instead of letting the agent guess which tool has station data, give it a tool specifically designed for this purpose. This is a data-driven decision based on what you observed in Phoenix.
</div>

## Fix: Add Station Tool
Update your config to include a new `station_statistics` tool by running the following line of code: 


```python
%load climate_analyzer/src/climate_analyzer/configs/config_updated.yml
```

```yaml
functions:
  # New tool to address observed churn
  station_statistics:
    _type: climate_analyzer/station_statistics
    description: "Get statistics on climate stations used in the data"

workflow:
  _type: react_agent
  tool_names:
    - list_countries
    - calculate_statistics
    - filter_by_country
    - find_extreme_years
    - create_visualization
    # Our new tool
    - station_statistics
```
<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 What This Tool Does</h4>
<code>station_statistics</code> returns:
<ul>
<li><strong>total_stations</strong> - Count across all countries</li>
<li><strong>countries_with_most_stations</strong> - Top 5 countries ranked by station count</li>
<li><strong>stations_per_country</strong> - Complete breakdown</li>
</ul>
This gives the agent a direct path to answer station-related questions.
</div>


### Test the Fix
Now run the same queries with the updated config:


```python
for query in queries:
    print(f"\nRunning: {query}")
    !nat run --config_file climate_analyzer/src/climate_analyzer/configs/config_updated.yml --input "$query"
    print("-" * 60)
```

## See the Improvement
Refresh Phoenix to check it again - Look at the new traces in the climate_analyzer_optimized project.
<div style="background-color: #e8f5e9; border-left: 6px solid #4CAF50; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">✅ After Optimization: Station Query Behavior</h4>
<p>Phoenix now shows a much cleaner pattern:</p>
<ul>
<li><strong>Direct answers</strong> - Agent calls <code>station_statistics</code> immediately</li>
<li><strong>Fewer tool calls</strong> - 1-2 calls instead of 5-7</li>
<li><strong>Faster response</strong> - Executes in under 2 seconds</li>
<li><strong>Consistent accuracy</strong> - Correct answer every time</li>
</ul>
</div>

<div style="background-color: #f9f9f9; border: 2px solid #ddd; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h4 style="text-align: center; margin-bottom: 20px;">After Optimization: Station Query Behavior</h4>
<div style="display: flex; justify-content: center; align-items: center; gap: 10px; margin: 0 auto; max-width: 600px;">
    <div style="text-align: center;">
        <div style="background-color: #4CAF50; color: white; padding: 15px; border-radius: 8px; margin-bottom: 8px; width: 140px;">
            <strong>1-2 Tool Calls</strong>
        </div>
        <small>Direct to station_statistics</small>
    </div>
    <span style="font-size: 24px;">→</span>
    <div style="text-align: center;">
        <div style="background-color: #4CAF50; color: white; padding: 15px; border-radius: 8px; margin-bottom: 8px; width: 140px;">
            <strong>&lt;2 Seconds</strong>
        </div>
        <small>Fast, efficient execution</small>
    </div>
    <span style="font-size: 24px;">→</span>
    <div style="text-align: center;">
        <div style="background-color: #4CAF50; color: white; padding: 15px; border-radius: 8px; margin-bottom: 8px; width: 140px;">
            <strong>Correct</strong>
        </div>
        <small>Reliable answers</small>
    </div>
</div>
</div>

<div style="background-color: #e3f2fd; border: 2px solid #2196F3; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h3 style="color: #1976d2; margin-top: 0;">📊 Before vs. After Comparison</h3>
<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    <tr style="background-color: #2196F3; color: white;">
        <th style="padding: 12px; text-align: left; border: 1px solid #ddd;">Metric</th>
        <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Before</th>
        <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">After</th>
        <th style="padding: 12px; text-align: center; border: 1px solid #ddd;">Improvement</th>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Tool Calls</strong></td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">5-7</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">1-2</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd; color: #4CAF50;"><strong>↓ 70%</strong></td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Response Time</strong></td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">3-5s</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">&lt;2s</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd; color: #4CAF50;"><strong>↓ 60%</strong></td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Accuracy</strong></td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">Inconsistent</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">100%</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd; color: #4CAF50;"><strong>✓ Reliable</strong></td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Token Usage</strong></td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">High</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd;">Low</td>
        <td style="padding: 12px; text-align: center; border: 1px solid #ddd; color: #4CAF50;"><strong>↓ Cost</strong></td>
    </tr>
</table>
</div>

## Clean Up


```python
# Stop Phoenix server
phoenix_process.terminate()
phoenix_process.wait()
print("✅ Phoenix stopped")
```


```python
# Uninstall workflow
!pip uninstall climate_analyzer -y
```

## Summary
<div style="background-color: #e3f2fd; border: 2px solid #2196F3; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h3 style="color: #1976d2; margin-top: 0;">🎉 What You Accomplished</h3>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #4CAF50; margin-top: 0;">✅ What You Learned</h4>
<ol>
<li><strong>Set up Phoenix tracing</strong> - Added telemetry config to capture agent behavior</li>
<li><strong>Identified inefficiency</strong> - Found station queries causing unnecessary tool calls</li>
<li><strong>Made data-driven fix</strong> - Added dedicated tool based on observed patterns</li>
<li><strong>Measured improvement</strong> - Used Phoenix to verify 60-70% performance gain</li>
</ol>
</div>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #2196F3; margin-top: 0;">🔑 Key Insights</h4>
<ul>
<li><strong>Observability is essential</strong> - You can't optimize what you can't see</li>
<li><strong>Traces reveal patterns</strong> - Phoenix shows where agents struggle, not just that they fail</li>
<li><strong>Data-driven decisions</strong> - Improvements based on evidence, not guesses</li>
<li><strong>Before/after comparison</strong> - Phoenix lets you prove your changes worked</li>
</ul>
</div>
<div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="margin-top: 0;">💡 The Observability Loop</h4>
<div style="display: flex; justify-content: center; align-items: center; gap: 8px; margin: 0 auto; max-width: 700px;">
    <div style="text-align: center;">
        <div style="background-color: #ffc107; color: black; padding: 12px; border-radius: 8px; width: 120px;">
            <strong>1. Observe</strong>
        </div>
        <small>Use Phoenix tracing</small>
    </div>
    <span style="font-size: 20px;">→</span>
    <div style="text-align: center;">
        <div style="background-color: #ffc107; color: black; padding: 12px; border-radius: 8px; width: 120px;">
            <strong>2. Identify</strong>
        </div>
        <small>Find patterns</small>
    </div>
    <span style="font-size: 20px;">→</span>
    <div style="text-align: center;">
        <div style="background-color: #ffc107; color: black; padding: 12px; border-radius: 8px; width: 120px;">
            <strong>3. Fix</strong>
        </div>
        <small>Make targeted changes</small>
    </div>
    <span style="font-size: 20px;">→</span>
    <div style="text-align: center;">
        <div style="background-color: #ffc107; color: black; padding: 12px; border-radius: 8px; width: 120px;">
            <strong>4. Verify</strong>
        </div>
        <small>Measure improvement</small>
    </div>
</div>
</div>
<div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="margin-top: 0;">🚀 Next Lesson: Multi-Agent Orchestration</h4>
You'll learn to:
<ul>
<li>Integrate agents from other frameworks (LangGraph, CrewAI) into NAT</li>
<li>Orchestrate multiple specialized agents working together</li>
<li>Use Phoenix to trace multi-agent workflows</li>
<li>Build complex systems where agents coordinate on different tasks</li>
</ul>
This takes you from single-agent optimization to multi-agent collaboration.
</div>
</div>
