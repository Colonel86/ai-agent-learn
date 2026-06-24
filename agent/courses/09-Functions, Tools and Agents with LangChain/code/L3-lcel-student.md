# LangChain Expression Language (LCEL)


```python
import os
import openai

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']
```


```python
#!pip install pydantic==1.10.8
```


```python
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
```

## Simple Chain


```python
prompt = ChatPromptTemplate.from_template(
    "tell me a short joke about {topic}"
)
model = ChatOpenAI()
output_parser = StrOutputParser()
```


```python
chain = prompt | model | output_parser
```


```python
chain.invoke({"topic": "bears"})
```

## More complex chain

And Runnable Map to supply user-provided inputs to the prompt.


```python
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import DocArrayInMemorySearch
```


```python
vectorstore = DocArrayInMemorySearch.from_texts(
    ["harrison worked at kensho", "bears like to eat honey"],
    embedding=OpenAIEmbeddings()
)
retriever = vectorstore.as_retriever()
```


```python
retriever.get_relevant_documents("where did harrison work?")
```


```python
retriever.get_relevant_documents("what do bears like to eat")
```


```python
template = """Answer the question based only on the following context:
{context}

Question: {question}
"""
prompt = ChatPromptTemplate.from_template(template)
```


```python
from langchain.schema.runnable import RunnableMap
```


```python
chain = RunnableMap({
    "context": lambda x: retriever.get_relevant_documents(x["question"]),
    "question": lambda x: x["question"]
}) | prompt | model | output_parser
```


```python
chain.invoke({"question": "where did harrison work?"})
```


```python
inputs = RunnableMap({
    "context": lambda x: retriever.get_relevant_documents(x["question"]),
    "question": lambda x: x["question"]
})
```


```python
inputs.invoke({"question": "where did harrison work?"})
```

## Bind

and OpenAI Functions


```python
functions = [
    {
      "name": "weather_search",
      "description": "Search for weather given an airport code",
      "parameters": {
        "type": "object",
        "properties": {
          "airport_code": {
            "type": "string",
            "description": "The airport code to get the weather for"
          },
        },
        "required": ["airport_code"]
      }
    }
  ]
```


```python
prompt = ChatPromptTemplate.from_messages(
    [
        ("human", "{input}")
    ]
)
model = ChatOpenAI(temperature=0).bind(functions=functions)
```


```python
runnable = prompt | model
```


```python
runnable.invoke({"input": "what is the weather in sf"})
```


```python
functions = [
    {
      "name": "weather_search",
      "description": "Search for weather given an airport code",
      "parameters": {
        "type": "object",
        "properties": {
          "airport_code": {
            "type": "string",
            "description": "The airport code to get the weather for"
          },
        },
        "required": ["airport_code"]
      }
    },
        {
      "name": "sports_search",
      "description": "Search for news of recent sport events",
      "parameters": {
        "type": "object",
        "properties": {
          "team_name": {
            "type": "string",
            "description": "The sports team to search for"
          },
        },
        "required": ["team_name"]
      }
    }
  ]
```


```python
model = model.bind(functions=functions)
```


```python
runnable = prompt | model
```


```python
runnable.invoke({"input": "how did the patriots do yesterday?"})
```

## Fallbacks


```python
from langchain.llms import OpenAI
import json
```

**Note**: Due to the deprication of OpenAI's model `text-davinci-001` on 4 January 2024, you'll be using OpenAI's recommended replacement model `gpt-3.5-turbo-instruct` instead.


```python
simple_model = OpenAI(
    temperature=0, 
    max_tokens=1000, 
    model="gpt-3.5-turbo-instruct"
)
simple_chain = simple_model | json.loads
```


```python
challenge = "write three poems in a json blob, where each poem is a json blob of a title, author, and first line"
```


```python
simple_model.invoke(challenge)
```

<p style=\"background-color:#F5C780; padding:15px\"><b>Note:</b> The next line is expected to fail.</p>


```python
simple_chain.invoke(challenge)
```


```python
model = ChatOpenAI(temperature=0)
chain = model | StrOutputParser() | json.loads
```


```python
chain.invoke(challenge)
```


```python
final_chain = simple_chain.with_fallbacks([chain])
```


```python
final_chain.invoke(challenge)
```

## Interface


```python
prompt = ChatPromptTemplate.from_template(
    "Tell me a short joke about {topic}"
)
model = ChatOpenAI()
output_parser = StrOutputParser()

chain = prompt | model | output_parser
```


```python
chain.invoke({"topic": "bears"})
```


```python
chain.batch([{"topic": "bears"}, {"topic": "frogs"}])
```


```python
for t in chain.stream({"topic": "bears"}):
    print(t)
```


```python
response = await chain.ainvoke({"topic": "bears"})
response
```


```python

```


```python

```


```python

```


```python

```


```python

```


```python

```
