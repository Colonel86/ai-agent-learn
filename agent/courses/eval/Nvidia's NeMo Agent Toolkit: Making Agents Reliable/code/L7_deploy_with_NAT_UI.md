# Lesson 7: Production Deployment with NAT UI
You've built a complete climate analysis agent with tools, tracing, multi-agent integration, and evaluation. But right now, only you can use it through the command line. To make your agent accessible to others, you need a user interface and production deployment.In this final lesson, you'll deploy your agent with a web-based chat interface, connect it to your running NAT API, and see how all the pieces come together into a production-ready application that anyone can use.<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 10px 0;">
<h4 style="margin-top: 0;">🎯 Learning Objectives</h4>
By the end of this lesson, you'll know how to:
<ul>
<li>Deploy your NAT agent as a REST API</li>
<li>Connect a web UI to your agent's API</li>
<li>Test the complete system with real user interactions</li>
<li>Understand the production deployment architecture</li>
</ul>
</div>


```python
%%capture
# load env variables
import os
from dotenv import load_dotenv
load_dotenv()

# Install the climate analyzer package
!cd climate_analyzer && pip install -e . && cd ..
```

## Start the NAT Server
This code starts your climate analysis agent as a REST API that the web UI can connect to. 

If you have run this notebook previously, you can run the following code to kill any existing processes that may prevent NAT server from gaining access to an open port: 

```python
# Kill anything on port 8000 
subprocess.run("pkill -9 -f 'nat serve'", shell=True)
time.sleep(3)
```


```python
# start the NAT server
import subprocess
import time

# Start NAT with explicit IPv4 host
nat_process = subprocess.Popen(
    ["nat", "serve", "--config_file", "./climate_analyzer/src/climate_analyzer/configs/config.yml", 
     "--host", "127.0.0.1", "--port", "8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for it to start
time.sleep(10)

# Check if it crashed
if nat_process.poll() is not None:
    stdout, stderr = nat_process.communicate()
    print("❌ Server crashed!")
    print("\n=== Error Output ===")
    print(stderr[-500:])
else:
    print("✅ Server is running in the background!")
```

<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">🔍 What NAT Serve Does</h4>
<ul>
<li><strong>Checks specified port</strong> - Makes sure nothing else is using the host and port you selected (default 127.0.0.1:8000)</li>
<li><strong>Starts NAT server</strong> - Launches your agent as a REST API in the background</li>
<li><strong>Waits for startup</strong> - Pauses briefly and verifies the server started successfully</li>
<li><strong>Monitors for crashes</strong> - Detects if the server fails during startup and shows the last part of the error output</li>
<li><strong>Generates API docs</strong> - Auto-creates interactive documentation at /docs</li>
<li><strong>Registers cleanup</strong> - Automatically stops the server when you close the notebook or script</li>
</ul>
<br>
The server uses the OpenAI-compatible <code>/v1/chat/completions</code> endpoint, so any tool that works with OpenAI's API works with NAT. Your agent is exposed at <code>http://127.0.0.1:8000</code>, and the web UI will send user messages to this endpoint, with your agent processing and returning responses.
</div>

## Install NeMo Agent Toolkit UI and Dependencies

- **Clone the NAT UI Repository** - Clones the NAT UI repository from GitHub if it doesn't already exist locally
- **Installs JavaScript dependencies** – Uses `npm install` to fetch React, Next.js, and other required packages, creating the node_modules/ folder with ~1000 packages. We've already done this for you on the deeplearning platform, but if you are running on your own environment, make sure to uncomment and run this block of code. 

**This step may take several minutes.**

Without these steps, the UI won’t start because it’s missing dependencies and the built assets (similar to trying to run Python code without installing required packages via pip).


```python
from pathlib import Path

ui_path = Path("NeMo-Agent-Toolkit-UI")

if not ui_path.exists():
    print("Cloning NAT UI repository...")
    subprocess.run([
        "git", "clone",
        "https://github.com/NVIDIA/NeMo-Agent-Toolkit-UI.git"
    ], check=True)
    print("UI repository cloned")
else:
    print("UI respository already exists!")
```

