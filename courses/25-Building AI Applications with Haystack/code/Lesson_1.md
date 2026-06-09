# L1: Haystack Building Blocks

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note <code>(Kernel Starting)</code>:</b> This notebook takes about 30 seconds to be ready to use. You may start and watch the video while you wait.</p>


```python
import warnings
warnings.filterwarnings('ignore')
```


```python
from helper import load_env
load_env()
```

<p style="background-color:#fff6ff; padding:15px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px"> 💻 &nbsp; <b>Access <code>requirements.txt</code> and <code>helper.py</code> files:</b> 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em>. For more help, please see the <em>"Appendix - Tips and Help"</em> Lesson.</p>

> **Note**: At time of recording, we are using haystack-ai==2.2.4 

To build any sort of AI application with Haystack, we combine Components [[+]](https://docs.haystack.deepset.ai/docs/components?utm_campaign=developer-relations&utm_source=dlai) into full Pipelines [[+]](https://docs.haystack.deepset.ai/docs/pipelines?utm_campaign=developer-relations&utm_source=dlai).

## Components


```python
from haystack.components.embedders import OpenAIDocumentEmbedder

embedder = OpenAIDocumentEmbedder(model="text-embedding-3-small")
```


```python
embedder
```


```python
from haystack.dataclasses import Document

documents = [Document(content="Haystack is an open source AI framework to build full AI applications in Python"),
             Document(content="You can build AI Pipelines by combining Components"),]

embedder.run(documents=documents)
```

## Pipelines
### Initialize a Document Store

Check out other available [Document Stores](https://docs.haystack.deepset.ai/docs/document-store?utm_campaign=developer-relations&utm_source=dlai). In this example, we will use the simplest document store that has no setup requirements, the [`InMemoryDocumentStore`](https://docs.haystack.deepset.ai/docs/inmemorydocumentstore?utm_campaign=developer-relations&utm_source=dlai).



```python
from haystack.document_stores.in_memory import InMemoryDocumentStore

document_store = InMemoryDocumentStore()
```

### Writing documents with embeddings into a document store



```python
from haystack import Pipeline

from haystack.components.converters.txt import TextFileToDocument
from haystack.components.preprocessors.document_splitter import DocumentSplitter
from haystack.components.embedders import OpenAIDocumentEmbedder
from haystack.components.writers import DocumentWriter

converter = TextFileToDocument()
splitter = DocumentSplitter()
embedder = OpenAIDocumentEmbedder()
writer = DocumentWriter(document_store=document_store)

indexing_pipeline = Pipeline()

indexing_pipeline.add_component("converter", converter)
indexing_pipeline.add_component("splitter", splitter)
indexing_pipeline.add_component("embedder", embedder)
indexing_pipeline.add_component("writer", writer)
```

#### Connecting Components


```python
indexing_pipeline.connect("converter", "splitter")
indexing_pipeline.connect("splitter", "embedder")
indexing_pipeline.connect("embedder", "writer")
```


```python
indexing_pipeline.show()
```

#### Running Pipelines



```python
indexing_pipeline.run({"converter": {"sources": ['data/davinci.txt']}})
```


```python
document_store.filter_documents()[5].content
```

### Creating a document search pipeline


```python
from haystack.components.embedders import OpenAITextEmbedder
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever

query_embedder = OpenAITextEmbedder()
retriever = InMemoryEmbeddingRetriever(document_store=document_store)

document_search = Pipeline()

document_search.add_component("query_embedder", query_embedder)
document_search.add_component("retriever", retriever)

document_search.connect("query_embedder.embedding", "retriever.query_embedding")
```


```python
document_search.show()
```


```python
question = "How old was Davinci when he died?"

results = document_search.run({"query_embedder": {"text": question}})

for i, document in enumerate(results["retriever"]["documents"]):
    print("\n--------------\n")
    print(f"DOCUMENT {i}")
    print(document.content)
```


```python
question = "How old was Davinci when he died?"

results = document_search.run({"query_embedder": {"text": question},
                               "retriever": {"top_k": 3}})

for i, document in enumerate(results["retriever"]["documents"]):
    print("\n--------------\n")
    print(f"DOCUMENT {i}")
    print(document.content)
```

**Next: Try changing the `top_k` for the retriever, or change the question:**
- Where was Davinci born?
- When did Davinci live in Rome?


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
