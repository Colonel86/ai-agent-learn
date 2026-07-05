# L1: Embedding Models

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note <code>(Kernel Starting)</code>:</b> This notebook takes about 30 seconds to be ready to use. You may start and watch the video while you wait.</p>


```python
import warnings
warnings.filterwarnings('ignore')
```


```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
model
```

<p style="background-color:#fff6ff; padding:15px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px"> 💻 &nbsp; <b>Access <code>requirements.txt</code> and <code>helper.py</code> files:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em>. For more help, please see the <em>"Appendix - Tips and Help"</em> Lesson.</p>


```python
tokenized_data = model.tokenize(["walker walked a long walk"])
tokenized_data
```


```python
model.tokenizer.convert_ids_to_tokens(tokenized_data["input_ids"][0])
```


```python
# Transformer consists of multiple stack modules. Tokens are an input
# of the first one, so we can ignore the rest.
first_module = model._first_module()
first_module.auto_model
```

## Input token embeddings


```python
embeddings = first_module.auto_model.embeddings
embeddings
```


```python
import torch
import plotly.express as px

device = torch.device("mps" if torch.has_mps else "cpu")  # Use MPS for Apple, CUDA for others, or fallback to CPU

first_sentence = "vector search optimization"
second_sentence = "we learn to apply vector search optimization"

with torch.no_grad():
    # Tokenize both texts
    first_tokens = model.tokenize([first_sentence])
    second_tokens = model.tokenize([second_sentence])
    
    # Get the corresponding embeddings
    first_embeddings = embeddings.word_embeddings(
        first_tokens["input_ids"].to(device)
    )
    second_embeddings = embeddings.word_embeddings(
        second_tokens["input_ids"].to(device)
    )

first_embeddings.shape, second_embeddings.shape
```


```python
from sentence_transformers import util

distances = util.cos_sim(
    first_embeddings.squeeze(), 
    second_embeddings.squeeze()
).cpu().numpy() # Move the tensor to the CPU and convert to a NumPy array

px.imshow(
    distances, 
    x=model.tokenizer.convert_ids_to_tokens(
        second_tokens["input_ids"][0]
    ),
    y=model.tokenizer.convert_ids_to_tokens(
        first_tokens["input_ids"][0]
    ),
    text_auto=True,
)
```

### Visualizing the input embeddings


```python
token_embeddings = first_module.auto_model \
    .embeddings \
    .word_embeddings \
    .weight \
    .detach() \
    .cpu() \
    .numpy()
token_embeddings.shape
```


```python
import random

vocabulary = first_module.tokenizer.get_vocab()
sorted_vocabulary = sorted(
    vocabulary.items(), 
    key=lambda x: x[1],  # uses the value of the dictionary entry
)
sorted_tokens = [token for token, _ in sorted_vocabulary]
random.choices(sorted_tokens, k=100)
```


```python
from sklearn.manifold import TSNE

tsne = TSNE(n_components=2, metric="cosine", random_state=42)
tsne_embeddings_2d = tsne.fit_transform(token_embeddings)
tsne_embeddings_2d.shape
```


```python
token_colors = []
for token in sorted_tokens:
    if token[0] == "[" and token[-1] == "]":
        token_colors.append("red")
    elif token.startswith("##"):
        token_colors.append("blue")
    else:
        token_colors.append("green")
```


```python
import plotly.graph_objs as go

scatter = go.Scattergl(
    x=tsne_embeddings_2d[:, 0], 
    y=tsne_embeddings_2d[:, 1],
    text=sorted_tokens,
    marker=dict(color=token_colors, size=3),
    mode="markers",
    name="Token embeddings",
)

fig = go.FigureWidget(
    data=[scatter],
    layout=dict(
        width=600,
        height=900,
        margin=dict(l=0, r=0),
    )
)

fig.show()
```

## Output token embeddings


```python
output_embedding = model.encode(["walker walked a long walk"])
output_embedding.shape
```


```python
output_token_embeddings = model.encode(
    ["walker walked a long walk"], 
    output_value="token_embeddings"
)
output_token_embeddings[0].shape
```


```python
first_sentence = "vector search optimization"
second_sentence = "we learn to apply vector search optimization"

with torch.no_grad():
    first_tokens = model.tokenize([first_sentence])
    second_tokens = model.tokenize([second_sentence])
    
    first_embeddings = model.encode(
        [first_sentence], 
        output_value="token_embeddings"
    )
    second_embeddings = model.encode(
        [second_sentence], 
        output_value="token_embeddings"
    )

distances = util.cos_sim(
    first_embeddings[0], 
    second_embeddings[0]
)
```


```python
px.imshow(
    distances.cpu().numpy(),  # Move the tensor to CPU and convert to a NumPy array
    x=model.tokenizer.convert_ids_to_tokens(
        second_tokens["input_ids"][0]
    ),
    y=model.tokenizer.convert_ids_to_tokens(
        first_tokens["input_ids"][0]
    ),
    text_auto=True,
)
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
