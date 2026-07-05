# L5: Optimizing HNSW Search

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note <code>(Kernel Starting)</code>:</b> This notebook takes about 30 seconds to be ready to use. You may start and watch the video while you wait.</p>


```python
import warnings
warnings.filterwarnings('ignore')
```

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note <code>(Loading the collection)</code>:</b> The following code block might take a few minutes to complete.</p>


```python
from qdrant_client import QdrantClient, models

client = QdrantClient("http://localhost:6333", timeout=600)
client.delete_collection("wands-products")
client.recover_snapshot(
    "wands-products", 
    "https://dlai-course-resource.s3.us-west-2.amazonaws.com/qdrant-c1/wands-products.snapshot",
)
collection = client.get_collection("wands-products")
collection
```

<p style="background-color:#fff6ff; padding:15px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px"> 💻 &nbsp; <b>Access <code>requirements.txt</code> and <code>helper.py</code> files:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em>. For more help, please see the <em>"Appendix - Tips and Help"</em> Lesson.</p>

## HNSW parameters


```python
collection.config.hnsw_config
```

## Test queries


```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
```


```python
import pandas as pd

queries_df = pd.read_csv(
    "shared_data/WANDS/query.csv", 
    sep="\t", 
    index_col="query_id",
)
queries_df["query_embedding"] = model.encode(
    queries_df["query"].tolist()
).tolist()
queries_df.sample(n=5)
```

## ANN search


```python
client.search(
    "wands-products",
    query_vector=models.NamedVector(
        name="product_name",
        vector=model.encode(queries_df.loc[0, "query"])
    ),
    limit=3,
    with_vectors=False,
    with_payload=False,
)
```

## kNN search


```python
client.search(
    "wands-products",
    query_vector=models.NamedVector(
        name="product_name",
        vector=model.encode(queries_df.loc[0, "query"])
    ),
    limit=3,
    with_vectors=False,
    with_payload=False,
    search_params=models.SearchParams(
        exact=True,  # Turns on the exact search mode
    ),
)
```

### Ground truth


```python
from collections import defaultdict
from ranx import Qrels

knn_qrels_dict = defaultdict(dict)
for id, row in queries_df.iterrows():
    query_id = f"query_{id}"
    
    results = client.search(
        collection_name="wands-products",
        query_vector=models.NamedVector(
            name="product_name", 
            vector=row["query_embedding"]
        ),
        with_vectors=False,
        with_payload=False,
        limit=100,
        search_params=models.SearchParams(
            exact=True,  # enable exact search
        ),
    )
    
    for point in results:
        document_id = f"doc_{point.id}"
        # The conversion to integer is required because ranx expects integers
        knn_qrels_dict[query_id][document_id] = int(point.score * 100)
    
qrels = Qrels(knn_qrels_dict)
qrels
```

### ANN search


```python
from ranx import Run

run_dict = defaultdict(dict)
for id, row in queries_df.iterrows():
    query_id = f"query_{id}"
    
    results = client.search(
        collection_name="wands-products",
        query_vector=models.NamedVector(
            name="product_name", 
            vector=row["query_embedding"]
        ),
        with_vectors=False,
        with_payload=False,
        limit=100,
        search_params=models.SearchParams(
            exact=False,  # disable exact search
        ),
    )
    
    for point in results:
        document_id = f"doc_{point.id}"
        run_dict[query_id][document_id] = point.score

initial_run = Run(
    run_dict, 
    name="initial",
)
initial_run
```


```python
from ranx import evaluate

evaluate(
    qrels=qrels, 
    run=initial_run, 
    metrics=["precision@25"]
)
```

## Tweaking the HNSW parameters


```python
client.update_collection(
    collection_name="wands-products",
    hnsw_config=models.HnswConfigDiff(
        m=64, 
        ef_construct=200,
    )
)
```


```python
import time

time.sleep(1.0)
collection = client.get_collection("wands-products")
while collection.status != models.CollectionStatus.GREEN:
    time.sleep(1.0)
    collection = client.get_collection("wands-products")
    
collection
```


```python
tweaked_run_dict = defaultdict(dict)
for id, row in queries_df.iterrows():
    query_id = f"query_{id}"
    
    results = client.search(
        collection_name="wands-products",
        query_vector=models.NamedVector(
            name="product_name", 
            vector=row["query_embedding"]
        ),
        with_vectors=False,
        with_payload=False,
        limit=100,
        search_params=models.SearchParams(
            exact=False,  # disable exact search
        ),
    )
    
    for point in results:
        document_id = f"doc_{point.id}"
        tweaked_run_dict[query_id][document_id] = point.score
    
tweaked_run = Run(
    tweaked_run_dict, 
    name="tweaked"
)
tweaked_run
```


```python
evaluate(
    qrels=qrels, 
    run=tweaked_run, 
    metrics=["precision@25"]
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
