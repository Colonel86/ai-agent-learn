# L6: Vector Quantization

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
        limit=50,
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

## Product Quantization (PQ)


```python
client.update_collection(
    "wands-products",
    quantization_config=models.ProductQuantization(
        product=models.ProductQuantizationConfig(
            compression=models.CompressionRatio.X64,
            always_ram=True,
        )    
    ),
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
import numpy as np

response_times = []
pq_run_dict = defaultdict(dict)
for id, row in queries_df.iterrows():
    query_id = f"query_{id}"

    # Measure the initial time
    start_time = time.monotonic()
    
    results = client.search(
        collection_name="wands-products",
        query_vector=models.NamedVector(
            name="product_name", 
            vector=row["query_embedding"]
        ),
        search_params=models.SearchParams(
            quantization=models.QuantizationSearchParams(
                rescore=False # Disable re-scoring using the original vectors
            )
        ),
        with_vectors=False,
        with_payload=False,
        limit=50,
    )

    # Store the response time in the list
    response_times.append(time.monotonic() - start_time)
    
    for point in results:
        document_id = f"doc_{point.id}"
        pq_run_dict[query_id][document_id] = point.score
    
np.mean(response_times)
```


```python
from ranx import Run, evaluate

product_name_pq_run = Run(
    pq_run_dict, 
    name="product_name_pq"
)
evaluate(
    qrels=qrels, 
    run=product_name_pq_run, 
    metrics=["precision@25"]
)
```


```python
response_times = []
pq_rescore_run_dict = defaultdict(dict)
for id, row in queries_df.iterrows():
    query_id = f"query_{id}"
    
    start_time = time.monotonic()
    
    results = client.search(
        collection_name="wands-products",
        query_vector=models.NamedVector(
            name="product_name", 
            vector=row["query_embedding"]
        ),
        search_params=models.SearchParams(
            quantization=models.QuantizationSearchParams(
                rescore=True # Enable re-scoring using the original vectors
            )
        ),
        with_vectors=False,
        with_payload=False,
        limit=50,
    )
    
    response_times.append(time.monotonic() - start_time)
    
    for point in results:
        document_id = f"doc_{point.id}"
        pq_rescore_run_dict[query_id][document_id] = point.score
    
np.mean(response_times)
```


```python
product_name_pq_rescore_run = Run(
    pq_rescore_run_dict,
    name="product_name_pq_rescore"
)
evaluate(
    qrels=qrels, 
    run=product_name_pq_rescore_run, 
    metrics=["precision@25"]
)
```

## Scalar Quantization (SQ)


```python
client.update_collection(
    "wands-products",
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            always_ram=True,
        )    
    ),
)
```


```python
time.sleep(1.0)
collection = client.get_collection("wands-products")
while collection.status != models.CollectionStatus.GREEN:
    time.sleep(1.0)
    collection = client.get_collection("wands-products")
    
collection
```


```python
response_times = []
sq_run_dict = defaultdict(dict)
for id, row in queries_df.iterrows():
    query_id = f"query_{id}"
    
    start_time = time.monotonic()
    
    results = client.search(
        collection_name="wands-products",
        query_vector=models.NamedVector(
            name="product_name", 
            vector=row["query_embedding"]
        ),
        search_params=models.SearchParams(
            quantization=models.QuantizationSearchParams(
                rescore=False # Disable re-scoring using the original vectors
            )
        ),
        with_vectors=False,
        with_payload=False,
        limit=50,
    )
    
    response_times.append(time.monotonic() - start_time)
    
    for point in results:
        document_id = f"doc_{point.id}"
        sq_run_dict[query_id][document_id] = point.score
    
np.mean(response_times)
```


```python
product_name_sq_run = Run(
    sq_run_dict, 
    name="product_name_sq"
)
evaluate(
    qrels=qrels, 
    run=product_name_sq_run, 
    metrics=["precision@25"]
)
```


