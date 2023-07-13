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

#### `create_memory(category, text, id=None, embedding=None, metadata=None, persist=True)`

Create a new memory in a collection.

##### Arguments

```
# Required
category (str): Category of the collection.
text (str): Document text.

# Optional
id (str): Unique id. Generated incrementally unless set.
metadata (dict): Metadata.
embedding (array): Embedding of the document. Defaults to None. Use if you already have an embedding.
persist (bool): Whether to persist the changes to disk. Defaults to True.
```

##### Example

```python
>>> create_memory(category='sample_category', text='sample_text', id='sample_id', metadata={'sample_key': 'sample_value'}, persist=True)
```

## Search Memory

#### `search_memory(category, search_text, n_results=5, min_distance=None, max_distance=None, filter_metadata=None, contains_text=None, include_embeddings=True)`

Search a collection with given query texts.

A note about distances: the filters are applied after the query, so the n_results may be dramatically shortened. This is a current limitation of Chromadb.

##### Arguments

```
# Required
category (str): Category of the collection.
search_text (str): Text to be searched.

# Optional
n_results (int): Number of results to be returned.
filter_metadata (dict): Metadata for filtering the results.
contains_text (str): Text that must be contained in the documents.
include_embeddings (bool): Whether to include embeddings in the results.
include_distances (bool): Whether to include distances in the results.
max_distance (float): Only include memories with this distance threshold maximum.
    0.1 = most memories will be exluded, 1.0 = no memories will be excluded
min_distance (float): Only include memories that are at least this distance
    0.0 = No memories will be excluded, 0.9 = most memories will be excluded
```

##### Returns

```
list: List of search results.
```

##### Example

```python
>>> search_memory('sample_category', 'search_text', min_distance=0.01, max_distance=0.7, n_results=2, filter_metadata={'sample_key': 'sample_value'}, contains_text='sample', include_embeddings=True, include_distances=True)
[{'metadata': '...', 'document': '...', 'id': '...'}, {'metadata': '...', 'document': '...', 'id': '...'}]
```

## Get a Memory

#### `get_memory(category, id, include_embeddings=True)`

Retrieve a specific memory from a given category based on its ID.

##### Arguments

```
# Required
category (str): The category of the memory.
id (str/int): The ID of the memory.

#optional
include_embeddings (bool): Whether to include the embeddings. Defaults to True.
```

##### Returns

```
dict: The retrieved memory.
```

##### Example

```python
>>> get_memory("books", "1")
```

## Get Memories

#### `get_memories(category, sort_order="desc", filter_metadata=None, n_results=20, include_embeddings=True)`

Retrieve a list of memories from a given category, sorted by ID, with optional filtering. `sort_order` controls whether you get from the beginning or end of the list.

###### Arguments

```
# Required
category (str): The category of the memories.

# Optional
sort_order (str): The sorting order of the memories. Can be 'asc' or 'desc'. Defaults to 'desc'.
filter_metadata (dict): Filter to apply on metadata. Defaults to None.
n_results (int): The number of results to return. Defaults to 20.
include_embeddings (bool): Whether to include the embeddings. Defaults to True.
```

##### Returns

```
list: List of retrieved memories.
```

##### Example

```python
>>> get_memories("books", sort_order="asc", n_results=10)
```

## Update a Memory

#### `update_memory(category, id, text=None, metadata=None, persist=True)`

Update a memory with new text and/or metadata.

##### Arguments

```
# Required
category (str): The category of the memory.
id (str/int): The ID of the memory.

# Optional
text (str): The new text of the memory. Defaults to None.
metadata (dict): The new metadata of the memory. Defaults to None.
persist (bool): Whether to persist the changes to disk. Defaults to True.
```

##### Example

```python
# with keyword arguments
update_memory(category="conversation", id=1, text="Okay, I will open the podbay doors.", metadata={ "speaker": "HAL", "sentiment": "positive" }, persist=True)

# with positional arguments
update_memory("conversation", 1, "Okay, I will open the podbay doors.")
```

## Delete a Memory

