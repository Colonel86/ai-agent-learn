# Lesson 2: Pydantic Basics

In this lesson, you'll learn the fundamentals of Pydantic models for data validation using a customer support system as your example application. You'll see how to define data models, validate user input, and handle validation errors gracefully.

By the end of this lesson, you'll be able to:
- Create Pydantic models to validate user input data
- Handle validation errors with proper error handling
- Use optional fields and field constraints in your models
- Work with JSON data validation methods

---


```python
# Import libraries needed for the lesson
from pydantic import BaseModel, ValidationError, EmailStr
import json
```

### Define a UserInput Pydantic model and populate it with data


```python
# Create a Pydantic model for validating user input
class UserInput(BaseModel):
    name: str
    email: EmailStr
    query: str
```


```python
# Create a model instance
user_input = UserInput(
    name="Joe User", 
    email="joe.user@example.com", 
    query="I forgot my password."
)
print(user_input)
```

### Note: the following cell will produce a validation error. You can correct the error by following along with the video, or just proceed with the rest of the notebook as cells below do not depend on this cell. 


```python
# Attempt to create another model instance with an invalid email
user_input = UserInput(
    name="Joe User", 
    email="not-an-email", 
    query="I forgot my password."
)
print(user_input)
```

### Define a function for error handling and try different inputs


```python
# Define a function to handle user input validation safely
def validate_user_input(input_data):
    try:
        # Attempt to create a UserInput model instance from user input data
        user_input = UserInput(**input_data)
        print(f"✅ Valid user input created:")
        print(f"{user_input.model_dump_json(indent=2)}")
        return user_input
    except ValidationError as e:
        # Capture and display validation errors in a readable format
        print(f"❌ Validation error occurred:")
        for error in e.errors():
            print(f"  - {error['loc'][0]}: {error['msg']}")
        return None
```


```python
# Create an instance of UserInput using validate_user_input() function
input_data = {
    "name": "Joe User", 
    "email": "joe.user@example.com",
    "query": "I forgot my password."
}

user_input = validate_user_input(input_data)
```


```python
# Attempt to create an instance of UserInput with missing query field
input_data = {
    "name": "Joe User", 
    "email": "joe.user@example.com"
}

user_input = validate_user_input(input_data)
```

### Update your UserInput data model with additional fields and experiment with different input data


```python
# Import additional libraries for enhanced validation
from pydantic import Field
from typing import Optional
from datetime import date

# Define a new UserInput model with optional fields
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
# Define a dictionary with required fields only
input_data = {
    "name": "Joe User",
    "email": "joe.user@example.com",
    "query": "I forgot my password."
}

# Validate the user input data
user_input = validate_user_input(input_data)
```


```python
print(user_input)
```


```python
# Define a dictionary with all fields including optional ones
input_data = {
    "name": "Joe User",
    "email": "joe.user@example.com",
    "query": f"""I bought a laptop carrying case and it turned out to be 
             the wrong size. I need to return it.""",
    "order_id": 12345,
    "purchase_date": date(2025, 12, 31)
}

# Validate the user input data
user_input = validate_user_input(input_data)
```


```python
# Define a dictionary with all fields and including additional ones
input_data = {
    "name": "Joe User",
    "email": "joe.user@example.com",
    "query": f"""I bought a laptop carrying case and it turned out to be 
             the wrong size. I need to return it.""",
    "order_id": 12345,
    "purchase_date": date(2025, 12, 31),
    "system_message": "logging status regarding order processing...",
    "iteration": 1 
}

# Validate the user input data
user_input = validate_user_input(input_data)
```


```python
print(user_input)
```


```python
# Create an instance of UserInput with valid data
input_data = {
    "name": "Joe User",
    "email": "joe.user@example.com",
    "query": f"""I bought a laptop carrying case and it turned out to be 
             the wrong size. I need to return it.""",
    "order_id": 12345,
    "purchase_date": "2025-12-31"
}

user_input = validate_user_input(input_data)
```


```python
# Define order_id as a string
input_data = {
    "name": "Joe User",
    "email": "joe.user@example.com",
    "query": f"""I bought a laptop carrying case and it turned out to be 
             the wrong size. I need to return it.""",
    "order_id": "12345",
    "purchase_date": "2025-12-31"
}

# Validate the user input data
user_input = validate_user_input(input_data)
```


```python
# Define name field as an integer
input_data = {
    "name": 99999,
    "email": "joe.user@example.com",
    "query": f"""I bought a laptop carrying case and it turned out to be 
             the wrong size. I need to return it.""",
    "order_id": 12345,
    "purchase_date": "2025-12-31"
}

# Validate the user input data
user_input = validate_user_input(input_data)
```

### Try starting with JSON data as input


```python
# Define user input as JSON data
json_data = '''
{
    "name": "Joe User",
    "email": "joe.user@example.com",
    "query": "I bought a keyboard and mouse and was overcharged.",
    "order_id": 12345,
    "purchase_date": "2025-12-31"
}
'''

# Parse the JSON string into a Python dictionary
input_data = json.loads(json_data)
print("Parsed JSON:", input_data)
```


```python
# Validate the user iput data
user_input = validate_user_input(input_data)
```


```python
# Try different JSON input
json_data = '''
{
    "name": "Joe User",
    "email": "joe.user@example.com",
    "query": "My account has been locked for some reason.",
    "order_id": "01234",
    "purchase_date": "2025-12-31"
}
'''

# Parse the JSON into a Python dictionary
input_data = json.loads(json_data)
print("Parsed JSON:", input_data)
```


```python
# Validate the customer support data from JSON with non-standard formats
user_input = validate_user_input(input_data)
```

### Try the `model_validate_json` method

### Note: the following cell will produce a validation error. You can correct the error by following along with the video. 


```python
# Parse JSON and validate user input data in one step using model_validate_json method
user_input = UserInput.model_validate_json(json_data)
print(user_input.model_dump_json(indent=2))
```

---

## Conclusion

In this lesson, you learned how to use Pydantic models to validate user input for a customer support scenario. By defining clear data models and handling validation errors, you can ensure your code only works with well-formed data. This approach helps you build more robust and reliable applications, and sets the stage for more advanced validation and structured output in future lessons.
