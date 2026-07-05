# Lesson 1: Llama 3 Basics

> Note: You can access the `data` and `util` subdirectories used in the course. In Jupyter version 6, this is via the File>Open menu. In Jupyter version 7 this is in View> File Browser

> Also note that as models and systems change, the output of the models may shift from the video content.


```python
import lamini
```


```python
llm = lamini.Lamini(model_name="meta-llama/Meta-Llama-3-8B-Instruct")
```


```python
prompt = """\
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

You are a helpful assistant.<|eot_id|><|start_header_id|>user<|end_header_id|>

Please write a birthday card for my good friend Andrew\
<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
```


```python
result = llm.generate(prompt, max_new_tokens=200)
print(result)
```


```python
prompt2 = ( 
    "<|begin_of_text|>"  # Start of prompt
    "<|start_header_id|>system<|end_header_id|>\n\n"  #  header - system
    "You are a helpful assistant."  # system prompt
    "<|eot_id|>" # end of turn
    "<|start_header_id|>user<|end_header_id|>\n\n" # header - user
    "Please write a birthday card for my good friend Andrew" 
    "<|eot_id|>" # end of turn
    "<|start_header_id|>assistant<|end_header_id|>\n\n" # header - assistant
    )
print(prompt2)
```


```python
prompt == prompt2
```


```python
def make_llama_3_prompt(user, system=""):
    system_prompt = ""
    if system != "":
        system_prompt = (
            f"<|start_header_id|>system<|end_header_id|>\n\n{system}"
            f"<|eot_id|>"
        )
    prompt = (f"<|begin_of_text|>{system_prompt}"
              f"<|start_header_id|>user<|end_header_id|>\n\n"
              f"{user}"
              f"<|eot_id|>"
              f"<|start_header_id|>assistant<|end_header_id|>\n\n"
         )
    return prompt    
```


```python
system_prompt = user_prompt = "You are a helpful assistant."
user_prompt = "Please write a birthday card for my good friend Andrew"
prompt3 = make_llama_3_prompt(user_prompt, system_prompt)
print(prompt3)
```


```python
prompt == prompt3
```


```python
user_prompt = "Tell me a joke about birthday cake"
prompt = make_llama_3_prompt(user_prompt)
print(prompt)
```


```python
result = llm.generate(prompt, max_new_tokens=200)
print(result)
```

## Llama 3 can generate SQL


```python
question = (
    "Given an arbitrary table named `sql_table`, "
    "write a query to return how many rows are in the table." 
    )
prompt = make_llama_3_prompt(question)
print(llm.generate(prompt, max_new_tokens=200))
```


```python
question = """Given an arbitrary table named `sql_table`, 
help me calculate the average `height` where `age` is above 20."""
prompt = make_llama_3_prompt(question)
print(llm.generate(prompt, max_new_tokens=200))
```


```python
question = """Given an arbitrary table named `sql_table`, 
Can you calculate the p95 `height` where the `age` is above 20?"""
prompt = make_llama_3_prompt(question)
print(llm.generate(prompt, max_new_tokens=200))
```


```python
question = ("Given an arbitrary table named `sql_table`, "
            "Can you calculate the p95 `height` "
            "where the `age` is above 20? Use sqlite.")
prompt = make_llama_3_prompt(question)

print(llm.generate(prompt, max_new_tokens=200))
```
