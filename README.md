# agentmemory

Easy-to-use agent memory, powered by chromadb

<img src="resources/image.jpg">

# Installation

```bash
pip install agentmemory
```

# Quickstart

```python
from agentmemory import create_memory, search_memory, set_storage_path

set_storage_path('./memory')

# create a memory
create_memory("conversation", "I can't do that, Dave.", metadata={"speaker": "HAL", "some_other_key": "some value, could be a number or string"})

# search for a memory
memories = search_memory("conversation", "Dave") # category, search term

print(str(memories))

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

# Basic Usage Guide

## Importing into your project

```python
from agentmemory import (
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

## Create a Memory

```python
# category, document, metadata
create_memory("conversation", "I can't do that, Dave.", metadata={"speaker": "HAL", "some_other_key": "some value, could be a number or string"})
```

## Search memories

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

## Get a memory

```python
memory = get_memory("conversation", 1) # category, id
```

## Update a memory

```python
update_memory("conversation", 1, "Okay, I will open the podbay doors.")
```

## Delete a Memory

```python
delete_memory("conversation", 1)
```

# Documentation

## Create a Memory

#### `create_memory(category, text, id=None, metadata=None, persist=True)`

Create a new memory in a collection.

```python
>>> create_memory(category='sample_category', text='sample_text', id='sample_id', metadata={'sample_key': 'sample_value'}, persist=True)
```

## Search Memory

#### `search_memory(category, search_text, n_results=5, filter_metadata=None, contains_text=None, include_embeddings=True)`

Search a collection with given query texts.

```python
>>> search_memory('sample_category', 'search_text', n_results=2, filter_metadata={'sample_key': 'sample_value'}, contains_text='sample', include_embeddings=True, include_distances=True)
[{'metadata': '...', 'document': '...', 'id': '...'}, {'metadata': '...', 'document': '...', 'id': '...'}]
```

## Get a Memory

#### `get_memory(category, id, include_embeddings=True)`

Retrieve a specific memory from a given category based on its ID.

```python
>>> get_memory("books", "1")
```

## Get Memories

#### `get_memories(category, sort_order="desc", filter_metadata=None, n_results=20, include_embeddings=True)`

Retrieve a list of memories from a given category, sorted by ID, with optional filtering. `sort_order` controls whether you get from the beginning or end of the list.

```python
>>> get_memories("books", sort_order="asc", n_results=10)
```

## Update a Memory

#### `update_memory(category, id, text=None, metadata=None, persist=True)`

Update a specific memory with new text and/or metadata.

```python
# with keyword arguments
update_memory(category="conversation", id=1, text="Okay, I will open the podbay doors.", metadata={ "speaker": "HAL", "sentiment": "positive" }, persist=True)

# with positional arguments
update_memory("conversation", 1, "Okay, I will open the podbay doors.")
```

## Delete a Memory

#### `delete_memory(category, id, contains_metadata=None, contains_text=None, persist=True)`

Delete a specific memory based on its ID and optionally on matching metadata and/or text.

```python
>>> delete_memory("books", "1")
```

## Check if a memory exists

#### `memory_exists(category, id, includes_metadata=None)`

Check if a memory with a specific ID exists in a given category.

```python
>>> memory_exists("books", "1")
```

## Wipe an Entire Category of Memories

#### `wipe_category(category, persist=True)`

Delete an entire category of memories.

```python
>>> wipe_category("books")
```

## Count Memories

#### `count_memories(category)`

Count the number of memories in a given category.

```python
>>> count_memories("books")
```

## Wipe All Memories

#### `wipe_all_memories(persist=True)`

Delete all memories across all categories.

```python
>>> wipe_all_memories()
```

## Set a Persistent Storage Path

#### `set_storage_path(path)`

```python
    >>> set_storage_path("path/to/persistent/directory")
```

## Save All Memory to Disk

#### `save_memory()`

```python
    >>> save_memory()
```

# Publishing

```bash
bash publish.sh --version=<version> --username=<pypi_username> --password=<pypi_password>
```

# Contributions Welcome

If you like this library and want to contribute in any way, please feel free to submit a PR and I will review it. Please note that the goal here is simplicity and accesibility, using common language and few dependencies.

# Questions, Comments, Concerns

If you have any questions, please feel free to reach out to me on [Twitter](https://twitter.com/spatialweeb) or [Discord](@new.moon).
