# Lesson 3: Prompting for structure and setting up a retry method 

In this notebook, you'll learn how to combine Pydantic with retry strategies to reliably extract structured output from an LLM.

By the end, you'll be able to:
- Define structured data models for LLM responses
- Build robust retry mechanisms for validation errors
- Create reusable functions for LLM interactions

---

### Import packages and initialize the OpenAI client


```python
# Import necessary packages
from pydantic import BaseModel, ValidationError, Field, EmailStr
from typing import List, Literal, Optional
import json
from datetime import date
from dotenv import load_dotenv
import openai
```


```python
# Load environment variables for API access
load_dotenv()
# Initialize OpenAI client for API calls
client = openai.OpenAI()
```

### Define some sample input data


```python
# Define a JSON string representing user input
user_input_json = '''
{
    "name": "Joe User",
    "email": "joe.user@example.com",
    "query": "I forgot my password.",
    "order_number": null,
    "purchase_date": null
}
'''
```

### Define your UserInput data model


```python
# Define UserInput model
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
```


```python
# Create UserInput instance from JSON data
user_input = UserInput.model_validate_json(user_input_json)
```

### Create a new data model called CustomerQuery


```python
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

### Construct a prompt with example output


```python
# Create a prompt with generic example data to guide LLM.
example_response_structure = f"""{{
    name="Example User",
    email="user@example.com",
    query="I ordered a new computer monitor and it arrived with the screen cracked. I need to exchange it for a new one.",
    order_id=12345,
    purchase_date="2025-12-31",
    priority="medium",
    category="refund_request",
    is_complaint=True,
    tags=["monitor", "support", "exchange"] 
}}"""
```


```python
# Create prompt with user data and expected JSON structure
prompt = f"""
Please analyze this user query\n {user_input.model_dump_json(indent=2)}:

Return your analysis as a JSON object matching this exact structure 
and data types:
{example_response_structure}

Respond ONLY with valid JSON. Do not include any explanations or 
other text or formatting before or after the JSON object.
"""

print(prompt)
```

### Define a function to call an LLM and try it with your prompt


```python
# Define a function to call the LLM
def call_llm(prompt, model="gpt-4o"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
```


```python
# Get response from LLM
response_content = call_llm(prompt)
print(response_content)
```

### Validate the LLM output using your CustomerQuery model

### Note: the following cell will produce a validation error. This is expected. You can simply proceed with the rest of the notebook as cells below do not depend on this cell. 


```python
# Attempt to parse the response into CustomerQuery model
valid_data = CustomerQuery.model_validate_json(response_content)
```

### Define a function for error handling


```python
# Define a function to validate an LLM response
def validate_with_model(data_model, llm_response):
    try:
        validated_data = data_model.model_validate_json(llm_response)
        print("data validation successful!")
        print(validated_data.model_dump_json(indent=2))
        return validated_data, None
    except ValidationError as e:
        print(f"error validating data: {e}")
        error_message = (
            f"This response generated a validation error: {e}."
        )
        return None, error_message
```


```python
# Test your validation function with the LLM response
validated_data, validation_error = validate_with_model(
    CustomerQuery, response_content
)
```

### Define a function to create a retry prompt including error details


```python
# Define a function to create a retry prompt with error feedback
def create_retry_prompt(
    original_prompt, original_response, error_message
):
    retry_prompt = f"""
This is a request to fix an error in the structure of an llm_response.
Here is the original request:
<original_prompt>
{original_prompt}
</original_prompt>

Here is the original llm_response:
<llm_response>
{original_response}
</llm_response>

This response generated an error: 
<error_message>
{error_message}
</error_message>

Compare the error message and the llm_response and identify what 
needs to be fixed or removed
in the llm_response to resolve this error. 

Respond ONLY with valid JSON. Do not include any explanations or 
other text or formatting before or after the JSON string.
"""
    return retry_prompt
```


```python
# Create a retry prompt for validation errors
validation_retry_prompt = create_retry_prompt(
    original_prompt=prompt,
    original_response=response_content,
    error_message=validation_error
)

print(validation_retry_prompt)
```

### Call the LLM with your retry prompt


```python
# Call the LLM with the validation retry prompt
validation_retry_response = call_llm(validation_retry_prompt)
print(validation_retry_response)
```


```python
# Attempt to validate retry response from LLM
validated_data, validation_error = validate_with_model(
    CustomerQuery, validation_retry_response
)
```

### Create a second retry prompt


```python
# Create a second retry prompt for validation errors
second_validation_retry_prompt = create_retry_prompt(
    original_prompt=validation_retry_prompt,
    original_response=validation_retry_response,
    error_message=validation_error
)

print(second_validation_retry_prompt)
```


```python
# Call the LLM with the second validation retry prompt
second_validation_retry_response = call_llm(
    second_validation_retry_prompt
)
print(second_validation_retry_response)
```

### Define a function to handle multiple retries in a feedback loop


```python
# Define a function to automatically retry an LLM call multiple times
def validate_llm_response(
    prompt, data_model, n_retry=5, model="gpt-4o"
):
    # Initial LLM call
    response_content = call_llm(prompt, model=model)
    current_prompt = prompt

    # Try to validate with the model
    # attempt: 0=initial, 1=first retry, ...
    for attempt in range(n_retry + 1):

        validated_data, validation_error = validate_with_model(
            data_model, response_content
        )

        if validation_error:
            if attempt < n_retry:
                print(f"retry {attempt} of {n_retry} failed, trying again...")
            else:
                print(f"Max retries reached. Last error: {validation_error}")
                return None, (
                    f"Max retries reached. Last error: {validation_error}"
                )

            validation_retry_prompt = create_retry_prompt(
                original_prompt=current_prompt,
                original_response=response_content,
                error_message=validation_error
            )
            response_content = call_llm(
                validation_retry_prompt, model=model
            )
            current_prompt = validation_retry_prompt
            continue

        # If you get here, both parsing and validation succeeded
        return validated_data, None
```


```python
# Test your complete solution with the original prompt
validated_data, error = validate_llm_response(
    prompt, CustomerQuery
)
```

### Have a look at the JSON schema of your CustomerQuery data model


```python
# Investigate the model_json_schema for CustomerQuery
data_model_schema = json.dumps(
    CustomerQuery.model_json_schema(), indent=2
)
print(data_model_schema)
```


```python
# Print the original prompt from above
print(prompt)
```

### Construct a new prompt using the JSON schema of your data model


```python
# Create new prompt with user input and model_json_schema
prompt = f"""
Please analyze this user query\n {user_input.model_dump_json(indent=2)}:

Return your analysis as a JSON object matching the following schema:
{data_model_schema}

Respond ONLY with valid JSON. Do not include any explanations or 
other text or formatting before or after the JSON object.
"""
```


```python
# Run your validate_llm_response function with the new prompt
final_analysis, error = validate_llm_response(
    prompt, CustomerQuery
)
```

---

## Conclusion

In this lesson, you explored how to combine Pydantic models with retry logic to reliably extract structured data from LLM outputs. You practiced building reusable validation functions and prompts, and saw how robust error handling can help you get consistent, usable results from language models. These techniques will help you confidently scale up your LLM-powered workflows.
