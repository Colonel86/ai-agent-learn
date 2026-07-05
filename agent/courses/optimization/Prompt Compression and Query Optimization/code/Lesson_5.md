# L5: Prompt Compression


<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note <code>(Kernel Starting)</code>:</b> This notebook takes about 30 seconds to be ready to use. You may start and watch the video while you wait.</p>


```python
# Warning control
import warnings
warnings.filterwarnings('ignore')
```


```python
#pip install llmlingua
```


```python
import custom_utils 
```

<p style="background-color:#fff6ff; padding:15px; border-width:3px; border-color:#efe6ef; border-style:solid; border-radius:6px"> 💻 &nbsp; <b>Access <code>requirements.txt</code> and <code>utils</code> files:</b> To access <code>requirements.txt</code> for this notebook, 1) click on the <em>"File"</em> option on the top menu of the notebook and then 2) click on <em>"Open"</em>. For more help, please see the <em>"Appendix - Tips and Help"</em> Lesson.</p>

## Data Loading


```python
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
collection.insert_many(listings)
print("Data ingestion into MongoDB completed")
```

## Vector Search Index defintion


```python
# Create vector search index
custom_utils.setup_vector_search_index_with_filter(collection=collection)
```

<p style="background-color:#fff6e4; padding:15px; border-width:3px; border-color:#f5ecda; border-style:solid; border-radius:6px"> ⏳ <b>Note:</b> If the output of the previous cell is <code>Error creating vector search index: Duplicate Index</code> you may proceed to the next cell if you intend to still use a previously created index.</p>

## Handling User Query


```python
from pydantic import BaseModel
from typing import Optional

class SearchResultItem(BaseModel):
    name: str
    accommodates: Optional[int] = None
    address: custom_utils.Address
    neighborhood_overview: Optional[str] = None
    notes: Optional[str] = None
    averageReviewScore: Optional[float] = None
    number_of_reviews: Optional[float] = None
    combinedScore: Optional[float] = None
```

## Boosting Search Results After Vector Search


```python
review_average_stage = {
    "$addFields": {
        "averageReviewScore": {
            "$divide": [
                {
                    "$add": [
                        "$review_scores.review_scores_accuracy",
                        "$review_scores.review_scores_cleanliness",
                        "$review_scores.review_scores_checkin",
                        "$review_scores.review_scores_communication",
                        "$review_scores.review_scores_location",
                        "$review_scores.review_scores_value",
                    ]
                },
                6  # Divide by the number of review score types to get the average
            ]
        },
        # Calculate a score boost factor based on the number of reviews
        "reviewCountBoost": "$number_of_reviews"
    }
}
```


```python
weighting_stage = {
    "$addFields": {
        "combinedScore": {
            # Example formula that combines average review score and review count boost
            "$add": [
                {"$multiply": ["$averageReviewScore", 0.3]},  # Weighted average review score
                {"$multiply": ["$reviewCountBoost", 0.7]}   # Weighted review count boost
            ]
        }
    }
}
```


```python
# Apply the combinedScore for sorting
sorting_stage_sort = {
    "$sort": {"combinedScore": -1}  # Descending order to boost higher combined scores
}
```


```python
additional_stages = [review_average_stage, weighting_stage, sorting_stage_sort]
```

## Modified Handling User Query


```python
from IPython.display import display, HTML
import pprint

def handle_user_query(query, db, collection, stages=[], vector_index="vector_index_text"):
    get_knowledge = custom_utils.vector_search_with_filter(query, db, collection, stages, vector_index)

    if not get_knowledge:
        return "No results found.", "No source information available."
    
    search_results_models = [
        SearchResultItem(**result)
        for result in get_knowledge
    ]

    search_results_df = pd.DataFrame([item.dict() for item in search_results_models])

    print("Uncompressed Prompt (Query Info):\n")
    print(search_results_df)

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
    print(f"- User Question:\n{query}\n")
    print(f"- System Response:\n{system_response}\n")
    display(HTML(search_results_df.to_html()))
    return system_response
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
    additional_stages, 
    vector_index="vector_index_with_filter"
)
```

## Prompt Compression


```python
import json
from llmlingua import PromptCompressor

llm_lingua = PromptCompressor(
    model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
    model_config={"revision": "main"},
    use_llmlingua2=True,
    device_map="cpu",
)

# Function definition
def compress_query_prompt(query):

    demonstration_str = query['demonstration_str']
    instruction = query['instruction']
    question = query['question']

    # 6x Compression
    compressed_prompt = llm_lingua.compress_prompt(
        demonstration_str.split("\n"), 
        instruction=instruction,
        question=question,
        target_token=500,
        rank_method="longllmlingua", 
        context_budget="+100",
        dynamic_context_compression_ratio=0.4,
        reorder_context="sort",
    )

    return json.dumps(compressed_prompt, indent=4)

```


```python
def handle_user_query_with_compression(query, db, collection, stages=[], vector_index="vector_index_text"):
    # Perform vector search to get knowledge from the database
    get_knowledge = custom_utils.vector_search_with_filter(query, db, collection, stages, vector_index)

    # Check if there are any results
    if not get_knowledge:
        return None, "No results found."

    # Convert search results into a list of SearchResultItem models
    search_results_models = [SearchResultItem(**result) for result in get_knowledge]

    # Convert search results into a DataFrame for better rendering
    search_results_df = pd.DataFrame([item.dict() for item in search_results_models])

    # Prepare information for compression
    query_info = {
        'demonstration_str': search_results_df.to_string(),  # Results from information retrieval process
        'instruction': "Write a high-quality answer for the given question using only the provided search results.",
        'question': query  # User query
    }

    # Compress the query prompt using predefined function
    compressed_prompt = compress_query_prompt(query_info)

    # Optional: Print compressed prompts for debugging
    print("Compressed Prompt:\n")
    pprint.pprint(compressed_prompt)
    print("\n" + "=" * 80 + "\n")

    return search_results_df, compressed_prompt


```


```python
def handle_system_response(query, compressed_prompt):
    # Generate system response using OpenAI's completion
    completion = custom_utils.openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are an Airbnb listing recommendation system."
            },
            {
                "role": "user",
                "content": f"Answer this user query: {query} with the following context:\n{compressed_prompt}"
            }
        ]
    )

    system_response = completion.choices[0].message.content

    # Print User Question, System Response
    print(f"- User Question:\n{query}\n")
    print(f"- System Response:\n{system_response}\n")

    # Return the system response
    return system_response

```


```python
# Compress the query and get search results
results, compressed_prompt = handle_user_query_with_compression(query, 
                                                                  db, 
                                                                  collection, 
                                                                  additional_stages, 
                                                                  vector_index="vector_index_with_filter"
                                                                 )
```


```python
if compressed_prompt:
    # Handle the system response with the compressed prompt
    system_response = handle_system_response(query, compressed_prompt)
else:
    print("No valid results to display.")
```

## Additional Resouces

- [The MongoDB Developer Center for tutorials, articles and videos](https://mdb.link/developer_center)

- [The GenAI Showcase Repo for code showcasing building AI applications and demo](https://github.com/mongodb-developer/GenAI-Showcase)

- [DeepLearning AI forum for question in regards to this course](https://community.deeplearning.ai/)


```python

```


```python

```


```python

```


```python

```