## Architecture Overview
Before deploying, let's understand how the pieces fit together:

<div style="background-color: #f9f9f9; border: 2px solid #ddd; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h2 style="text-align: center;">Production Architecture</h2>
<div style="margin: 20px 0;">
    <div style="text-align: center; margin-bottom: 15px;">
        <div style="display: inline-block; background-color: #2196F3; color: white; padding: 20px; border-radius: 8px; width: 280px; text-align: center;">
            <strong>🌐 Web UI (Frontend)</strong><br>
            <small>React/Next.js chat interface</small>
        </div>
    </div>

<div style="text-align: center; font-size: 24px; margin: 10px 0;">↓ HTTP Requests</div>

<div style="text-align: center; margin: 15px 0;">
    <div style="display: inline-block; background-color: #4CAF50; color: white; padding: 20px; border-radius: 8px; width: 280px; text-align: center;">
        <strong>🚀 NAT API Server</strong><br>
        <small>FastAPI server on port 8000</small>
    </div>
</div>

<div style="text-align: center; font-size: 24px; margin: 10px 0;">↓ Orchestrates</div>

<div style="text-align: center; margin: 15px 0;">
    <div style="display: inline-flex; justify-content: center; gap: 10px; flex-wrap: wrap; max-width: 600px;">
        <div style="background-color: #FF9800; color: white; padding: 15px; border-radius: 8px; width: 180px; text-align: center;">
            <strong>🔧 Climate Tools</strong><br>
            <small>Data analysis</small>
        </div>
        <div style="background-color: #9C27B0; color: white; padding: 15px; border-radius: 8px; width: 180px; text-align: center;">
            <strong>🧮 Calculator Agent</strong><br>
            <small>LangGraph math</small>
        </div>
        <div style="background-color: #f44336; color: white; padding: 15px; border-radius: 8px; width: 180px; text-align: center;">
            <strong>📊 Phoenix Tracing</strong><br>
            <small>Observability</small>
        </div>
    </div>
</div>

</div>
</div>
<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 How It Works</h4>
<ol>
<li><strong>User types message</strong> in web UI</li>
<li><strong>UI sends HTTP POST</strong> to NAT API at <code>http://localhost:8000/v1/chat/completions</code></li>
<li><strong>NAT processes request</strong> through your ReAct agent workflow</li>
<li><strong>Agent calls tools</strong> (climate data, calculator, visualizations)</li>
<li><strong>Phoenix captures traces</strong> for every step</li>
<li><strong>NAT returns response</strong> to UI</li>
<li><strong>UI displays answer</strong> to user</li>
</ol>
</div>

<div style="background-color: #f9f9f9; border: 2px solid #ddd; padding: 20px; border-radius: 8px; margin: 20px auto; max-width: 700px; text-align: center;">
<h4 style="margin-bottom: 30px;">How UI and API Work Together</h4>
<div style="display: flex; flex-direction: column; gap: 15px; align-items: center;">
    <div style="background-color: #2196F3; color: white; padding: 20px; border-radius: 8px; width: 250px;">
        <strong>🌐 Web UI</strong><br>
        <small>http://localhost:3000</small><br>
        <small>User types message</small>
    </div>
    <div style="font-size: 24px;">↓ HTTP POST</div>
    <div style="background-color: #4CAF50; color: white; padding: 20px; border-radius: 8px; width: 250px;">
        <strong>🚀 NAT API</strong><br>
        <small>http://localhost:8000</small><br>
        <small>Processes with agent</small>
    </div>
    <div style="font-size: 24px;">↑ JSON Response</div>
    <div style="background-color: #2196F3; color: white; padding: 20px; border-radius: 8px; width: 250px;">
        <strong>🌐 Web UI</strong><br>
        <small>Displays answer to user</small>
    </div>
</div>
</div>


```python
# uncomment and run if you are running in your own environment
# print("Installing dependencies...this could take a few minutes")
# subprocess.run(["npm", "ci"], cwd=ui_path, check=True)
# print("Dependencies installed")
```

