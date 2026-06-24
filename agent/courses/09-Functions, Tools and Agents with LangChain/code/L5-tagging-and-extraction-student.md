# Tagging and Extraction Using OpenAI functions


```python
import os
import openai

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']
```


```python
from typing import List
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
```


```python
class Tagging(BaseModel):
    """Tag the piece of text with particular info."""
    sentiment: str = Field(description="sentiment of text, should be `pos`, `neg`, or `neutral`")
    language: str = Field(description="language of text (should be ISO 639-1 code)")
```


```python
convert_pydantic_to_openai_function(Tagging)
```


```python
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
```


```python
model = ChatOpenAI(temperature=0)
```


```python
tagging_functions = [convert_pydantic_to_openai_function(Tagging)]
```


```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "Think carefully, and then tag the text as instructed"),
    ("user", "{input}")
])
```


```python
model_with_functions = model.bind(
    functions=tagging_functions,
    function_call={"name": "Tagging"}
)
```


```python
tagging_chain = prompt | model_with_functions
```


```python
tagging_chain.invoke({"input": "I love langchain"})
```


```python
tagging_chain.invoke({"input": "non mi piace questo cibo"})
```


```python
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
```


```python
tagging_chain = prompt | model_with_functions | JsonOutputFunctionsParser()
```


```python
tagging_chain.invoke({"input": "non mi piace questo cibo"})
```

## Extraction

Extraction is similar to tagging, but used for extracting multiple pieces of information.


```python
from typing import Optional
class Person(BaseModel):
    """Information about a person."""
    name: str = Field(description="person's name")
    age: Optional[int] = Field(description="person's age")
```


```python
class Information(BaseModel):
    """Information to extract."""
    people: List[Person] = Field(description="List of info about people")
```


```python
convert_pydantic_to_openai_function(Information)
```


```python
extraction_functions = [convert_pydantic_to_openai_function(Information)]
extraction_model = model.bind(functions=extraction_functions, function_call={"name": "Information"})
```


```python
extraction_model.invoke("Joe is 30, his mom is Martha")
```


```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract the relevant information, if not explicitly provided do not guess. Extract partial info"),
    ("human", "{input}")
])
```


```python
extraction_chain = prompt | extraction_model
```


```python
extraction_chain.invoke({"input": "Joe is 30, his mom is Martha"})
```


```python
extraction_chain = prompt | extraction_model | JsonOutputFunctionsParser()
```


```python
extraction_chain.invoke({"input": "Joe is 30, his mom is Martha"})
```


```python
from langchain.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
```


```python
extraction_chain = prompt | extraction_model | JsonKeyOutputFunctionsParser(key_name="people")
```


```python
extraction_chain.invoke({"input": "Joe is 30, his mom is Martha"})
```

## Doing it for real

We can apply tagging to a larger body of text.

For example, let's load this blog post and extract tag information from a sub-set of the text.


```python
from langchain.document_loaders import WebBaseLoader
loader = WebBaseLoader("https://lilianweng.github.io/posts/2023-06-23-agent/")
documents = loader.load()
```


```python
doc = documents[0]
```


```python
page_content = doc.page_content[:10000]
```


```python
print(page_content[:1000])
```


```python
class Overview(BaseModel):
    """Overview of a section of text."""
    summary: str = Field(description="Provide a concise summary of the content.")
    language: str = Field(description="Provide the language that the content is written in.")
    keywords: str = Field(description="Provide keywords related to the content.")
```


```python
overview_tagging_function = [
    convert_pydantic_to_openai_function(Overview)
]
tagging_model = model.bind(
    functions=overview_tagging_function,
    function_call={"name":"Overview"}
)
tagging_chain = prompt | tagging_model | JsonOutputFunctionsParser()
```


```python
tagging_chain.invoke({"input": page_content})
```


```python
class Paper(BaseModel):
    """Information about papers mentioned."""
    title: str
    author: Optional[str]


class Info(BaseModel):
    """Information to extract"""
    papers: List[Paper]
```


```python
paper_extraction_function = [
    convert_pydantic_to_openai_function(Info)
]
extraction_model = model.bind(
    functions=paper_extraction_function, 
    function_call={"name":"Info"}
)
extraction_chain = prompt | extraction_model | JsonKeyOutputFunctionsParser(key_name="papers")
```


```python
extraction_chain.invoke({"input": page_content})
```


```python
template = """A article will be passed to you. Extract from it all papers that are mentioned by this article follow by its author. 

Do not extract the name of the article itself. If no papers are mentioned that's fine - you don't need to extract any! Just return an empty list.

Do not make up or guess ANY extra information. Only extract what exactly is in the text."""

prompt = ChatPromptTemplate.from_messages([
    ("system", template),
    ("human", "{input}")
])
```


```python
extraction_chain = prompt | extraction_model | JsonKeyOutputFunctionsParser(key_name="papers")
```


```python
extraction_chain.invoke({"input": page_content})
```


```python
extraction_chain.invoke({"input": "hi"})
```


```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(chunk_overlap=0)
```


```python
splits = text_splitter.split_text(doc.page_content)
```


```python
len(splits)
```


```python
def flatten(matrix):
    flat_list = []
    for row in matrix:
        flat_list += row
    return flat_list
```


```python
flatten([[1, 2], [3, 4]])
```


```python
print(splits[0])
```


```python
from langchain.schema.runnable import RunnableLambda
```


```python
prep = RunnableLambda(
    lambda x: [{"input": doc} for doc in text_splitter.split_text(x)]
)
```


```python
prep.invoke("hi")
```


```python
chain = prep | extraction_chain.map() | flatten
```


```python
chain.invoke(doc.page_content)
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
