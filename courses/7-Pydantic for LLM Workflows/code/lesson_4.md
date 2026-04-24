# Lesson 4: Using Pydantic Models for Structured LLM Output

In the previous lesson, you implemented retry mechanisms to handle validation errors, which mimics what some structured output frameworks are doing behind the scenes when they handle validation for you.

In this lesson, you'll experiment with passing you Pydantic model directly in your API call using different frameworks and LLM providers.

By the end of this lesson, you'll be able to:
- Use Pydantic models directly in your API calls to LLMs
- Reliably receive a properly structured response using a variety of different frameworks and LLM providers.

---

### Import all required libraries and set up your environment


```python
# Import packages
from pydantic import BaseModel, Field, EmailStr
from typing import List, Literal, Optional
from openai import OpenAI
import instructor
import anthropic
from dotenv import load_dotenv
from datetime import date
```

### Define your Pydantic models for user input and LLM output


```python
# Define the UserInput model for customer support queries
class UserInput(BaseModel):
    name: str
    email: EmailStr
    query: str
    order_id: Optional[int] = Field(
        None,
        description="5-digit order number (cannot start with 0)",
        ge=10000,
        le=99999
    )
    purchase_date: Optional[date] = None

# Define the CustomerQuery model that inherits from UserInput
class CustomerQuery(UserInput):
    priority: str = Field(
        ..., description="Priority level: low, medium, high"
    )
    category: Literal[
        'refund_request', 'information_request', 'other'
    ] = Field(..., description="Query category")
    is_complaint: bool = Field(
        ..., description="Whether this is a complaint"
    )
    tags: List[str] = Field(..., description="Relevant keyword tags")
```

### Provide sample input and validate it using your model


```python
# Define your input data as a JSON string
user_input_json = '''{
    "name": "Joe User",
    "email": "joe.user@example.com",
    "query": "I ordered a new computer monitor and it arrived with the screen cracked. This is the second time this has happened. I need a replacement ASAP.",
    "order_number": 12345,
    "purchase_date": "2025-12-31"
}'''
```


```python
# Validate the user_input_json by creating a UserInput instance
user_input = UserInput.model_validate_json(user_input_json)
```

### Build a prompt and call the Anthropic API with the instructor package for structured output


```python
prompt = (
    f"Analyze the following customer query {user_input} "
    f"and provide a structured response."
)
```


```python
# Load environment variables
load_dotenv()
# Use Anthropic with Instructor to get structured output
anthropic_client = instructor.from_anthropic(
    anthropic.Anthropic()
)

response = anthropic_client.messages.create(
    model="claude-3-7-sonnet-latest",  
    max_tokens=1024,
    messages=[
        {
            "role": "user", 
            "content": prompt
        }
    ],
    response_model=CustomerQuery  
)
```


```python
# Inspect the returned structured data
print(type(response))
print(response.model_dump_json(indent=2))
```

### Use OpenAI's structured output API with your Pydantic schema


```python
# Initialize OpenAI client and call passing CustomerQuery in your API call
openai_client = OpenAI()
response = openai_client.beta.chat.completions.parse(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    response_format=CustomerQuery
)
response_content = response.choices[0].message.content
print(type(response_content))
print(response_content)
```

### Additional advanced usage and inspection


```python
# Validate the repsonse you got from the LLM
valid_data = CustomerQuery.model_validate_json(
    response_content
)
print(type(valid_data))
print(valid_data.model_dump_json(indent=2))
```


```python
# Try the responses API from OpenAI
response = openai_client.responses.parse(
    model="gpt-4o",
    input=[{"role": "user", "content": prompt}],
    text_format=CustomerQuery
)

print(type(response))
```


```python
# Investigate class inheritance structure of the OpenAI response
def print_class_inheritence(llm_response):
    for cls in type(llm_response).mro():
        print(f"{cls.__module__}.{cls.__name__}")

print_class_inheritence(response)
```


```python
# Print the response type and content 
print(type(response.output_parsed))
print(response.output_parsed.model_dump_json(indent=2))
```


```python
# Try out the Pydantic AI package for defining an agent and getting a structured response
from pydantic_ai import Agent
import nest_asyncio
nest_asyncio.apply()

agent = Agent(
    model="google-gla:gemini-2.0-flash",
    output_type=CustomerQuery,
)

response = agent.run_sync(prompt)
```


```python
# Print out the repsonse type and content
print(type(response.output))
print(response.output.model_dump_json(indent=2))
```

---

## Conclusion

In this lesson, you learned how to use Pydantic models to extract structured, validated output directly from LLMs using both OpenAI and Anthropic APIs. By defining your expected output schema with Pydantic and passing it directly to the API, you can eliminate manual parsing and validation code and receive reliable, well-formed responses in a single API call. This approach lets you focus on designing clear data models and prompts, making your code more maintainable and robust.
