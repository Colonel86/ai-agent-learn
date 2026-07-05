# Lesson 2: Your First NAT Workflow
In this lesson, you'll learn how to create and run NAT workflows.

NAT workflows are defined in YAML configuration files that specify your agent's capabilities, which LLM to use, and which tools it can access. This config-driven approach means you can test different models or swap tools by changing a few lines—no code refactoring required.
You'll build a simple climate Q&A assistant, test it locally, deploy it as a REST API, and preview the final application you'll build by the end of the course.

<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 10px 0;">
<h4 style="margin-top: 0;">🎯 What you'll do:</h4>
<ul>
<li>Define your first agent in a YAML config file</li>
<li>Test your workflow locally before deploying</li>
<li>Launch it as a REST API and send live requests</li>
<li>See how NAT automatically generates interactive API documentation</li>
<li>Preview the UI you'll build for your agent</li>
</ul>
</div>

**Note:** All dependencies are pre-installed on the DeepLearning.AI platform. If you're running this in your own environment, uncomment and run the following code to install NAT and LangChain endpoints:


```python
%%capture
#install Nemo Agent Toolkit and langchain dependency
!pip install nvidia-nat
!pip install "nvidia-nat[langchain]"
```

### Getting your own API key

<div style="background-color: #e8f4f8; border-left: 4px solid #0076ce; padding: 15px; margin: 10px 0; border-radius: 4px;">
    <p style="margin: 0; font-size: 14px; line-height: 1.6;">
        <strong>📝 Note:</strong> An API key is already configured in the course environment. If you're running this code in your own environment, visit <a href="https://build.nvidia.com" target="_blank" style="color: #0076ce;">https://build.nvidia.com</a> to create a free account and generate an API key, then set it as an environment variable using a <code>.env</code> file or <code>export NVIDIA_API_KEY='your-key'</code>.
    </p>
</div>


```python
# load env variables 
from dotenv import load_dotenv
import os
   
# Load environment variables from .env file
load_dotenv()
   
# Verify the key loaded
print("API key loaded:", "Yes" if os.getenv('NVIDIA_API_KEY') else "No")
```

## Create the NAT Configuration
Start by creating `config.yml`. This YAML file defines your entire workflow in a declarative way— no Python code needed.

