# L2: Filtering With Metadata

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note <code>(Kernel Starting)</code>:</b> This notebook takes about 30 seconds to be ready to use. You may start and watch the video while you wait.</p>



```python
# Warning control
import warnings
warnings.filterwarnings('ignore')
```


```python
import custom_utils
```

<p style="background-color:#fff6ff; padding:15px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px"> 💻 &nbsp; <b>Access <code>requirements.txt</code> and <code>utils</code> files:</b> To access <code>requirements.txt</code> for this notebook, 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em>. For more help, please see the <em>"Appendix - Tips and Help"</em> Lesson.</p>

## Data Loading


```python
# 1. Dataset Loading
from datasets import load_dataset
import pandas as pd

dataset = load_dataset("MongoDB/airbnb_embeddings", streaming=True, split="train")
dataset = dataset.take(100)
# Convert the dataset to a pandas dataframe
dataset_df = pd.DataFrame(dataset)
dataset_df.head(5)
```


```python
print("Columns:", dataset_df.columns)
```

## Document Modelling


```python
listings = custom_utils.process_records(dataset_df)
```

## Database Creation and Connection


```python
db, collection = custom_utils.connect_to_database()
```


```python
# Delete any existing records in the collection
collection.delete_many({})
```

## Data Ingestion


```python
# The ingestion process might take a few minutes
collection.insert_many(listings)
print("Data ingestion into MongoDB completed")
```

## Vector Search Index defintion


```python
custom_utils.setup_vector_search_index(collection=collection)
```

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note:</b> If the output of the previous cell is <code>Error creating vector search index: Duplicate Index</code> you may proceed to the next cell if you intend to still use a previously created index.</p>

## Compose Vector Search Query


```python
def vector_search(user_query, db, collection, additional_stages=[], vector_index="vector_index_text"):
    """
    Perform a vector search in the MongoDB collection based on the user query.

    Args:
    user_query (str): The user's query string.
    db (MongoClient.database): The database object.
    collection (MongoCollection): The MongoDB collection to search.
    additional_stages (list): Additional aggregation stages to include in the pipeline.

    Returns:
    list: A list of matching documents.
    """

    # Generate embedding for the user query
    query_embedding = custom_utils.get_embedding(user_query)

    if query_embedding is None:
        return "Invalid query or embedding generation failed."

    # Define the vector search stage
    vector_search_stage = {
        "$vectorSearch": {
            "index": vector_index, # specifies the index to use for the search
            "queryVector": query_embedding, # the vector representing the query
            "path": "text_embeddings", # field in the documents containing the vectors to search against
            "numCandidates": 150, # number of candidate matches to consider
            "limit": 20, # return top 20 matches
        }
    }

    # Define the aggregate pipeline with the vector search stage and additional stages
    pipeline = [vector_search_stage] + additional_stages

    # Execute the search
    results = collection.aggregate(pipeline)

    explain_query_execution = db.command( # sends a database command directly to the MongoDB server
        'explain', { # return information about how MongoDB executes a query or command without actually running it
            'aggregate': collection.name, # specifies the name of the collection on which the aggregation is performed
            'pipeline': pipeline, # the aggregation pipeline to analyze
            'cursor': {} # indicates that default cursor behavior should be used
        }, 
        verbosity='executionStats') # detailed statistics about the execution of each stage of the aggregation pipeline

    vector_search_explain = explain_query_execution['stages'][0]['$vectorSearch']
    millis_elapsed = vector_search_explain['explain']['collectors']['allCollectorStats']['millisElapsed']

    print(f"Total time for the execution to complete on the database server: {millis_elapsed} milliseconds")

    return list(results)
```

## Handling User Query


```python
from pydantic import BaseModel
from typing import Optional

class SearchResultItem(BaseModel):
    name: str
    accommodates: Optional[int] = None
    bedrooms: Optional[int] = None
    address: custom_utils.Address
    space: str = None
```