#### `delete_memory(category, id, contains_metadata=None, contains_text=None, persist=True)`

Delete a memory by ID.

##### Arguments

```
# Required
category (str): The category of the memory.
id (str/int): The ID of the memory.

# Optional
persist (bool): Whether to persist the changes to disk. Defaults to True.
```

##### Example

```python
>>> delete_memory("books", "1")
```

## Check if a memory exists

#### `memory_exists(category, id, includes_metadata=None)`

Check if a memory exists in a given category.

##### Arguments

```
# Required
category (str): The category of the memory.
id (str/int): The ID of the memory.

# Optional
includes_metadata (dict): Metadata that the memory should include. Defaults to None.
```

##### Example

```python
>>> memory_exists("books", "1")
```

## Wipe an Entire Category of Memories

#### `wipe_category(category, persist=True)`

Delete an entire category of memories.

##### Arguments

```
# Required
category (str): The category to delete.

# Optional
persist (bool): Whether to persist the changes to disk. Defaults to True.
```

##### Example

```python
>>> wipe_category("books")
```

## Count Memories

#### `count_memories(category)`

Count the number of memories in a given category.

##### Arguments

```
category (str): The category of the memories.
```

##### Returns

```
int: The number of memories.
```

##### Example

```python
>>> count_memories("books")
```

## Wipe All Memories

#### `wipe_all_memories(persist=True)`

Delete all memories across all categories.

##### Arguments

```
# Optional
persist (bool): Whether to persist the changes to disk. Defaults to True.
```

##### Example

```python
>>> wipe_all_memories()
```

## Set a Persistent Storage Path

#### `set_storage_path(path)`

##### Arguments

```
path (string): the path to save to
```

##### Example

```python
    >>> set_storage_path("path/to/persistent/directory")
```

## Save All Memory to Disk

#### `save_memory()`

##### Example

```python
    >>> save_memory()
```

Sure, here's a Markdown formatted version that can be used in a `README.md` file:

````markdown
# Memory Management with ChromaDB

This document provides a guide to using the memory management functions provided in the module.

## Functions

### Export Memories to JSON

The `export_memory_to_json` function exports all memories to a dictionary, optionally including embeddings.

##### Arguments

- `include_embeddings` (bool, optional): Whether to include memory embeddings in the output. Defaults to True.

**Returns:**

- dict: A dictionary with collection names as keys and lists of memories as values.

##### Example

```python
>>> export_memory_to_json()
```
````

### Export Memories to File

The `export_memory_to_file` function exports all memories to a JSON file, optionally including embeddings.

##### Arguments

- `path` (str, optional): The path to the output file. Defaults to "./memory.json".
- `include_embeddings` (bool, optional): Whether to include memory embeddings in the output. Defaults to True.

##### Example

```python
>>> export_memory_to_file(path="/path/to/output.json")
```

### Import Memories from JSON

The `import_json_to_memory` function imports memories from a dictionary into the current database.

##### Arguments

- `data` (dict): A dictionary with collection names as keys and lists of memories as values.
- `replace` (bool, optional): Whether to replace existing memories. If True, all existing memories will be deleted before import. Defaults to True.

##### Example

```python
>>> import_json_to_memory(data)
```

### Import Memories from File

The `import_file_to_memory` function imports memories from a JSON file into the current database.

##### Arguments

- `path` (str, optional): The path to the input file. Defaults to "./memory.json".
- `replace` (bool, optional): Whether to replace existing memories. If True, all existing memories will be deleted before import. Defaults to True.

##### Example

```python
>>> import_file_to_memory(path="/path/to/input.json")
```

````

In the above Markdown, you may replace "ChromaDB" with the actual name of the module if it's different. You can include this in your `README.md` file to give your users a guide on how to use these functions.

# Publishing

```bash
bash publish.sh --version=<version> --username=<pypi_username> --password=<pypi_password>
````

# Contributions Welcome

If you like this library and want to contribute in any way, please feel free to submit a PR and I will review it. Please note that the goal here is simplicity and accesibility, using common language and few dependencies.

<img src="resources/youcreatethefuture.jpg">