```python
response_times = []
sq_rescore_run_dict = defaultdict(dict)
for id, row in queries_df.iterrows():
    query_id = f"query_{id}"
    
    start_time = time.monotonic()
    
    results = client.search(
        collection_name="wands-products",
        query_vector=models.NamedVector(
            name="product_name", 
            vector=row["query_embedding"]
        ),
        search_params=models.SearchParams(
            quantization=models.QuantizationSearchParams(
                rescore=True # Enable re-scoring using the original vectors
            )
        ),
        with_vectors=False,
        with_payload=False,
        limit=50,
    )
    
    response_times.append(time.monotonic() - start_time)
    
    for point in results:
        document_id = f"doc_{point.id}"
        sq_rescore_run_dict[query_id][document_id] = point.score
    
np.mean(response_times)
```


```python
product_name_sq_rescore_run = Run(
    sq_rescore_run_dict, 
    name="product_name_sq_rescore"
)
evaluate(
    qrels=qrels, 
    run=product_name_sq_rescore_run, 
    metrics=["precision@25"]
)
```

## Binary Quantization (BQ)


```python
client.update_collection(
    "wands-products",
    quantization_config=models.BinaryQuantization(
        binary=models.BinaryQuantizationConfig(
            always_ram=True,
        )    
    ),
)
```


```python
time.sleep(1.0)
collection = client.get_collection("wands-products")
while collection.status != models.CollectionStatus.GREEN:
    time.sleep(1.0)
    collection = client.get_collection("wands-products")
    
collection
```


```python
response_times = []
bq_run_dict = defaultdict(dict)
for id, row in queries_df.iterrows():
    query_id = f"query_{id}"
    
    start_time = time.monotonic()
    
    results = client.search(
        collection_name="wands-products",
        query_vector=models.NamedVector(
            name="product_name", 
            vector=row["query_embedding"]
        ),
        search_params=models.SearchParams(
            quantization=models.QuantizationSearchParams(
                rescore=False # Disable re-scoring using the original vectors
            )
        ),
        with_vectors=False,
        with_payload=False,
        limit=50,
    )
    
    response_times.append(time.monotonic() - start_time)
    
    for point in results:
        document_id = f"doc_{point.id}"
        bq_run_dict[query_id][document_id] = point.score
    
np.mean(response_times)
```


```python
product_name_bq_run = Run(
    bq_run_dict, 
    name="product_name_bq"
)
evaluate(
    qrels=qrels, 
    run=product_name_bq_run, 
    metrics=["precision@25"]
)
```


```python
response_times = []
bq_rescore_run_dict = defaultdict(dict)
for id, row in queries_df.iterrows():
    query_id = f"query_{id}"
    
    start_time = time.monotonic()
    
    results = client.search(
        collection_name="wands-products",
        query_vector=models.NamedVector(
            name="product_name", 
            vector=row["query_embedding"]
        ),
        search_params=models.SearchParams(
            quantization=models.QuantizationSearchParams(
                rescore=True # Enable re-scoring using the original vectors
            )
        ),
        with_vectors=False,
        with_payload=False,
        limit=50,
    )
    
    response_times.append(time.monotonic() - start_time)
    
    for point in results:
        document_id = f"doc_{point.id}"
        bq_rescore_run_dict[query_id][document_id] = point.score
    
np.mean(response_times)
```


```python
product_name_bq_rescore_run = Run(
    bq_rescore_run_dict, 
    name="product_name_bq_rescore"
)
evaluate(
    qrels=qrels, 
    run=product_name_bq_rescore_run, 
    metrics=["precision@25"]
)
```


```python
from ranx import compare

compare(
    qrels=qrels,
    runs=[
        product_name_pq_run, 
        product_name_pq_rescore_run, 
        product_name_sq_run, 
        product_name_sq_rescore_run, 
        product_name_bq_run, 
        product_name_bq_rescore_run,
    ],
    metrics=["precision@25"],
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
