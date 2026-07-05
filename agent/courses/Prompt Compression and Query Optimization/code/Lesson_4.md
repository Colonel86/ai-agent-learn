# L4: Boosting


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
    averageReviewScore: Optional[float] = None
    number_of_reviews: Optional[float] = None
    combinedScore: Optional[float] = None

```


```python
from IPython.display import display, HTML

def handle_user_query(query, db, collection, stages=[], vector_index="vector_index_text"):
    get_knowledge = custom_utils.vector_search_with_filter(query, db, collection, stages, vector_index)

    if not get_knowledge:
        return "No results found.", "No source information available."
    
    print("List of all fields of the first document, before model conformance")
    print(get_knowledge[0].keys())

    search_results_models = [
        SearchResultItem(**result)
        for result in get_knowledge
    ]

    search_results_df = pd.DataFrame([item.dict() for item in search_results_models])

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
                {"$multiply": ["$averageReviewScore", 0.9]},  # Weighted average review score
                {"$multiply": ["$reviewCountBoost", 0.1]}   # Weighted review count boost
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

## Results


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
