# Lab 5: Agentic Rag and External Memory

## Preparation

<div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
<p> 💻 &nbsp; <b>Access <code>requirements.txt</code> and <code>helper.py</code> files:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em>.

<p> ⬇ &nbsp; <b>Download Notebooks:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Download as"</em> and select <em>"Notebook (.ipynb)"</em>.</p>

<p> 📒 &nbsp; For more help, please see the <em>"Appendix – Tips, Help, and Download"</em> Lesson.</p>
</div>

## Section 0: Setup a Letta client


```python
from letta_client import Letta

client = Letta(base_url="http://localhost:8283")
```


```python
def print_message(message):  
    if message.message_type == "reasoning_message": 
        print("🧠 Reasoning: " + message.reasoning) 
    elif message.message_type == "assistant_message": 
        print("🤖 Agent: " + message.content) 
    elif message.message_type == "tool_call_message": 
        print("🔧 Tool Call: " + message.tool_call.name + "\n" + message.tool_call.arguments)
    elif message.message_type == "tool_return_message": 
        print("🔧 Tool Return: " + message.tool_return)
    elif message.message_type == "user_message": 
        print("👤 User Message: " + message.content)
```

## Section 1: Data Sources

### Creating a source


```python
source = client.sources.create(
    name="employee_handbook",
    embedding="openai/text-embedding-3-small"
)
source
```

### Uploading a source


```python
job = client.sources.files.upload(
    source_id=source.id,
    file=open("handbook.pdf", "rb")
)
```


```python
job.status
```

### Viewing job status over time


```python
import time
from letta_client import JobStatus

while job.status != 'completed':
    job = client.jobs.retrieve(job.id)
    print(job.status)
    time.sleep(1)
```

### Viewing job metadata


```python
job.metadata
```


```python
passages = client.sources.passages.list(
    source_id=source.id,
)
len(passages)
```

### Creating an agent and attaching sources


```python
agent_state = client.agents.create(
    memory_blocks=[
        {
          "label": "human",
          "value": "My name is Sarah"
        },
        {
          "label": "persona",
          "value": "You are a helpful assistant"
        }
    ],
    model="openai/gpt-4o-mini-2024-07-18",
    embedding="openai/text-embedding-3-small"
)
```


```python
agent_state = client.agents.sources.attach(
    agent_id=agent_state.id, 
    source_id=source.id
)
```

### Viewing agent's attached sources


```python
client.agents.sources.list(agent_id=agent_state.id)
```


```python
passages = client.agents.passages.list(agent_id=agent_state.id)
len(passages)
```

### Messaging agents and referencing attached sources


```python
response = client.agents.messages.create(
    agent_id=agent_state.id,
    messages=[
        {
            "role": "user",
            "content": "Search archival for our company's vacation policies"
        }
    ]
)
for message in response.messages:
    print_message(message)
```

## Section 2: Connecting Data with Custom Tools

### Creating a custom tool


```python
def query_birthday_db(name: str):
    """
    This tool queries an external database to
    lookup the birthday of someone given their name.

    Args:
        name (str): The name to look up

    Returns:
        birthday (str): The birthday in mm-dd-yyyy format

    """
    my_fake_data = {
        "bob": "03-06-1997",
        "sarah": "07-06-1993"
    }
    name = name.lower()
    if name not in my_fake_data:
        return None
    else:
        return my_fake_data[name]
```


```python
birthday_tool = client.tools.upsert_from_function(func=query_birthday_db)
```

### Creating an agent with access to tools


```python
agent_state = client.agents.create(
    memory_blocks=[
        {
          "label": "human",
          "value": "My name is Sarah"
        },
        {
          "label": "persona",
          "value": "You are a agent with access to a birthday_db " \
            + "that you use to lookup information about users' birthdays."
        }
    ],
    model="openai/gpt-4o-mini-2024-07-18",
    embedding="openai/text-embedding-3-small",
    tool_ids=[birthday_tool.id],
    #tool_exec_environment_variables={"DB_KEY": "my_key"}
)
```


```python
# send a message to the agent
response = client.agents.messages.create_stream(
    agent_id=agent_state.id,
    messages=[
        {
            "role": "user",
            "content": "whens my bday????"
        }
    ]
)
for message in response:
    print_message(message)
```
