# L1: Vanilla Vector Search


<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note <code>(Kernel Starting)</code>:</b> This notebook takes about 30 seconds to be ready to use. You may start and watch the video while you wait.</p>



```python
# Warning control
import warnings
warnings.filterwarnings('ignore')
```


```python
#!pip install datasets pandas openai pymongo pydantic
```

## Get API Keys
In this classroom, the libraries and APIs have been already installed and set up for you.
If you would like to run this code on your own machine, you will need to enter your own MONGO_URI and OPENAI_API_KEY keys in the following cell.


```python
import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MONGO_URI = os.environ.get("MONGO_URI")
```

<p style="background-color:#fff6ff; padding:15px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px"> 💻 &nbsp; <b>Access <code>requirements.txt</code> file:</b> To access <code>requirements.txt</code> for this notebook, 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em>. For more help, please see the <em>"Appendix - Tips and Help"</em> Lesson.</p>

## 1.1 Data Loading


```python
# 1. Dataset Loading
from datasets import load_dataset
import pandas as pd

# NOTE: Make sure you have an Hugging Face token (HF_TOKEN) in your development environemnt
# NOTE: https://huggingface.co/datasets/MongoDB/airbnb_embeddings
# NOTE: This dataset contains several records with datapoint representing an airbnb listing.
# NOTE: This dataset contains text and image embeddings, but this lessons only uses the text embeddings
dataset = load_dataset("MongoDB/airbnb_embeddings", streaming=True, split="train")
dataset = dataset.take(100)
# Convert the dataset to a pandas dataframe
dataset_df = pd.DataFrame(dataset)
dataset_df.head(5)
```


```python
print("Columns:", dataset_df.columns)
```

## 1.2 Document Modelling


```python
from typing import List, Optional
from pydantic import BaseModel, ValidationError
from datetime import datetime
```


```python
class Host(BaseModel):
    host_id: str
    host_url: str
    host_name: str
    host_location: str
    host_about: str
    host_response_time: Optional[str] = None
    host_thumbnail_url: str
    host_picture_url: str
    host_response_rate: Optional[int] = None
    host_is_superhost: bool
    host_has_profile_pic: bool
    host_identity_verified: bool
```


```python
class Location(BaseModel):
    type: str
    coordinates: List[float]
    is_location_exact: bool

class Address(BaseModel):
    street: str
    government_area: str
    market: str
    country: str
    country_code: str
    location: Location
```


```python
class Review(BaseModel):
    _id: str
    date: Optional[datetime] = None
    listing_id: str
    reviewer_id: str
    reviewer_name: Optional[str] = None
    comments: Optional[str] = None
```


```python
class Listing(BaseModel):
    _id: int
    listing_url: str
    name: str
    summary: str
    space: str
    description: str
    neighborhood_overview: Optional[str] = None
    notes: Optional[str] = None
    transit: Optional[str] = None
    access: str
    interaction: Optional[str] = None
    house_rules: str
    property_type: str
    room_type: str
    bed_type: str
    minimum_nights: int
    maximum_nights: int
    cancellation_policy: str
    last_scraped: Optional[datetime] = None
    calendar_last_scraped: Optional[datetime] = None
    first_review: Optional[datetime] = None
    last_review: Optional[datetime] = None
    accommodates: int
    bedrooms: Optional[float] = 0
    beds: Optional[float] = 0
    number_of_reviews: int
    bathrooms: Optional[float] = 0
    amenities: List[str]
    price: int
    security_deposit: Optional[float] = None
    cleaning_fee: Optional[float] = None
    extra_people: int
    guests_included: int
    images: dict
    host: Host
    address: Address
    availability: dict
    review_scores: dict
    reviews: List[Review]
    text_embeddings: List[float]

```


```python
records = dataset_df.to_dict(orient='records')
```


```python
# To handle catch `NaT` values
for record in records:
    for key, value in record.items():
        # Check if the value is list-like; if so, process each element.
        if isinstance(value, list):
            processed_list = [None if pd.isnull(v) else v for v in value]
            record[key] = processed_list
        # For scalar values, continue as before.
        else:
            if pd.isnull(value):
                record[key] = None
```


```python
try:
  # Convert each dictionary to a Movie instance
  listings = [Listing(**record).dict() for record in records]
  # Get an overview of a single datapoint
  print(listings[0].keys())
except ValidationError as e:
  print(e)
```

## 1.3 Database Creation and Connection


```python
from pymongo.mongo_client import MongoClient
from pymongo.operations import SearchIndexModel
```


```python
database_name = "airbnb_dataset"
collection_name = "listings_reviews"
```