## Start UI

This code starts the NeMo Agent Toolkit web UI in **development mode** in the background, so you can interact with your agent through a browser.

<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">🔍 What Each Part Does</h4>

1. **Start the Next.js development server**
   - `["npm", "run", "dev` – Launches the UI in dev mode with hot-reloading
   - `cwd=ui_path` – Runs inside the NeMo-Agent-Toolkit-UI directory
   - `stdout/stderr=subprocess.PIPE` – Captures output for debugging if needed
   - `env={**os.environ, "NEXT_TELEMETRY_DISABLED": "1"}` – Disables Next.js telemetry

2. **Track the process**
   - `ui_process` – Keeps a reference so the server can be stopped later if needed

3. **Wait for startup**
   - `time.sleep(30)` – Gives the dev server time to compile and initialize before use

</div>


```python
# start UI
print("Starting UI development server...")
ui_process = subprocess.Popen(
    ["npm", "run", "dev"],
    cwd=ui_path,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    env={**os.environ, "NEXT_TELEMETRY_DISABLED": "1"}
)

time.sleep(30)
print(f"UI started!")
```

## Access the UI
This code generates the accessible URL for the NeMo Agent Toolkit web UI on the DeepLearning.AI platform 

<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">🔍 What Each Part Does</h4>

1. **Build the platform-specific URL**
- Extracts the server IP from the `HOSTNAME` environment variable
- Constructs the full URL using the platform's reverse proxy pattern `(REV_PROXY_BASE_DOMAIN)`

2. **Display the URL**
- Prints the URL in bold so it's easy to find and click
</div>

**Summary:** This generates the correct URL for accessing your agent through the DeepLearning.AI platform's reverse proxy, since localhost URLs won't work in this hosted environment.


```python
import os

def make_nat_ui_url(port=3000):
    """Generate the accessible URL for NAT UI on DeepLearning.AI platform."""
    
    # Extract IP from hostname (same pattern as Phoenix)
    ip = os.environ['HOSTNAME'].split('.')[0][3:]
    
    # Build the URL using platform's reverse proxy pattern
    url = os.environ['REV_PROXY_BASE_DOMAIN'].format(ip=ip, port=port)
    
    # Terminal formatting
    BOLD = "\033[1m"
    RESET = "\033[0m"
    
    print(f"{BOLD}NAT UI URL: {url}{RESET}")
    return url

# Try both ports (one should work)
print("Your agent can be accessed at the following URL:\n")
url_proxy = make_nat_ui_url(3000)  # Proxy server

```

## Try These Questions in the UI
Once your agent has been successfully deployed and you are able to interact with the user interfact, test it out with these progressively complex queries:

<p style="background-color:#f7fff8; padding:15px; border-width:3px; border-color:#e0f0e0; border-style:solid; border-radius:6px"> 🛑
&nbsp; <b>Different Run Results:</b> The output responses generated may differ from those shown in the video.</p>

<div style="background-color: #e8f5e9; border-left: 6px solid #4CAF50; padding: 15px; margin: 20px 0;">
<h4 style="margin-top: 0;">📝 Suggested Test Queries</h4><div style="background-color: white; padding: 12px; margin: 10px 0; border-radius: 5px;">
<strong>1. Comparative Analysis</strong><br>
"What was Mexico's average temperature 1990-2000 vs global?"
<br><br>
<em>Tests: Time-range filtering, country comparison, data synthesis</em>

</div><div style="background-color: white; padding: 12px; margin: 10px 0; border-radius: 5px;">
<strong>2. Complete Analysis</strong><br>
"Complete climate analysis for France with trends and visualization."
<br><br>
<em>Tests: All capabilities - multiple tools, synthesis, visualization</em>
</div>  

<div>
<strong>3. Visualization Request</strong><br>
"Show the top 5 countries by warming trend with visualization."
<br><br>
<em>Tests: Data ranking, visualization generation, file handling</em>
</div>

