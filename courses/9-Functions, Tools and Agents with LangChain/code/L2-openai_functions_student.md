# OpenAI Function Calling


**Notes**:
- LLMs don't always produce the same results. The results you see in this notebook may differ from the results you see in the video.
- Notebooks results are temporary. Download the notebooks to your local machine if you wish to save your results.
- OpenAI has announced the release of an updated GPT-3.5-Turbo model and the deprecation of the ```gpt-3.5-turbo-0613``` model. The gpt-3.5-turbo-0613 model, which has been utilized in this Short Course since its launch in October 2023, will be replaced by the ```gpt-3.5-turbo``` model.


```python
import os
import openai

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']
```


```python
import json

# Example dummy function hard coded to return the same weather
# In production, this could be your backend API or an external API
def get_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    weather_info = {
        "location": location,
        "temperature": "72",
        "unit": unit,
        "forecast": ["sunny", "windy"],
    }
    return json.dumps(weather_info)
```


```python
# define a function
functions = [
    {
        "name": "get_current_weather",
        "description": "Get the current weather in a given location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    }
]
```


```python
messages = [
    {
        "role": "user",
        "content": "What's the weather like in Boston?"
    }
]
```


```python
import openai
```

> Note: This notebook was updated in June 2024. Consequently, we are now using the ```gpt-3.5-turbo model``` instead of the ```gpt-3.5-turbo-0613``` model featured by the instructor in the video lesson.


```python
# Call the ChatCompletion endpoint
response = openai.ChatCompletion.create(
    # OpenAI Updates: As of June 2024, we are now using the GPT-3.5-Turbo model
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions
)
```

> Note: The following result may differ slightly from the one shown by the instructor in the video lesson due to the model being updated.


```python
print(response)
```


```python
response_message = response["choices"][0]["message"]
```


```python
response_message
```


```python
response_message["content"]
```


```python
response_message["function_call"]
```


```python
json.loads(response_message["function_call"]["arguments"])
```


```python
args = json.loads(response_message["function_call"]["arguments"])
```


```python
get_current_weather(args)
```

* Pass a message that is not related to a function.


```python
messages = [
    {
        "role": "user",
        "content": "hi!",
    }
]
```

> Note: This notebook was updated in June 2024. Consequently, we are now using the ```gpt-3.5-turbo model``` instead of the ```gpt-3.5-turbo-0613``` model featured by the instructor in the video lesson.


```python
response = openai.ChatCompletion.create(
    # OpenAI Updates: As of June 2024, we are now using the GPT-3.5-Turbo model
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
)
```


```python
print(response)
```

* Pass additional parameters to force the model to use or not a function.


```python
messages = [
    {
        "role": "user",
        "content": "hi!",
    }
]
response = openai.ChatCompletion.create(
    # OpenAI Updates: As of June 2024, we are now using the GPT-3.5-Turbo model
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
    function_call="auto",
)
print(response)
```

* Use mode 'none' for function call.


```python
messages = [
    {
        "role": "user",
        "content": "hi!",
    }
]
response = openai.ChatCompletion.create(
    # OpenAI Updates: As of June 2024, we are now using the GPT-3.5-Turbo model
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
    function_call="none",
)
print(response)
```

* When the message should call a function and still uses mode 'none'.


```python
messages = [
    {
        "role": "user",
        "content": "What's the weather in Boston?",
    }
]
response = openai.ChatCompletion.create(
    # OpenAI Updates: As of June 2024, we are now using the GPT-3.5-Turbo model
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
    function_call="none",
)
print(response)
```

* Force calling a function.


```python
messages = [
    {
        "role": "user",
        "content": "hi!",
    }
]
response = openai.ChatCompletion.create(
    # OpenAI Updates: As of June 2024, we are now using the GPT-3.5-Turbo model
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
    function_call={"name": "get_current_weather"},
)
print(response)
```

* Final notes.


```python
messages = [
    {
        "role": "user",
        "content": "What's the weather like in Boston!",
    }
]
response = openai.ChatCompletion.create(
    # OpenAI Updates: As of June 2024, we are now using the GPT-3.5-Turbo model
    model="gpt-3.5-turbo",
    messages=messages,
    functions=functions,
    function_call={"name": "get_current_weather"},
)
print(response)
```


```python
messages.append(response["choices"][0]["message"])
```


```python
args = json.loads(response["choices"][0]["message"]['function_call']['arguments'])
observation = get_current_weather(args)
```


```python
messages.append(
        {
            "role": "function",
            "name": "get_current_weather",
            "content": observation,
        }
)
```


```python
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=messages,
)
print(response)
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


```python

```


```python

```
