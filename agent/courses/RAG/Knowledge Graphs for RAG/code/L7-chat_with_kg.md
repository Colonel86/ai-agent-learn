# Lesson 7: Chatting with the SEC Knowledge Graph

<p style="background-color:#fd4a6180; padding:15px; margin-left:20px"> <b>Note:</b> This notebook takes about 30 seconds to be ready to use. Please wait until the "Kernel starting, please wait..." message clears from the top of the notebook before running any cells. You may start the video while you wait.</p>

### Import packages and set up Neo4j


```python
from dotenv import load_dotenv
import os

import textwrap

# Langchain
from langchain_community.graphs import Neo4jGraph
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI

# Warning control
import warnings
warnings.filterwarnings("ignore")
```


```python
# Load from environment
load_dotenv('.env', override=True)
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE') or 'neo4j'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Note the code below is unique to this course environment, and not a 
# standard part of Neo4j's integration with OpenAI. Remove if running 
# in your own environment.
OPENAI_ENDPOINT = os.getenv('OPENAI_BASE_URL') + '/embeddings'

# Global constants
VECTOR_INDEX_NAME = 'form_10k_chunks'
VECTOR_NODE_LABEL = 'Chunk'
VECTOR_SOURCE_PROPERTY = 'text'
VECTOR_EMBEDDING_PROPERTY = 'textEmbedding'
```


```python
kg = Neo4jGraph(
    url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD, database=NEO4J_DATABASE
)
```

### Explore the updated SEC documents graph
In this lesson, you'll be working with an updated graph that also includes the address information discussed in the video
- Some outputs below may differ slightly from the video
- Start by checking the schema of the graph


```python
kg.refresh_schema()
print(textwrap.fill(kg.schema, 60))
```

- Check the address of a random Manager
- Note: the company returned by the following query may differ from the one in the video


```python
kg.query("""
MATCH (mgr:Manager)-[:LOCATED_AT]->(addr:Address)
RETURN mgr, addr
LIMIT 1
""")
```

- Full text search for a manager named Royal Bank


```python
kg.query("""
  CALL db.index.fulltext.queryNodes(
         "fullTextManagerNames", 
         "royal bank") YIELD node, score
  RETURN node.managerName, score LIMIT 1
""")
```

- Find location of Royal Bank


```python
kg.query("""
CALL db.index.fulltext.queryNodes(
         "fullTextManagerNames", 
         "royal bank"
  ) YIELD node, score
WITH node as mgr LIMIT 1
MATCH (mgr:Manager)-[:LOCATED_AT]->(addr:Address)
RETURN mgr.managerName, addr
""")
```

- Determine which state has the most investment firms


```python
kg.query("""
  MATCH p=(:Manager)-[:LOCATED_AT]->(address:Address)
  RETURN address.state as state, count(address.state) as numManagers
    ORDER BY numManagers DESC
    LIMIT 10
""")
```

- Determine which state has the most companies


```python
kg.query("""
  MATCH p=(:Company)-[:LOCATED_AT]->(address:Address)
  RETURN address.state as state, count(address.state) as numCompanies
    ORDER BY numCompanies DESC
""")
```

- What are the cities in California with the most investment firms?


```python
kg.query("""
  MATCH p=(:Manager)-[:LOCATED_AT]->(address:Address)
         WHERE address.state = 'California'
  RETURN address.city as city, count(address.city) as numManagers
    ORDER BY numManagers DESC
    LIMIT 10
""")
```

- Which city in California has the most companies listed?


```python
kg.query("""
  MATCH p=(:Company)-[:LOCATED_AT]->(address:Address)
         WHERE address.state = 'California'
  RETURN address.city as city, count(address.city) as numCompanies
    ORDER BY numCompanies DESC
""")
```

- What are top investment firms in San Francisco?


```python
kg.query("""
  MATCH p=(mgr:Manager)-[:LOCATED_AT]->(address:Address),
         (mgr)-[owns:OWNS_STOCK_IN]->(:Company)
         WHERE address.city = "San Francisco"
  RETURN mgr.managerName, sum(owns.value) as totalInvestmentValue
    ORDER BY totalInvestmentValue DESC
    LIMIT 10
""")
```