<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">📋 Config File Structure</h4>
Your config has two main sections:
<br><br>
<strong>llms:</strong> Defines the language models available to your workflow. Each model gets a name (like <code>climate_llm</code>) that you'll reference later. Here you specify:
<ul>
<li>Which model to use (<code>meta/llama-3.1-70b-instruct</code>)</li>
<li>Where to find it (NVIDIA's API endpoint)</li>
<li>Generation parameters (temperature, max tokens)</li>
</ul>
<strong>workflow:</strong> Defines how your agent behaves. In this simple example:
<ul>
<li><code>_type: chat_completion</code> means it's a basic conversational agent</li>
<li><code>llm_name</code> connects to the LLM you defined above</li>
<li><code>system_prompt</code> sets the agent's personality and expertise</li>
</ul>
</div>


```python
%%writefile config.yml

llms:
  climate_llm:
    _type: nim
    model_name: meta/llama-3.1-70b-instruct
    base_url: $NVIDIA_BASE_URL
    api_key: $NVIDIA_API_KEY
    temperature: 0.7
    max_tokens: 2048

workflow:
  _type: chat_completion
  llm_name: climate_llm
  system_prompt: |
    You are a knowledgeable climate science assistant. You help users understand 
    climate data, weather patterns, and global temperature trends. Be accurate, 
    informative, and cite scientific consensus when appropriate.
```

## Test Your Workflow
Before deploying as an API, test your workflow locally using `nat run`. 

<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">🔍 What <code>nat run</code> Does</h4>
<ol>
<li>Reads your config file</li>
<li>Initializes the specified LLM</li>
<li>Sends your query through the workflow</li>
<li>Returns the result</li>
</ol>
This is perfect for quick testing before deploying as an API.
</div>

Try these three test questions that progress from general knowledge to more specific data questions:

### Question 1: Climate Basics

<div style="background-color: #e8f5e9; border-left: 6px solid #4CAF50; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">📊 Test 1: Simple Definition (Easy)</h4>
<p><strong>Type:</strong> <span style="background-color: #4CAF50; color: white; padding: 3px 8px; border-radius: 3px;">General Knowledge</span></p>
<p><strong>Expected Result:</strong> Clear, accurate answer from LLM's training data</p>
</div>

<div><p style="background-color:#f7fff8; padding:15px; border-width:3px; border-color:#e0f0e0; border-style:solid; border-radius:6px">
&nbsp; <b>Different Run Results:</b> The output visualizations generated may differ from those shown in the video.</p></div>


```python
# Simple question about climate basics
!nat run \
  --config_file config.yml \
  --input "What is the difference between weather and climate?"
```

<div style="background-color: #f5f5f5; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin: 15px 0; font-family: monospace;">
<strong>Expected Output:</strong>
<pre style="margin: 10px 0; white-space: pre-wrap;">
Contains a statement along the lines of: Weather refers to short-term atmospheric conditions (days to weeks), while climate describes long-term patterns (typically 30+ years). Weather changes frequently; climate represents average conditions over time.
</pre>
</div>

### Question 2: Global Temperature Trends
<div style="background-color: #fff3e0; border-left: 6px solid #ff9800; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">📊 Test 2: Scientific Fact (Moderate)</h4>
<p><strong>Type:</strong> <span style="background-color: #ff9800; color: white; padding: 3px 8px; border-radius: 3px;">Scientific Knowledge</span></p>
<p><strong>Expected Result:</strong> Fact-based answer with approximate figures</p>
</div>



```python
# Question about global temperature trends
!nat run \
  --config_file config.yml \
  --input "How much has global average \
  temperature increased since pre-industrial times?"
```

<div style="background-color: #f5f5f5; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin: 15px 0; font-family: monospace;">
<strong>Expected Output:</strong>
<pre style="margin: 10px 0; white-space: pre-wrap;">
Global average temperature has increased approximately 1.1-1.2°C since pre-industrial times (1850-1900). This warming is primarily due to human activities, particularly greenhouse gas emissions.
</pre>
</div>

### Question 3: Specific Data Query
<div style="background-color: #ffebee; border-left: 6px solid #f44336; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">📊 Test 3: Specific Data (Reveals Limitation)</h4>
<p><strong>Type:</strong> <span style="background-color: #f44336; color: white; padding: 3px 8px; border-radius: 3px;">Data-Specific</span></p>
<p><strong>Expected Result:</strong> Agent can't provide exact data—will either admit it or hallucinate</p>
</div>


```python
# A data-specific question that would benefit from real data analysis
!nat run \
  --config_file config.yml \
  --input "What were the exact temperature anomalies \
  for the top 5 warmest countries in 2023?"
```

<div style="background-color: #f5f5f5; border: 1px solid #ddd; padding: 15px; border-radius: 5px; margin: 15px 0; font-family: monospace;">
<strong>Expected Output:</strong>
<pre style="margin: 10px 0; white-space: pre-wrap;">
The agent might say something like: "I don't have access to specific 2023 temperature anomaly data for individual countries. To answer this accurately, I would need to query a climate database." It might also just hallucinate a response. 


<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 10px;">
<strong>Notice the Limitation:</strong> <br>
Your agent can answer general climate questions, but it can't analyze real data or perform calculations. It's limited to knowledge from its training set.
<br><br>
In the next lesson, you'll register Python functions as tools—giving your agent the ability to load climate datasets, calculate temperature anomalies, and generate visualizations.
</div>

## Deploy as an API
Now make your agent accessible through a REST API endpoint using `nat serve`.

In production, you can run the following line in a terminal:
```bash
nat serve --config_file config.yml
```

But since you're in a Jupyter notebook, you'll use Python's `subprocess` to start the server in the background:
### Start the local API Server:

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> <b>Note <code>(Server Starting)</code>:</b> The API server can take about 60 seconds to be ready for use. </p>


```python
# use subprocess since you are running in a notebook
import subprocess
import time

# Clean up old processes if you ran notebook before
!pkill -f "nat serve" 2>/dev/null || true
time.sleep(2)

# Start NAT with explicit IPv4 host
nat_process = subprocess.Popen(
    ["nat", "serve", "--config_file", "config.yml", "--host", "127.0.0.1"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait and let it print to console naturally
time.sleep(25)
```

<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 What's Happening Here?</h4>
<ul>
<li><strong>subprocess.Popen</strong> starts the NAT server as a separate process</li>
<li><strong>stderr=subprocess.DEVNULL</strong> suppresses informational logs (not actual errors)</li>
<li><strong>Server runs on</strong> <code>http://localhost:8000</code> by default</li>
<li><strong>NAT automatically generates</strong> API documentation at <code>http://localhost:8000/docs</code></li>
</ul>
</div>
<div style="background-color: #e8f5e9; border-left: 6px solid #4CAF50; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">🎯 What NAT Handles Automatically</h4>
<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    <tr style="background-color: #4CAF50; color: white;">
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Feature</th>
        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">What It Does</th>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>API Routing</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Creates standard REST endpoints automatically</td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Request Validation</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Validates incoming requests match expected format</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Error Handling</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Returns proper HTTP status codes and error messages</td>
    </tr>
</table>
</div>

### Test the API
Now send a POST request to your running NAT API server- NAT uses the OpenAI-compatible chat completions format, so any tool that works with OpenAI's API will work with your NAT agent. The API server will use the API key and base URL previously set in `config.yml`. 


```python
import requests
import json

# Test the API endpoint
response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={"Content-Type": "application/json"},
    json={
        "messages": [
            {
                "role": "user",
                "content": "What causes El Niño and how does it affect global weather?"
            }
        ],
        "stream": False
    }
)

# Parse and display the response
if response.status_code == 200:
    result = response.json()
    print(result["choices"][0]["message"]["content"])
else:
    print(f"Error: {response.status_code}")
    print(response.text)
```

<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 Response Structure</h4>
NAT returns a JSON object matching OpenAI's format:
<ul>
<li><code>choices[0].message.content</code> contains the agent's text response</li>
<li><code>usage</code> shows token counts (prompt tokens + completion tokens)</li>
<li><code>model</code> shows which LLM was used</li>
</ul>
<br>
This OpenAI-compatible format means your NAT agents can drop into existing applications that use OpenAI's API.
</div>

## Quick UI Demo
Throughout the course, you'll enhance your workflow with tools, tracing, and evaluation. In the final lesson, you'll deploy a UI that lets users interact with your agent through a chat interface.

✨ **Run the following code to preview the final UI you'll build (video may not reflect changes in the current version):** 


```python
from ui_manager import ui_manager

ui_manager.start()
ui_manager.show_ui_link()
```

<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💬 Try These Questions</h4>
<ul>
<li>"What is climate change?"</li>
<li>"How do scientists measure global temperature?"</li>
<li>"What were the warmest years on record?" (notice it can't give precise data yet)</li>
</ul>
<br>
<strong>What you'll notice:</strong> The agent can answer general questions well, but struggles with specific data queries. That's what you'll fix in the next lesson by adding tools.
</div>

## Clean Up
Before moving to the next lesson, stop the running processes to free up resources and avoid port conflicts:


```python
ui_manager.stop()
nat_process.terminate()
nat_process.wait()
print("✅ Server stopped")
```

## Summary
<div style="background-color: #e3f2fd; border: 2px solid #2196F3; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h3 style="color: #1976d2; margin-top: 0;">🎉 Congratulations on Building Your First NAT Workflow!</h3>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0;">
    <div style="background-color: white; padding: 15px; border-radius: 5px;">
        <h4 style="color: #4CAF50; margin-top: 0;">✅ What You Built</h4>
        <ul>
            <li>A YAML-based agent configuration (no Python code required)</li>
            <li>A climate Q&A assistant with custom system prompt</li>
            <li>A REST API endpoint with OpenAI-compatible format</li>
            <li>A preview of the chat interface you'll deploy</li>
        </ul>
    </div>
    <div style="background-color: white; padding: 15px; border-radius: 5px;">
        <h4 style="color: #2196F3; margin-top: 0;">🔧 Key Concepts</h4>
        <ul>
            <li><strong>Config-driven development</strong> - Change models/settings without code changes</li>
            <li><strong>nat run</strong> - Test locally before deploying</li>
            <li><strong>nat serve</strong> - Deploy as API instantly</li>
            <li><strong>OpenAI compatibility</strong> - Works with existing tools</li>
        </ul>
    </div>
</div>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #4CAF50; margin-top: 0;">✅ Current Capabilities</h4>
<ul>
<li>Answers general climate questions from LLM's training data</li>
<li>Serves responses through a REST API</li>
<li>Can connect to any chat UI or application</li>
<li>Auto-generates API documentation</li>
</ul>
</div>
<div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="margin-top: 0;">⚠️ Current Limitation</h4>
No access to real climate datasets—your agent can't:
<ul>
<li>Analyze actual temperature data</li>
<li>Perform calculations on climate records</li>
<li>Generate visualizations from data</li>
<li>Answer questions like "What were the 5 warmest years on record?"</li>
</ul>
</div>
<div style="background-color: #d4edda; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="margin-top: 0;">🚀 Next Lesson: Add Tools</h4>
You'll register Python functions as tools, giving your agent the ability to:
<ul>
<li>Load real climate data from CSV files</li>
<li>Calculate temperature anomalies and trends</li>
<li>Generate data visualizations</li>
<li>Answer specific questions with real data</li>
<li>Coordinate multiple tools to solve complex problems</li>
</ul>
Your agent will transform from a knowledge-only chatbot into a data analysis system.
</div>
</div>
