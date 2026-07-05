# Lesson 2: Create a SQL Agent



> Note: You can access the `data` and `util` subdirectories used in the course. In Jupyter version 6, this is via the File>Open menu. In Jupyter version 7 this is in View> File Browser

> Also note that as models and systems change, the output of the models may shift from the video content.


```python
import lamini 
```


```python
import logging
import sqlite3
import pandas as pd
from util.get_schema import get_schema
from util.make_llama_3_prompt import make_llama_3_prompt
from util.setup_logging import setup_logging

logger = logging.getLogger(__name__)
engine = sqlite3.connect("./nba_roster.db")
setup_logging()
```


```python
llm = lamini.Lamini(model_name="meta-llama/Meta-Llama-3-8B-Instruct")
```


```python
# Meta Llama 3 Instruct uses a prompt template, with special tags used to indicate the user query and system prompt. 
# You can find the documentation on this [model card](https://llama.meta.com/docs/model-cards-and-prompt-formats/meta-llama-3/#meta-llama-3-instruct).
def make_llama_3_prompt(user, system=""):
    system_prompt = ""
    if system != "":
        system_prompt = (
            f"<|start_header_id|>system<|end_header_id|>\n\n{system}<|eot_id|>"
        )
    return f"<|begin_of_text|>{system_prompt}<|start_header_id|>user<|end_header_id|>\n\n{user}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
```


```python
def get_schema():
    return """\
0|Team|TEXT 
1|NAME|TEXT  
2|Jersey|TEXT 
3|POS|TEXT
4|AGE|INT 
5|HT|TEXT 
6|WT|TEXT 
7|COLLEGE|TEXT 
8|SALARY|TEXT eg. 
"""
```


```python
user = """Who is the highest paid NBA player?"""
```


```python
system = f"""You are an NBA analyst with 15 years of experience writing complex SQL queries. Consider the nba_roster table with the following schema:
{get_schema()}

Write a sqlite query to answer the following question. Follow instructions exactly"""
```


```python
print(system)
```


```python
prompt = make_llama_3_prompt(user, system)
```


```python
print(llm.generate(prompt, max_new_tokens=200))
```


```python
def get_updated_schema():
    return """\
0|Team|TEXT eg. "Toronto Raptors"
1|NAME|TEXT eg. "Otto Porter Jr."
2|Jersey|TEXT eg. "0" and when null has a value "NA"
3|POS|TEXT eg. "PF"
4|AGE|INT eg. "22" in years
5|HT|TEXT eg. `6' 7"` or `6' 10"`
6|WT|TEXT eg. "232 lbs" 
7|COLLEGE|TEXT eg. "Michigan" and when null has a value "--"
8|SALARY|TEXT eg. "$9,945,830" and when null has a value "--"
"""
```


```python
system = f"""You are an NBA analyst with 15 years of experience writing complex SQL queries. Consider the nba_roster table with the following schema:
{get_updated_schema()}

Write a sqlite query to answer the following question. Follow instructions exactly"""
```


```python
prompt = make_llama_3_prompt(user, system)
```


```python
print(prompt)
```


```python
print(llm.generate(prompt, max_new_tokens=200))
```

## Structured Output

We'd like to be able to get just SQL output so we don't have to parse the query from the model response. For this we can use structured output.


```python
result = llm.generate(prompt, output_type={"sqlite_query": "str"}, max_new_tokens=200)
```


```python
result
```

This is great, now we can directly query with the output


```python
df = pd.read_sql(result['sqlite_query'], con=engine)
```


```python
df
```

## Diagnose Hallucinations

The **wrong** query looks like this:

```sql
SELECT NAME, SALARY
FROM nba_roster
WHERE salary != '--'
ORDER BY CAST(SALARY AS REAL) DESC
LIMIT 1;
```


The **correct** query is:

```sql
SELECT salary, name 
FROM nba_roster
WHERE salary != '--'
ORDER BY CAST(REPLACE(REPLACE(salary, '$', ''), ',','') AS INTEGER) DESC
LIMIT 1;
```


```python
query="""SELECT salary, name 
FROM nba_roster 
WHERE salary != '--' 
ORDER BY CAST(REPLACE(REPLACE(salary, '$', ''), ',','') AS INTEGER) DESC 
LIMIT 1;"""
df = pd.read_sql(query, con=engine)
print(df)
```


```python

```