- What companies are located in Santa Clara?


```python
kg.query("""
  MATCH (com:Company)-[:LOCATED_AT]->(address:Address)
         WHERE address.city = "Santa Clara"
  RETURN com.companyName
""")
```

- What companies are near Santa Clara?


```python
kg.query("""
  MATCH (sc:Address)
    WHERE sc.city = "Santa Clara"
  MATCH (com:Company)-[:LOCATED_AT]->(comAddr:Address)
    WHERE point.distance(sc.location, comAddr.location) < 10000
  RETURN com.companyName, com.companyAddress
""")
```

- What investment firms are near Santa Clara?
- Try updating the distance in the query to expand the search radius


```python
kg.query("""
  MATCH (address:Address)
    WHERE address.city = "Santa Clara"
  MATCH (mgr:Manager)-[:LOCATED_AT]->(managerAddress:Address)
    WHERE point.distance(address.location, 
        managerAddress.location) < 10000
  RETURN mgr.managerName, mgr.managerAddress
""")
```

- Which investment firms are near Palo Alto Networks?
- Note that full-text search is able to handle typos!


```python
# Which investment firms are near Palo Aalto Networks?
kg.query("""
  CALL db.index.fulltext.queryNodes(
         "fullTextCompanyNames", 
         "Palo Aalto Networks"
         ) YIELD node, score
  WITH node as com
  MATCH (com)-[:LOCATED_AT]->(comAddress:Address),
    (mgr:Manager)-[:LOCATED_AT]->(mgrAddress:Address)
    WHERE point.distance(comAddress.location, 
        mgrAddress.location) < 10000
  RETURN mgr, 
    toInteger(point.distance(comAddress.location, 
        mgrAddress.location) / 1000) as distanceKm
    ORDER BY distanceKm ASC
    LIMIT 10
""")
```

- Try pausing the video and modifying queries above to further explore the graph
- You can learn more about Cypher at the neo4j website: https://neo4j.com/product/cypher-graph-query-language/ 

### Writing Cypher with an LLM

In this section, you'll use few-shot learning to teach an LLM to write Cypher
- You'll use the OpenAI's GPT 3.5 model 
- You'll also use a new Neo4j integration within LangChain called **GraphCypherQAChain**


```python
CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to 
query a graph database.
Instructions:
Use only the provided relationship types and properties in the 
schema. Do not use any other relationship types or properties that 
are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than 
for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Examples: Here are a few examples of generated Cypher 
statements for particular questions:

# What investment firms are in San Francisco?
MATCH (mgr:Manager)-[:LOCATED_AT]->(mgrAddress:Address)
    WHERE mgrAddress.city = 'San Francisco'
RETURN mgr.managerName
The question is:
{question}"""
```


```python
CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)
```


```python
cypherChain = GraphCypherQAChain.from_llm(
    ChatOpenAI(temperature=0),
    graph=kg,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
)
```


```python
def prettyCypherChain(question: str) -> str:
    response = cypherChain.run(question)
    print(textwrap.fill(response, 60))
```


```python
prettyCypherChain("What investment firms are in San Francisco?")
```


```python
prettyCypherChain("What investment firms are in Menlo Park?")
```


```python
prettyCypherChain("What companies are in Santa Clara?")
```


```python
prettyCypherChain("What investment firms are near Santa Clara?")
```

### Expand the prompt to teach the LLM new Cypher patterns


```python
CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Examples: Here are a few examples of generated Cypher statements for particular questions:

# What investment firms are in San Francisco?
MATCH (mgr:Manager)-[:LOCATED_AT]->(mgrAddress:Address)
    WHERE mgrAddress.city = 'San Francisco'
RETURN mgr.managerName

# What investment firms are near Santa Clara?
  MATCH (address:Address)
    WHERE address.city = "Santa Clara"
  MATCH (mgr:Manager)-[:LOCATED_AT]->(managerAddress:Address)
    WHERE point.distance(address.location, 
        managerAddress.location) < 10000
  RETURN mgr.managerName, mgr.managerAddress

The question is:
{question}"""
```

