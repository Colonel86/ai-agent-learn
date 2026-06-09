# Lesson 2: RAG Triad of metrics


```python
import warnings
warnings.filterwarnings('ignore')
```


```python
import utils

import os
import openai
openai.api_key = utils.get_openai_api_key()
```


```python
from trulens_eval import Tru

tru = Tru()
tru.reset_database()
```


```python
from llama_index import SimpleDirectoryReader

documents = SimpleDirectoryReader(
    input_files=["./eBook-How-to-Build-a-Career-in-AI.pdf"]
).load_data()
```


```python
from llama_index import Document

document = Document(text="\n\n".\
                    join([doc.text for doc in documents]))
```


```python
from utils import build_sentence_window_index

from llama_index.llms import OpenAI

llm = OpenAI(model="gpt-3.5-turbo", temperature=0.1)

sentence_index = build_sentence_window_index(
    document,
    llm,
    embed_model="local:BAAI/bge-small-en-v1.5",
    save_dir="sentence_index"
)
```


```python
from utils import get_sentence_window_query_engine

sentence_window_engine = \
get_sentence_window_query_engine(sentence_index)
```


```python
output = sentence_window_engine.query(
    "How do you create your AI portfolio?")
output.response
```

## Feedback functions


```python
import nest_asyncio

nest_asyncio.apply()
```


```python
from trulens_eval import OpenAI as fOpenAI

provider = fOpenAI()
```

### 1. Answer Relevance


```python
from trulens_eval import Feedback

f_qa_relevance = Feedback(
    provider.relevance_with_cot_reasons,
    name="Answer Relevance"
).on_input_output()
```

### 2. Context Relevance


```python
from trulens_eval import TruLlama

context_selection = TruLlama.select_source_nodes().node.text
```


```python
import numpy as np

f_qs_relevance = (
    Feedback(provider.qs_relevance,
             name="Context Relevance")
    .on_input()
    .on(context_selection)
    .aggregate(np.mean)
)
```


```python
import numpy as np

f_qs_relevance = (
    Feedback(provider.qs_relevance_with_cot_reasons,
             name="Context Relevance")
    .on_input()
    .on(context_selection)
    .aggregate(np.mean)
)
```

### 3. Groundedness


```python
from trulens_eval.feedback import Groundedness

grounded = Groundedness(groundedness_provider=provider)
```


```python
f_groundedness = (
    Feedback(grounded.groundedness_measure_with_cot_reasons,
             name="Groundedness"
            )
    .on(context_selection)
    .on_output()
    .aggregate(grounded.grounded_statements_aggregator)
)
```

## Evaluation of the RAG application


```python
from trulens_eval import TruLlama
from trulens_eval import FeedbackMode

tru_recorder = TruLlama(
    sentence_window_engine,
    app_id="App_1",
    feedbacks=[
        f_qa_relevance,
        f_qs_relevance,
        f_groundedness
    ]
)
```


```python
eval_questions = []
with open('eval_questions.txt', 'r') as file:
    for line in file:
        # Remove newline character and convert to integer
        item = line.strip()
        eval_questions.append(item)
```


```python
eval_questions
```


```python
eval_questions.append("How can I be successful in AI?")
```


```python
eval_questions
```


```python
for question in eval_questions:
    with tru_recorder as recording:
        sentence_window_engine.query(question)
```


```python
records, feedback = tru.get_records_and_feedback(app_ids=[])
records.head()
```


```python
import pandas as pd

pd.set_option("display.max_colwidth", None)
records[["input", "output"] + feedback]
```


```python
tru.get_leaderboard(app_ids=[])
```


```python
tru.run_dashboard()
```
