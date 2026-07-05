# Lesson 2: Overview of Automated Evals


```python
import warnings
warnings.filterwarnings('ignore')
```

## Load API tokens for our 3rd party APIs.


```python
from utils import get_circle_api_key
cci_api_key = get_circle_api_key()
```


```python
from utils import get_gh_api_key
gh_api_key = get_gh_api_key()
```


```python
from utils import get_openai_api_key
openai_api_key = get_openai_api_key()
```

## Set up our github branch


```python
from utils import get_repo_name
course_repo = get_repo_name()
course_repo
```


```python
from utils import get_branch
course_branch = get_branch()
course_branch
```

## The sample application: AI-powered quiz generator
We are going to build a AI powered quiz generator.

Create the dataset for the quizz.


```python
human_template  = "{question}"
```


```python
quiz_bank = """1. Subject: Leonardo DaVinci
   Categories: Art, Science
   Facts:
    - Painted the Mona Lisa
    - Studied zoology, anatomy, geology, optics
    - Designed a flying machine
  
2. Subject: Paris
   Categories: Art, Geography
   Facts:
    - Location of the Louvre, the museum where the Mona Lisa is displayed
    - Capital of France
    - Most populous city in France
    - Where Radium and Polonium were discovered by scientists Marie and Pierre Curie

3. Subject: Telescopes
   Category: Science
   Facts:
    - Device to observe different objects
    - The first refracting telescopes were invented in the Netherlands in the 17th Century
    - The James Webb space telescope is the largest telescope in space. It uses a gold-berillyum mirror

4. Subject: Starry Night
   Category: Art
   Facts:
    - Painted by Vincent van Gogh in 1889
    - Captures the east-facing view of van Gogh's room in Saint-Rémy-de-Provence

5. Subject: Physics
   Category: Science
   Facts:
    - The sun doesn't change color during sunset.
    - Water slows the speed of light
    - The Eiffel Tower in Paris is taller in the summer than the winter due to expansion of the metal."""
```

Build the prompt template.


```python
delimiter = "####"

prompt_template = f"""
Follow these steps to generate a customized quiz for the user.
The question will be delimited with four hashtags i.e {delimiter}

The user will provide a category that they want to create a quiz for. Any questions included in the quiz
should only refer to the category.

Step 1:{delimiter} First identify the category user is asking about from the following list:
* Geography
* Science
* Art

Step 2:{delimiter} Determine the subjects to generate questions about. The list of topics are below:

{quiz_bank}

Pick up to two subjects that fit the user's category. 

Step 3:{delimiter} Generate a quiz for the user. Based on the selected subjects generate 3 questions for the user using the facts about the subject.

Use the following format for the quiz:
Question 1:{delimiter} <question 1>

Question 2:{delimiter} <question 2>

Question 3:{delimiter} <question 3>

"""
```

Use langchain to build the prompt template.


```python
from langchain.prompts import ChatPromptTemplate
chat_prompt = ChatPromptTemplate.from_messages([("human", prompt_template)])
```


```python
# print to observe the content or generated object
chat_prompt
```

Choose the LLM.


```python
from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
llm
```

Set up an output parser in LangChain that converts the llm response into a string.


```python
# parser
from langchain.schema.output_parser import StrOutputParser
output_parser = StrOutputParser()
output_parser
```

Connect the pieces using the pipe operator from Langchain Expression Language.


```python
chain = chat_prompt | llm | output_parser
chain
```

Build the function 'assistance_chain' to put together all steps above.


```python
# taking all components and making reusable as one piece
def assistant_chain(
    system_message,
    human_template="{question}",
    llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0),
    output_parser=StrOutputParser()):
  
  chat_prompt = ChatPromptTemplate.from_messages([
      ("system", system_message),
      ("human", human_template),
  ])
  return chat_prompt | llm | output_parser
```

### Evaluations

Create the function 'eval_expected_words' for the first example.


```python
def eval_expected_words(
    system_message,
    question,
    expected_words,
    human_template="{question}",
    llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0),
    output_parser=StrOutputParser()):
    
  assistant = assistant_chain(
      system_message,
      human_template,
      llm,
      output_parser)
    
  
  answer = assistant.invoke({"question": question})
    
  print(answer)
    
  assert any(word in answer.lower() \
             for word in expected_words), \
    f"Expected the assistant questions to include \
    '{expected_words}', but it did not"
```

Test: Generate a quiz about science.


```python
question  = "Generate a quiz about science."
expected_words = ["davinci", "telescope", "physics", "curie"]
```

Create the eval.


```python
eval_expected_words(
    prompt_template,
    question,
    expected_words
)
```

Create the function 'evaluate_refusal' to define a failing test case where the app should decline to answer.


```python
def evaluate_refusal(
    system_message,
    question,
    decline_response,
    human_template="{question}", 
    llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0),
    output_parser=StrOutputParser()):
    
  assistant = assistant_chain(human_template, 
                              system_message,
                              llm,
                              output_parser)
  
  answer = assistant.invoke({"question": question})
  print(answer)
  
  assert decline_response.lower() in answer.lower(), \
    f"Expected the bot to decline with \
    '{decline_response}' got {answer}"
```

Define a new question (which should be a bad request)


```python
question  = "Generate a quiz about Rome."
decline_response = "I'm sorry"
```

Create the refusal eval.

<p style="background-color:pink; padding:15px;"> <b>Note:</b> The following function call will throw an exception.</p>



```python
evaluate_refusal(
    prompt_template,
    question,
    decline_response
)
```