```python

def get_mongo_client(mongo_uri):
    """Establish connection to the MongoDB."""

    # gateway to interacting with a MongoDB database cluster
    client = MongoClient(mongo_uri, appname="devrel.deeplearningai.lesson1.python")
    print("Connection to MongoDB successful")
    return client
```


```python
if not MONGO_URI:
    print("MONGO_URI not set in environment variables")

mongo_client = get_mongo_client(MONGO_URI)

# Pymongo client of database and collection
db = mongo_client.get_database(database_name)
collection = db.get_collection(collection_name)
```


```python
# Delete any existing records in the collection
collection.delete_many({})
```

## 1.4 Data Ingestion


```python
# The ingestion process might take a few minutes
collection.insert_many(listings)
print("Data ingestion into MongoDB completed")
```

## 1.5 Vector Search Index defintion


```python
# NOTE: This dataset contains text and image embeddings, but this lessons only uses the text embeddings
# The field containing the text embeddings on each document within the listings_reviews collection 
text_embedding_field_name = "text_embeddings"
# MongoDB Atlas Vector Search index name
vector_search_index_name_text = "vector_index_text"
```


```python
vector_search_index_model = SearchIndexModel(
    definition={
        "mappings": { # describes how fields in the database documents are indexed and stored
            "dynamic": True, # automatically index new fields that appear in the document
            "fields": { # properties of the fields that will be indexed.
                text_embedding_field_name: { 
                    "dimensions": 1536, # size of the vector.
                    "similarity": "cosine", # algorithm used to compute the similarity between vectors
                    "type": "knnVector",
                }
            },
        }
    },
    name=vector_search_index_name_text, # identifier for the vector search index
)
```


```python
# Check if the index already exists
index_exists = False
for index in collection.list_indexes():
    print(index)
    if index['name'] == vector_search_index_name_text:
        index_exists = True
        break
```


```python
import time

# Create the index if it doesn't exist
if not index_exists:
    try:
        result = collection.create_search_index(model=vector_search_index_model)
        print("Creating index...")
        time.sleep(20)  # Sleep for 20 seconds, adding sleep to ensure vector index has compeleted inital sync before utilization
        print("Index created successfully:", result)
        print("Wait a few minutes before conducting search with index to ensure index intialization")
    except Exception as e:
        print(f"Error creating vector search index: {str(e)}")
else:
    print(f"Index '{vector_search_index_name_text}' already exists.")

# NOTE: if the output of this process is Error creating vector search index: Duplicate Index, you may proceed to the next cell if you intend to still use a previously created index
```

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note:</b> If the output of the previous cell is <code>Error creating vector search index: Duplicate Index</code> you may proceed to the next cell if you intend to still use a previously created index.</p>


```python
import openai

openai.api_key = OPENAI_API_KEY

def get_embedding(text):
    """Generate an embedding for the given text using OpenAI's API."""

    # Check for valid input
    if not text or not isinstance(text, str):
        return None

    try:
        # Call OpenAI API to get the embedding
        embedding = openai.embeddings.create(
            input=text,
            model="text-embedding-3-small", dimensions=1536).data[0].embedding
        return embedding
    except Exception as e:
        print(f"Error in get_embedding: {e}")
        return None
```

## 1.6 Compose Vector Search Query


```python
def vector_search(user_query, db, collection, vector_index="vector_index_text"):
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
    query_embedding = get_embedding(user_query)

    if query_embedding is None:
        return "Invalid query or embedding generation failed."

    # Define the vector search stage
    vector_search_stage = {
        "$vectorSearch": {
            "index": vector_index, # specifies the index to use for the search
            "queryVector": query_embedding, # the vector representing the query
            "path": text_embedding_field_name, # field in the documents containing the vectors to search against
            "numCandidates": 150, # number of candidate matches to consider
            "limit": 20 # return top 20 matches
        }
    }

    # Define the aggregate pipeline with the vector search stage and additional stages
    pipeline = [vector_search_stage]

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

## 1.7 Handling User Query


```python
class SearchResultItem(BaseModel):
    name: str
    accommodates: Optional[int] = None
    address: Address
    summary: Optional[str] = None
    description: Optional[str] = None
    neighborhood_overview: Optional[str] = None
    notes: Optional[str] = None
```


```python
from IPython.display import display, HTML

def handle_user_query(query, db, collection):
    # Assuming vector_search returns a list of dictionaries with keys 'title' and 'plot'
    get_knowledge = vector_search(query, db, collection)

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
    completion = openai.chat.completions.create(
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


```python
query = """
I want to stay in a place that's warm and friendly, 
and not too far from resturants, can you recommend a place? 
Include a reason as to why you've chosen your selection.
"""
handle_user_query(query, db, collection)
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