<div style="background-color: white; padding: 12px; margin: 10px 0; border-radius: 5px;">
<strong>4. Mathematical Projection</strong><br>
"If temps rise 0.18°C/decade since 1980, project to 2050."
<br><br>
<em>Tests: Calculator agent integration, multi-step reasoning</em>
</div><div style="background-color: white; padding: 12px; margin: 10px 0; border-radius: 5px;">
<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">👀 What to Watch For</h4>
<p>As you test these queries, notice:</p>
<ul>
<li><strong>Response streaming</strong> - The answer appears word-by-word in real-time</li>
<li><strong>Tool calls happen invisibly</strong> - Users see natural language, not function calls</li>
<li><strong>Error recovery</strong> - If something fails, the agent explains what went wrong</li>
<li><strong>Natural synthesis</strong> - Multiple data points combined into coherent answers</li>
</ul>
</div>




```python
# ===== Cleanup =====
print("🛑 Stopping services...")
nat_process.terminate()
nat_process.wait()
!pkill -f "npm run dev" 2>/dev/null || true
print("✅ Services stopped")
```

## UI Features
<div style="background-color: #f3e5f5; border-left: 6px solid #9c27b0; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 What This UI Provides</h4>
<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd; width: 200px;"><strong>🔍 Real-Time Tool Calls</strong></td>
        <td style="padding: 12px; border: 1px solid #ddd;">Watch the agent's decision-making process - see which tools it calls and when</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>🔌 Connection Options</strong></td>
        <td style="padding: 12px; border: 1px solid #ddd;">Supports HTTP streaming, WebSocket, or standard HTTP requests</td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>💬 Chat History</strong></td>
        <td style="padding: 12px; border: 1px solid #ddd;">Maintains conversation context across multiple messages</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>📱 Responsive Design</strong></td>
        <td style="padding: 12px; border: 1px solid #ddd;">Works on desktop, tablet, and mobile devices</td>
    </tr>