## Running evaluations in a CircleCI pipeline

Put all these steps together into files to reuse later.

**_Note:_** fixing the system_message by adding additional rules:

- Only use explicit matches for the category, if the category is not an exact match to categories in the quiz bank, answer that you do not have information.
- If the user asks a question about a subject you do not have information about in the quiz bank, answer "I'm sorry I do not have information about that".


```python
%%writefile app.py
from langchain.prompts                import ChatPromptTemplate
from langchain.chat_models            import ChatOpenAI
from langchain.schema.output_parser   import StrOutputParser

delimiter = "####"

quiz_bank = """1. Subject: Leonardo DaVinci
   Categories: Art, Science
   Facts:
    - Painted the Mona Lisa
    - Studied zoology, anatomy, geology, optics
    - Designed a flying machine
  
2. Subject: Paris
   Categories: Art, Geography
   Facts:
    - Location of the Louvre, the museum where the Mona Lisa is displayed
    - Capital of France
    - Most populous city in France
    - Where Radium and Polonium were discovered by scientists Marie and Pierre Curie

3. Subject: Telescopes
   Category: Science
   Facts:
    - Device to observe different objects
    - The first refracting telescopes were invented in the Netherlands in the 17th Century
    - The James Webb space telescope is the largest telescope in space. It uses a gold-berillyum mirror

4. Subject: Starry Night
   Category: Art
   Facts:
    - Painted by Vincent van Gogh in 1889
    - Captures the east-facing view of van Gogh's room in Saint-Rémy-de-Provence

5. Subject: Physics
   Category: Science
   Facts:
    - The sun doesn't change color during sunset.
    - Water slows the speed of light
    - The Eiffel Tower in Paris is taller in the summer than the winter due to expansion of the metal.
"""

system_message = f"""
Follow these steps to generate a customized quiz for the user.
The question will be delimited with four hashtags i.e {delimiter}

The user will provide a category that they want to create a quiz for. Any questions included in the quiz
should only refer to the category.

Step 1:{delimiter} First identify the category user is asking about from the following list:
* Geography
* Science
* Art

Step 2:{delimiter} Determine the subjects to generate questions about. The list of topics are below:

{quiz_bank}

Pick up to two subjects that fit the user's category. 

Step 3:{delimiter} Generate a quiz for the user. Based on the selected subjects generate 3 questions for the user using the facts about the subject.

Use the following format for the quiz:
Question 1:{delimiter} <question 1>

Question 2:{delimiter} <question 2>

Question 3:{delimiter} <question 3>

Additional rules:

- Only use explicit matches for the category, if the category is not an exact match to categories in the quiz bank, answer that you do not have information.
- If the user asks a question about a subject you do not have information about in the quiz bank, answer "I'm sorry I do not have information about that".
"""

"""
  Helper functions for writing the test cases
"""

def assistant_chain(
    system_message=system_message,
    human_template="{question}",
    llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0),
    output_parser=StrOutputParser()):

  chat_prompt = ChatPromptTemplate.from_messages([
      ("system", system_message),
      ("human", human_template),
  ])
  return chat_prompt | llm | output_parser

```

Command to see the content:


```python
!cat app.py
```

Create new file to include the evals.


```python
%%writefile test_assistant.py
from app import assistant_chain
from app import system_message
from langchain.prompts                import ChatPromptTemplate
from langchain.chat_models            import ChatOpenAI
from langchain.schema.output_parser   import StrOutputParser

import os

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())

def eval_expected_words(
    system_message,
    question,
    expected_words,
    human_template="{question}",
    llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0),
    output_parser=StrOutputParser()):

  assistant = assistant_chain(system_message)
  answer = assistant.invoke({"question": question})
  print(answer)
    
  assert any(word in answer.lower() \
             for word in expected_words), \
    f"Expected the assistant questions to include \
    '{expected_words}', but it did not"

def evaluate_refusal(
    system_message,
    question,
    decline_response,
    human_template="{question}", 
    llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0),
    output_parser=StrOutputParser()):
    
  assistant = assistant_chain(human_template, 
                              system_message,
                              llm,
                              output_parser)
  
  answer = assistant.invoke({"question": question})
  print(answer)
  
  assert decline_response.lower() in answer.lower(), \
    f"Expected the bot to decline with \
    '{decline_response}' got {answer}"

"""
  Test cases
"""

def test_science_quiz():
  
  question  = "Generate a quiz about science."
  expected_subjects = ["davinci", "telescope", "physics", "curie"]
  eval_expected_words(
      system_message,
      question,
      expected_subjects)

def test_geography_quiz():
  question  = "Generate a quiz about geography."
  expected_subjects = ["paris", "france", "louvre"]
  eval_expected_words(
      system_message,
      question,
      expected_subjects)

def test_refusal_rome():
  question  = "Help me create a quiz about Rome"
  decline_response = "I'm sorry"
  evaluate_refusal(
      system_message,
      question,
      decline_response)
```

Command to see the content of the file:


```python
!cat test_assistant.py
```

### The CircleCI config file
Now let's set up our tests to run automatically in CircleCI.

For this course, we've created a working CircleCI config file. Let's take a look at the configuration.



```python
!cat circle_config.yml
```

## Run the per-commit evals
Push files into the github repo.


```python
from utils import push_files
push_files(course_repo, course_branch, ["app.py", "test_assistant.py"])
```

Trigger the pipeline in CircleCI pipeline.


```python
from utils import trigger_commit_evals
trigger_commit_evals(course_repo, course_branch, cci_api_key)
```


```python

```
