# L4: Optimize DSPy Agent with DSPy Optimizer

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note <code>(Kernel Starting)</code>:</b> This notebook takes about 30 seconds to be ready to use. You may start and watch the video while you wait.</p>


```python
from helper import get_openai_api_key
openai_api_key = get_openai_api_key()

import os

os.environ["OPENAI_API_KEY"] = get_openai_api_key()
```

<div style="background-color:#fff6ff; padding:13px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px">
<p> 💻 &nbsp; <b>Access <code>requirements.txt</code> and <code>helper.py</code> files:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em>.</p>

<p> ⬇ &nbsp; <b>Download Notebooks:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Download as"</em> and select <em>"Notebook (.ipynb)"</em>.</p>

<p> 📒 &nbsp; For more help, please see the <em>"Appendix – Tips, Help, and Download"</em> Lesson.</p>
</div>


```python
import mlflow
```


```python
from helper import get_mlflow_tracking_uri

mlflow_tracking_uri = get_mlflow_tracking_uri()
mlflow.set_tracking_uri(mlflow_tracking_uri)
```


```python
mlflow.set_experiment("dspy_course_4")
```


```python
mlflow.dspy.autolog(log_evals=True, log_compiles=True, log_traces_from_compile=True)
```


```python
import dspy

dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"))
```

## Build a RAG Agent


```python
def search_wikipedia(query: str) -> list[str]:
    results = dspy.ColBERTv2(url="http://20.102.90.50:2017/wiki17_abstracts")(query, k=3)
    return [x["text"] for x in results]

react = dspy.ReAct("question -> answer", tools=[search_wikipedia])
```


```python
import json

# Load trainset
trainset = []
with open("trainset.jsonl", "r") as f:
    for line in f:
        trainset.append(dspy.Example(**json.loads(line)).with_inputs("question"))

# Load valset
valset = []
with open("valset.jsonl", "r") as f:
    for line in f:
        valset.append(dspy.Example(**json.loads(line)).with_inputs("question"))
```


```python
# Overview of the dataset.
print(trainset[0])
```


```python
tp = dspy.MIPROv2(
    metric=dspy.evaluate.answer_exact_match,
    auto="light",
    num_threads=16
)
```


```python
dspy.cache.load_memory_cache("./memory_cache.pkl")
```


```python
optimized_react = tp.compile(
    react,
    trainset=trainset,
    valset=valset,
    requires_permission_to_run=False,
)
```


```python
optimized_react.react.signature
```


```python
optimized_react.react.demos
```


```python
evaluator = dspy.Evaluate(
    metric=dspy.evaluate.answer_exact_match,
    devset=valset,
    display_table=True,
    display_progress=True,
    num_threads=24,
)
```


```python
original_score = evaluator(react)
print(f"Original score: {original_score}")
```


```python
optimized_score = evaluator(optimized_react)
print(f"Optimized score: {optimized_score}")
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
