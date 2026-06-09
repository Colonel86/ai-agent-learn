# Lesson 3: Automating Model-Graded Evals


```python
import warnings
warnings.filterwarnings('ignore')
```

## Import the API keys for our 3rd party APIs.


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

Here is our sample application from the previous lesson that you will continue working on.



```python
!cat app.py
```

## A first model graded eval
Build a prompt that tells the LLM to evaluate the output of the quizzes.


```python
delimiter = "####"
```


```python
eval_system_prompt = f"""You are an assistant that evaluates \
  whether or not an assistant is producing valid quizzes.
  The assistant should be producing output in the \
  format of Question N:{delimiter} <question N>?"""
```

Simulate LLM response to make a first test.


```python
llm_response = """
Question 1:#### What is the largest telescope in space called and what material is its mirror made of?

Question 2:#### True or False: Water slows down the speed of light.

Question 3:#### What did Marie and Pierre Curie discover in Paris?
"""
```

Build the prompt for the evaluation (eval).


```python
eval_user_message = f"""You are evaluating a generated quiz \
based on the context that the assistant uses to create the quiz.
  Here is the data:
    [BEGIN DATA]
    ************
    [Response]: {llm_response}
    ************
    [END DATA]

Read the response carefully and determine if it looks like \
a quiz or test. Do not evaluate if the information is correct
only evaluate if the data is in the expected format.

Output Y if the response is a quiz, \
output N if the response does not look like a quiz.
"""
```

Use langchain to build the prompt template for evaluation.


```python
from langchain.prompts import ChatPromptTemplate
eval_prompt = ChatPromptTemplate.from_messages([
      ("system", eval_system_prompt),
      ("human", eval_user_message),
  ])
```

Choose an LLM.


```python
from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI(model="gpt-3.5-turbo",
                 temperature=0)
```

From langchain import a parser to have a readable response.


```python
from langchain.schema.output_parser import StrOutputParser
output_parser = StrOutputParser()
```

Connect all pieces together in the variable 'chain'.


```python
eval_chain = eval_prompt | llm | output_parser
```

Test the 'good LLM' with positive response by invoking the eval_chain.


```python
eval_chain.invoke({})
```

Create function 'create_eval_chain'.


```python
def create_eval_chain(
    agent_response,
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0),
    output_parser=StrOutputParser()
):
  delimiter = "####"
  eval_system_prompt = f"""You are an assistant that evaluates whether or not an assistant is producing valid quizzes.
  The assistant should be producing output in the format of Question N:{delimiter} <question N>?"""
  
  eval_user_message = f"""You are evaluating a generated quiz based on the context that the assistant uses to create the quiz.
  Here is the data:
    [BEGIN DATA]
    ************
    [Response]: {agent_response}
    ************
    [END DATA]

Read the response carefully and determine if it looks like a quiz or test. Do not evaluate if the information is correct
only evaluate if the data is in the expected format.

Output Y if the response is a quiz, output N if the response does not look like a quiz.
"""
  eval_prompt = ChatPromptTemplate.from_messages([
      ("system", eval_system_prompt),
      ("human", eval_user_message),
  ])

  return eval_prompt | llm | output_parser
```

Create new response to test in the eval_chain.


```python
known_bad_result = "There are lots of interesting facts. Tell me more about what you'd like to know"
```


```python
bad_eval_chain = create_eval_chain(known_bad_result)
```


```python
# response for wrong prompt
bad_eval_chain.invoke({})
```

Add new create_eval_chain into the 'test_assistant.py' file.


```python
!cat test_assistant.py
```


```python
# Command to see the content of the file
!cat test_release_evals.py
```

**_Note:_** if you want to inspect the config run `!head circle_config.yml`

Command: !cat circle_config.yml


Push new files into CircleCI's Git repo.


```python
from utils import push_files
push_files(course_repo, 
           course_branch, 
           ["app.py",
            "test_release_evals.py",
            "test_assistant.py"],
           config="circle_config.yml"
          )
```

Trigger the Release Evaluations.


```python
from utils import trigger_release_evals
trigger_release_evals(course_repo, 
                      course_branch, 
                      ["app.py",
                       "test_assistant.py",
                       "test_release_evals.py"],
                      cci_api_key)
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
