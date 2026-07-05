# L2: DSPy Programming - Signatures and Modules

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note <code>(Kernel Starting)</code>:</b> This notebook takes about 30 seconds to be ready to use. You may start and watch the video while you wait.</p>


```python
from helper import get_openai_api_key
openai_api_key = get_openai_api_key()

import os

os.environ["OPENAI_API_KEY"]  = get_openai_api_key()
```

<div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
<p> 💻 &nbsp; <b>Access <code>requirements.txt</code> and <code>helper.py</code> files:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em>.</p>

<p> ⬇ &nbsp; <b>Download Notebooks:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Download as"</em> and select <em>"Notebook (.ipynb)"</em>.</p>

<p> 📒 &nbsp; For more help, please see the <em>"Appendix – Tips, Help, and Download"</em> Lesson.</p>
</div>

### Set up API key


```python
from helper import get_openai_api_key
openai_api_key = get_openai_api_key()

import os

os.environ["OPENAI_API_KEY"] = get_openai_api_key()
```

### Configure the LM


```python
import dspy
dspy.settings.configure(lm=dspy.LM("openai/gpt-4o-mini"))
```

## Use DSPy built-in Module to Build a Sentiment Classifier


```python
class SentimentClassifier(dspy.Signature):
    """Classify the sentiment of a text."""

    text: str = dspy.InputField(desc="input text to classify sentiment")
    sentiment: int = dspy.OutputField(
        desc="sentiment, the higher the more positive", ge=0, le=10
    )
```


```python
str_signature = dspy.make_signature("text -> sentiment")
```

### Create a Module to Interact with the LM


```python
predict = dspy.Predict(SentimentClassifier) 
```


```python
output = predict(text="I am feeling pretty happy!")
print(output)
```


```python
print(f"The sentiment is: {output.sentiment}")
print(f"The sentiment is: {output['sentiment']}")
```


```python
dspy.configure(lm=dspy.LM("openai/gpt-4o"))
print(predict(text="I am feeling pretty happy!"))
```


```python
dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"))
```

### Wait, Where is My Prompt? 


```python
dspy.inspect_history(n=1)
```

### Try a Different Built-in Module


```python
cot = dspy.ChainOfThought(SentimentClassifier)

output = cot(text="I am feeling pretty happy!")
print(output)
```


```python
dspy.inspect_history(n=1)
```

### Use a Different Adapter


```python
dspy.configure(adapter=dspy.JSONAdapter())
```


```python
print(cot(text="I am feeling pretty happy!"))
dspy.inspect_history(n=1)
```

## Build a Program with Custom Module


```python
class QuestionGenerator(dspy.Signature):
    """Generate a yes or no question in order to guess the celebrity name in users' mind. You can ask in general or directly guess the name if you think the signal is enough. You should never ask the same question in the past_questions."""
    past_questions: list[str] = dspy.InputField(desc="past questions asked")
    past_answers: list[bool] = dspy.InputField(desc="past answers")
    new_question: str = dspy.OutputField(desc="new question that can help narrow down the celebrity name")
    guess_made: bool = dspy.OutputField(desc="If the new_question is the celebrity name guess, set to True, if it is still a general question set to False")


class Reflection(dspy.Signature):
    """Provide reflection on the guessing process"""
    correct_celebrity_name: str = dspy.InputField(desc="the celebrity name in user's mind")
    final_guessor_question: str = dspy.InputField(desc="the final guess or question LM made")
    past_questions: list[str] = dspy.InputField(desc="past questions asked")
    past_answers: list[bool] = dspy.InputField(desc="past answers")

    reflection: str = dspy.OutputField(
        desc="reflection on the guessing process, including what was done well and what can be improved"
    )

def ask(prompt, valid_responses=("y", "n")):
    while True:
        response = input(f"{prompt} ({'/'.join(valid_responses)}): ").strip().lower()
        if response in valid_responses:
            return response
        print(f"Please enter one of: {', '.join(valid_responses)}")

class CelebrityGuess(dspy.Module):
    def __init__(self, max_tries=10):
        super().__init__()

        self.question_generator = dspy.ChainOfThought(QuestionGenerator)
        self.reflection = dspy.ChainOfThought(Reflection)

        self.max_tries = 20

    def forward(self):
        celebrity_name = input("Please think of a celebrity name, once you are ready, type the name and press enter...")
        past_questions = []
        past_answers = []

        correct_guess = False

        for i in range(self.max_tries):
            question = self.question_generator(
                past_questions=past_questions,
                past_answers=past_answers,
            )
            answer = ask(f"{question.new_question}").lower() == "y"
            past_questions.append(question.new_question)
            past_answers.append(answer)

            if question.guess_made and answer:
                correct_guess = True
                break

        if correct_guess:
            print("Yay! I got it right!")
        else:
            print("Oops, I couldn't guess it right.")

        reflection = self.reflection(
            correct_celebrity_name=celebrity_name,
            final_guessor_question=question.new_question,
            past_questions=past_questions,
            past_answers=past_answers,
        )
        print(reflection.reflection)

```


```python
celebrity_guess = CelebrityGuess()
```


```python
celebrity_guess()
```

## Save and Load


```python
celebrity_guess.save("dspy_program/celebrity.json", save_program=False)
```


```python
celebrity_guess.load("dspy_program/celebrity.json")
```


```python
celebrity_guess.save("dspy_program/celebrity/", save_program=True)
```


```python
loaded = dspy.load("dspy_program/celebrity/")
```


```python
loaded()
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
