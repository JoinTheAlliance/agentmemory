# agentmemory

Dead simple agent memory, built on chromadb

# Installation

```bash
pip install agentmemory
```

# Usage

## Importing into your project

```python
from agentmemory.memory import (
    create_memory,
    get_memories,
    search_memory,
    get_memory,
    update_memory,
    delete_memory,
    count_memories,
    wipe_category,
    wipe_all_memories
)
```

## Create a memory

```python
# category, document, metadata
create_memory("conversation", "I can't do that, Dave.", metadata={"speaker": "HAL", "some_other_key": "some value, could be a number or string"})
```

## Get all memories

```python
memories = get_memories("conversation") # can be any category
# memories is a list of dictionaries
[
    {
        "id": int,
        "document": string,
        "metadata": dict{...values},
        "embeddings": (Optional) list[float] | None
    },
    {
        ...
    }
]
```

# Search memories

```python
memories = search_memory("conversation", "Dave") # category, search term
# memories is a list of dictionaries
[
    {
        "id": int,
        "document": string,
        "metadata": dict{...values},
        "embeddings": (Optional) list[float] | None
    },
    {
        ...
    }
]
```

## Get a memory

```python
memory = get_memory("conversation", 1) # category, id
```

## Update a memory

```python
# update the document and metadata
update_memory("conversation", 1, "Okay, I will open the podbay doors.", { "speaker": "HAL", "sentiment": "positive" }) # category, id, new document
# update the document
update_memory("conversation", 1, "Okay, I will open the podbay doors.") # category, id, new document
```

## Delete a memory

```python
delete_memory("conversation", 1) # category, id
```

## Count memories

```python
count_memories("conversation") # category
```

## Wipe a category

```python
wipe_category("conversation") # category
```

## Wipe all memories

```python
wipe_all_memories()
```

# Contributions Welcome

If you like this library and want to contribute in any way, please feel free to submit a PR and I will review it. Please note that the goal here is simplicity and accesibility, using common language and few dependencies.

# Questions, Comments, Concerns

If you have any questions, please feel free to reach out to me on [Twitter](https://twitter.com/spatialweeb) or [Discord](@new.moon).