```python
from IPython.display import display, HTML

def handle_user_query(query, db, collection, stages=[], vector_index="vector_index_text"):
    # Assuming vector_search returns a list of dictionaries with keys 'title' and 'plot'
    get_knowledge = vector_search(query, db, collection, stages, vector_index)

    # Check if there are any results
    if not get_knowledge:
        return "No results found.", "No source information available."

    # Convert search results into a list of SearchResultItem models
    search_results_models = [
        SearchResultItem(**result)
        for result in get_knowledge
    ]

    # Convert search results into a DataFrame for better rendering in Jupyter
    search_results_df = pd.DataFrame([item.dict() for item in search_results_models])

    # Generate system response using OpenAI's completion
    completion = custom_utils.openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system", 
                "content": "You are a airbnb listing recommendation system."},
            {
                "role": "user", 
                "content": f"Answer this user query: {query} with the following context:\n{search_results_df}"
            }
        ]
    )

    system_response = completion.choices[0].message.content

    # Print User Question, System Response, and Source Information
    print(f"- User Question:\n{query}\n")
    print(f"- System Response:\n{system_response}\n")

    # Display the DataFrame as an HTML table
    display(HTML(search_results_df.to_html()))

    # Return structured response and source info as a string
    return system_response
```

## Adding A Post Filter to Vector Search (Match Operator)


```python
import re
# Specifying the metadata field to limit documents on
search_path = "address.country"

# Create a match stage
match_stage = {
    "$match": {
       search_path: re.compile(r"United States"),
       "accommodates": { "$gt": 1, "$lt": 5}
    }
}

additional_stages = [match_stage]
```


```python
query = """
I want to stay in a place that's warm and friendly, 
and not too far from resturants, can you recommend a place? 
Include a reason as to why you've chosen your selection"
"""
handle_user_query(query, db, collection, additional_stages)
```

## Adding A PreFilter to Vector Search


```python
from pymongo.operations import SearchIndexModel
import time 

vector_index_with_filter = "vector_index_with_filter"

new_vector_search_index_model = SearchIndexModel(
    definition={
        "mappings": {
            "dynamic": True,
            "fields": {
                "text_embeddings": {
                    "dimensions": 1536,
                    "similarity": "cosine",
                    "type": "knnVector",
                },
                 "accommodates": {
                    "type": "number"
                },
                "bedrooms": {
                    "type": "number"
                },
            },
        }
    },
    name=vector_index_with_filter,
)

# Create the new index
try:
    result = collection.create_search_index(model=new_vector_search_index_model)
    print("Creating index...")
    time.sleep(20)  # Sleep for 20 seconds, adding sleep to ensure vector index has compeleted inital sync before utilization
    print("New index created successfully:", result)
except Exception as e:
    print(f"Error creating new vector search index: {str(e)}")
```

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note:</b> If the output of the previous cell is <code>Error creating vector search index: Duplicate Index</code> you may proceed to the next cell if you intend to still use a previously created index.</p>


```python
def vector_search(user_query, db, collection, additional_stages=[], vector_index="vector_index_text"):
    query_embedding = custom_utils.get_embedding(user_query)
    if query_embedding is None:
        return "Invalid query or embedding generation failed."

    vector_search_stage = {
        "$vectorSearch": {
            "index": vector_index,  # specifies the index to use for the search
            "queryVector": query_embedding,  # the vector representing the query
            "path": "text_embeddings",  # field in the documents containing the vectors to search against
            "numCandidates": 150,  # number of candidate matches to consider
            "limit": 20,  # return top 20 matches
            "filter": {
                "$and": [
                    {"accommodates": {"$gte": 2}}, 
                    {"bedrooms": {"$lte": 7}}
                ]
            },
        }
    }
    pipeline = [vector_search_stage] + additional_stages
    results = collection.aggregate(pipeline)
    explain_query_execution = db.command( # sends a database command directly to the MongoDB server
        'explain', { # return information about how MongoDB executes a query or command without actually running it
            'aggregate': collection.name, # specifies the name of the collection on which the aggregation is performed
            'pipeline': pipeline, # the aggregation pipeline to analyze
            'cursor': {} # indicates that default cursor behavior should be used
        }, 
        verbosity='executionStats') # detailed statistics about the execution of each stage of the aggregation pipeline

    vector_search_explain = explain_query_execution['stages'][0]['$vectorSearch']
    millis_elapsed = vector_search_explain['explain']['collectors']['allCollectorStats']['millisElapsed']

    print(f"Total time for the execution to complete on the database server: {millis_elapsed} milliseconds")
    return list(results)
```


```python
query = """
I want to stay in a place that's warm and friendly, 
and not too far from resturants, can you recommend a place? 
Include a reason as to why you've chosen your selection"
"""
handle_user_query(
    query, 
    db, 
    collection, 
    vector_index=vector_index_with_filter
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