- Update Cypher generation prompt with new template, and re-initialize the Cypher chain to use the new prompt
- Rerun this code anytime you make a change to the Cypher generation template!


```python
CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)

cypherChain = GraphCypherQAChain.from_llm(
    ChatOpenAI(temperature=0),
    graph=kg,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
)
```


```python
prettyCypherChain("What investment firms are near Santa Clara?")
```

### Expand the query to retrieve information from the Form 10K chunks


```python
CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Examples: Here are a few examples of generated Cypher statements for particular questions:

# What investment firms are in San Francisco?
MATCH (mgr:Manager)-[:LOCATED_AT]->(mgrAddress:Address)
    WHERE mgrAddress.city = 'San Francisco'
RETURN mgr.managerName

# What investment firms are near Santa Clara?
  MATCH (address:Address)
    WHERE address.city = "Santa Clara"
  MATCH (mgr:Manager)-[:LOCATED_AT]->(managerAddress:Address)
    WHERE point.distance(address.location, 
        managerAddress.location) < 10000
  RETURN mgr.managerName, mgr.managerAddress

# What does Palo Alto Networks do?
  CALL db.index.fulltext.queryNodes(
         "fullTextCompanyNames", 
         "Palo Alto Networks"
         ) YIELD node, score
  WITH node as com
  MATCH (com)-[:FILED]->(f:Form),
    (f)-[s:SECTION]->(c:Chunk)
  WHERE s.f10kItem = "item1"
RETURN c.text

The question is:
{question}"""
```


```python
CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)

cypherChain = GraphCypherQAChain.from_llm(
    ChatOpenAI(temperature=0),
    graph=kg,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
)

```


```python
prettyCypherChain("What does Palo Alto Networks do?")
```

### Try for yourself!

- Update the Cypher generation prompt below to ask different questions of the graph
- You can run the "check schema" cell to be reminded of the graph structure
- Use any of the examples in this notebook, or in previous lessons, to get started
- Remember to update the prompt template and restart the GraphCypherQAChain each time you make updates!


```python
# Check the graph schema
kg.refresh_schema()
print(textwrap.fill(kg.schema, 60))
```


```python
CYPHER_GENERATION_TEMPLATE = """Task:Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.
Schema:
{schema}
Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.
Examples: Here are a few examples of generated Cypher statements for particular questions:

# What investment firms are in San Francisco?
MATCH (mgr:Manager)-[:LOCATED_AT]->(mgrAddress:Address)
    WHERE mgrAddress.city = 'San Francisco'
RETURN mgr.managerName

# What investment firms are near Santa Clara?
  MATCH (address:Address)
    WHERE address.city = "Santa Clara"
  MATCH (mgr:Manager)-[:LOCATED_AT]->(managerAddress:Address)
    WHERE point.distance(address.location, 
        managerAddress.location) < 10000
  RETURN mgr.managerName, mgr.managerAddress

# What does Palo Alto Networks do?
  CALL db.index.fulltext.queryNodes(
         "fullTextCompanyNames", 
         "Palo Alto Networks"
         ) YIELD node, score
  WITH node as com
  MATCH (com)-[:FILED]->(f:Form),
    (f)-[s:SECTION]->(c:Chunk)
  WHERE s.f10kItem = "item1"
RETURN c.text

The question is:
{question}"""
```


```python
# Update the prompt and reset the QA chain
CYPHER_GENERATION_PROMPT = PromptTemplate(
    input_variables=["schema", "question"], 
    template=CYPHER_GENERATION_TEMPLATE
)

cypherChain = GraphCypherQAChain.from_llm(
    ChatOpenAI(temperature=0),
    graph=kg,
    verbose=True,
    cypher_prompt=CYPHER_GENERATION_PROMPT,
)
```


```python
prettyCypherChain("<<REPLACE WITH YOUR QUESTION>>")
```