</table>
</div>
<div style="background-color: #e7f3fe; border-left: 6px solid #2196F3; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">🔑 Key Insight: Build Your Own UI</h4>
<p>This UI is just <strong>one example</strong>. Your NAT API uses standard REST endpoints, so any frontend can connect to it:</p>
<ul>
<li><strong>Custom web apps</strong> - React, Vue, Angular, or plain JavaScript</li>
<li><strong>Mobile apps</strong> - iOS, Android, React Native</li>
<li><strong>Desktop applications</strong> - Electron, Qt, or native apps</li>
<li><strong>Voice interfaces</strong> - Alexa, Google Assistant integration</li>
<li><strong>Slack/Discord bots</strong> - Connect to messaging platforms</li>
</ul>
<br>
The API endpoint (<code>http://localhost:8000/v1/chat/completions</code>) is OpenAI-compatible, making integration straightforward.
</div>

## Production Deployment Options
Once you're ready to deploy beyond localhost, here are your options:
<div style="background-color: #e3f2fd; border: 2px solid #2196F3; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h4 style="color: #1976d2; margin-top: 0;">🚀 Deployment Strategies</h4>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #2196F3; margin-top: 0;">🐳 Docker Containerization</h4>
<p><strong>Package your entire workflow:</strong></p>
<ul>
<li>Agent code + dependencies</li>
<li>Python environment</li>
<li>Configuration files</li>
<li>Climate data (or connection to data source)</li>
</ul>
<br>
<strong>Benefits:</strong>
<ul>
<li>Consistent environment across dev/staging/production</li>
<li>Easy rollback if issues arise</li>
<li>Works anywhere Docker runs</li>
</ul>
</div>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #4CAF50; margin-top: 0;">☁️ Cloud Deployment</h4>
<p><strong>Deploy to major cloud providers:</strong></p>
<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 10px; border: 1px solid #ddd; width: 120px;"><strong>AWS</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">ECS (Elastic Container Service) or Lambda for serverless</td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Google Cloud</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Cloud Run or GKE (Google Kubernetes Engine)</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Azure</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Container Instances or Azure Kubernetes Service</td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Vercel/Render</strong></td>
        <td style="padding: 10px; border: 1px solid #ddd;">Simple deployment for API + UI together</td>
    </tr>
</table>
</div>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #FF9800; margin-top: 0;">📈 Scaling Strategies</h4>
<p><strong>Your NAT API uses standard REST - apply standard scaling:</strong></p>
<ul>
<li><strong>Horizontal scaling</strong> - Run multiple instances behind a load balancer</li>
<li><strong>Auto-scaling</strong> - Automatically add/remove instances based on traffic</li>
<li><strong>Caching layer</strong> - Redis or Memcached for frequent queries</li>
<li><strong>Database optimization</strong> - If you add conversation history storage</li>
<li><strong>CDN for UI</strong> - Serve static assets from edge locations</li>
</ul>
</div>
</div>
<div style="background-color: #fff3cd; border-left: 6px solid #ffc107; padding: 15px; margin: 15px 0;">
<h4 style="margin-top: 0;">💡 Key Insight: Standard Web Architecture</h4>
<p>Because NAT exposes a standard REST API, you can use all the same deployment and scaling tools you'd use for any web service. There's nothing special about deploying an AI agent vs. deploying a traditional API.</p>
</div>

## Summary
<div style="background-color: #e8f5e9; border: 2px solid #4CAF50; padding: 20px; border-radius: 8px; margin: 20px 0;">
<h3 style="color: #2e7d32; margin-top: 0;">🎉 What You've Accomplished</h3>
<div style="background-color: white; padding: 15px; border-radius: 5px; margin-top: 15px;">
<h4 style="color: #4CAF50; margin-top: 0;">✅ Your Climate Analyzer is Now:</h4>
<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 12px; border: 1px solid #ddd; width: 50px; text-align: center;">🚀</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>A Production API</strong> - Running on http://localhost:8000 with full OpenAI-compatible endpoints</td>
    </tr>
    <tr style="background-color: white;">
        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">🌐</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Accessible from Any Frontend</strong> - Web, mobile, desktop, voice interfaces - anything that can make HTTP requests</td>
    </tr>
    <tr style="background-color: #f9f9f9;">
        <td style="padding: 12px; border: 1px solid #ddd; text-align: center;">📈</td>
        <td style="padding: 12px; border: 1px solid #ddd;"><strong>Ready to Scale</strong> - Standard REST architecture means standard scaling: load balancers, auto-scaling, caching</td>
    </tr>
</table>
</div>
<div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin-top: 15px; border-left: 4px solid #2196F3;">
<h4 style="margin-top: 0;">💡 Key Insight</h4>
<p style="font-size: 16px; margin: 10px 0;">
<strong>NAT workflows become production APIs with one command:</strong>
</p>
<pre style="background-color: #f5f5f5; padding: 10px; border-radius: 3px; margin: 10px 0;">
nat serve --config_file config.yml
</pre>
<p style="margin: 10px 0;">
No additional deployment code. No API wrappers. Just your config file → running API.
</p>
</div>
<div style="background-color: #f9f9f9; border: 2px solid #ddd; padding: 20px; border-radius: 8px; margin: 20px auto; max-width: 700px; text-align: center;">
    <h4 style="color: #9C27B0; margin-bottom: 30px;">🔄 From Development to Production</h4>
    <div style="display: inline-flex; align-items: center; gap: 30px; flex-wrap: wrap;">
        <div style="text-align: center;">
            <div style="background-color: #FF9800; color: white; padding: 12px 20px; border-radius: 8px; margin-bottom: 10px;">
                <strong>nat run</strong>
            </div>
            <div style="font-size: 12px; color: #666;">Development/testing</div>
        </div>
        <div style="font-size: 24px;">→</div>
        <div style="text-align: center;">
            <div style="background-color: #4CAF50; color: white; padding: 12px 20px; border-radius: 8px; margin-bottom: 10px;">
                <strong>nat serve</strong>
            </div>
            <div style="font-size: 12px; color: #666;">Production API</div>
        </div>
    </div>
    <p style="text-align: center; color: #666; font-style: italic; margin-top: 20px;">
        Same config file. Same workflow. Different command.
    </p>
</div>
