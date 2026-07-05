# Lesson 1: Your First AI Agent

Welcome to Lesson 1.

To access the `requirements.txt` file, please go to the `File` menu and select`Open...`.

I hope you enjoy this course!

## Setup


```python
import os 
import pandas as pd 
from IPython.display import Markdown, HTML, display
```

## Connect to the Azure OpenAI endpoint

**Note**: The pre-configured cloud resource grants you access to the Azure OpenAI GPT model. The key and endpoint provided below are intended for teaching purposes only. Your notebook environment is already set up with the necessary keys, which may differ from those used by the instructor during the filming.

```
openai_api_version="2023-05-15"
azure_deployment="gpt-4-1106"
azure_endpoint="https://testadri.openai.azure.com"

```

## 1. Leveraging Langchain


```python
from langchain.schema import HumanMessage
from langchain_openai import AzureChatOpenAI

model = AzureChatOpenAI(
    openai_api_version="2024-04-01-preview",
    azure_deployment="gpt-4-1106",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)
```

## 2. Preparing your prompt


```python
message = HumanMessage(
    content="Translate this sentence from English "
    "to French and Spanish. I like red cars and "
    "blue houses, but my dog is yellow."
)
```

## 3. Engaging the model to receive a response


```python
model.invoke([message])
```
