# agentmemory <a href="https://discord.gg/qetWd7J9De"><img style="float: right" src="https://dcbadge.vercel.app/api/server/qetWd7J9De" alt=""></a> <a href="https://github.com/AutonomousResearchGroup/agentmemory/stargazers"><img style="float: right; padding: 5px;" src="https://img.shields.io/github/stars/AutonomousResearchGroup/agentmemory?style=social" alt=""></a>

Easy-to-use agent memory, powered by chromadb

<img src="resources/image.jpg">

[![Lint and Test](https://github.com/AutonomousResearchGroup/agentmemory/actions/workflows/test.yml/badge.svg)](https://github.com/AutonomousResearchGroup/agentmemory/actions/workflows/test.yml)
[![PyPI version](https://badge.fury.io/py/agentmemory.svg)](https://badge.fury.io/py/agentmemory)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://github.com/AutonomousResearchGroup/easycompletion/blob/main/LICENSE)
[![forks - easycompletion](https://img.shields.io/github/forks/AutonomousResearchGroup/easycompletion?style=social)](https://github.com/AutonomousResearchGroup/easycompletion)

# Installation

```bash
pip install agentmemory
```

# Quickstart

```python
from agentmemory import create_memory, search_memory

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

# Debugging

You can enable debugging by passing `debug=True` to most functions, or by setting DEBUG=True in your environment to get global memory debugging.

```python
create_memory("conversation", "I can't do that, Dave.", debug=True)
```

# Basic Usage Guide

## Importing into your project

```python
from agentmemory import (
    create_memory,
    create_unique_memory,
    get_memories,
    search_memory,
    get_memory,
    update_memory,
    delete_memory,
    delete_similar_memories,
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

### Delete Similar Memories

#### `delete_similar_memories(category, content, similarity_threshold=0.95)`

Search for memories that are similar to the one that contains the given content and removes them.

##### Parameters

- `category` (str): The category of the collection.
- `content` (str): The content to search for.
- `similarity_threshold` (float, optional): The threshold for determining similarity. Defaults to 0.95.

##### Returns

- `bool`: True if the memory item is found and removed, False otherwise.

# API Reference

## Create a Memory

#### `create_memory(category, text, id=None, embedding=None, metadata=None)`

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
```

##### Example

```python
>>> create_memory(category='sample_category', text='sample_text', id='sample_id', metadata={'sample_key': 'sample_value'})
```

### Create Unique Memory

#### `create_unique_memory(category, content, metadata={}, similarity=0.95)`

Create a new memory only if there aren't any that are very similar to it. If a similar memory is found, the new memory's "novel" metadata field is set to "False" and it is linked to the existing memory.

##### Parameters

- `category` (str): The category of the collection.
- `content` (str): The text of the memory.
- `metadata` (dict, optional): Metadata for the memory.
- `similarity` (float, optional): The threshold for determining similarity.

##### Returns

None

## Search Memory

#### `search_memory(category, search_text, n_results=5, min_distance=None, max_distance=None, filter_metadata=None, contains_text=None, include_embeddings=True, novel=False)`

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
novel (bool): Whether to return only novel memories.
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

#### `get_memories(category, sort_order="desc", filter_metadata=None, n_results=20, include_embeddings=True, novel=False)`

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
novel (bool): Whether to return only novel memories. Defaults to False.
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

#### `update_memory(category, id, text=None, metadata=None)`

Update a memory with new text and/or metadata.

##### Arguments

```
# Required
category (str): The category of the memory.
id (str/int): The ID of the memory.

# Optional
text (str): The new text of the memory. Defaults to None.
metadata (dict): The new metadata of the memory. Defaults to None.
```

##### Example

```python
# with keyword arguments
update_memory(category="conversation", id=1, text="Okay, I will open the podbay doors.", metadata={ "speaker": "HAL", "sentiment": "positive" })

# with positional arguments
update_memory("conversation", 1, "Okay, I will open the podbay doors.")
```

## Delete a Memory

#### `delete_memory(category, id, contains_metadata=None, contains_text=None)`

Delete a memory by ID.

##### Arguments

```
# Required
category (str): The category of the memory.
id (str/int): The ID of the memory.

# Optional
```

##### Example

```python
>>> delete_memory("books", "1")
```

#### `delete_memories(category, document=None, metadata=None)`

Delete all memories in the category either by document, or by metadata, or by both.

##### Arguments

```
# Required
category (str): The category of the memory.

# Optional
document (str): Document text to match memories to delete. Defaults to None.
metadata (dict): Metadata to match memories to delete. Defaults to None.
```

##### Returns

```
bool: True if memories were deleted, False otherwise.
```

##### Example

```python
>>> delete_memories("books", document="Foundation", metadata={"author": "Isaac Asimov"})
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

#### `wipe_category(category)`

Delete an entire category of memories.

##### Arguments

```
# Required
category (str): The category to delete.

# Optional
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

#### `wipe_all_memories()`

Delete all memories across all categories.

##### Arguments

```
# Optional
```

##### Example

```python
>>> wipe_all_memories()
```

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

## Event API

A common need for the memory API is "events" -- logging when things happen sequentially. The event API provides a simple way to do this using the idea of "epochs". You can increment epochs as needed, and group events together within epochs. All of the events within a loop, or a conversation turn, for example, could be recorded as an epoch.

## `reset_epoch()`

The `reset_epoch` function resets the epoch in the agent's memory to 1. It wipes the "epoch" category and creates a new memory of 1.

**Usage:**

```python
reset_epoch()
```

**Example:**

```python
reset_epoch()
```

---

## `set_epoch(epoch)`

The `set_epoch` function sets the epoch in the agent's memory to the specified value.

**Arguments:**

- `epoch` (int): The desired epoch value.

**Usage:**

```python
set_epoch(epoch)
```

**Example:**

```python
set_epoch(5)
```

---

## `increment_epoch()`

The `increment_epoch` function increments the current epoch value by 1. It retrieves the current epoch from memory, increments it, and then writes the new epoch value to memory.

**Usage:**

```python
increment_epoch()
```

**Example:**

```python
increment_epoch()
```

---

## `get_epoch()`

The `get_epoch` function retrieves the current epoch value from the agent's memory.

**Usage:**

```python
get_epoch()
```

**Example:**

```python
current_epoch = get_epoch()
print(current_epoch)
```

---

## `create_event(text, metadata={}, embedding=None)`

The `create_event` function creates a new event in the agent's memory.

**Arguments:**

- `text` (str): The text content of the event.
- `metadata` (dict, optional): Additional metadata for the event. Defaults to {}.
- `embedding` (object, optional): An optional embedding for the event.

**Usage:**

```python
create_event(text, metadata={}, embedding=None)
```

**Example:**

```python
create_event("This is a test event", metadata={"test": "test"})
```

---

## `get_events(epoch=None, filter_metadata=None, n_results=10)`

The `get_events` function retrieves events from the agent's memory.

**Arguments:**

- `epoch` (int, optional): If specified, only retrieve events from this epoch.

**Usage:**

```python
get_events(epoch=None)
```

**Example:**

```python
events = get_events(1)
for event in events:
    print(event["document"])
```

# Clustering

## Overview

The `cluster` function in `agentmemory.clustering` provides an implementation of DBScan (Density-Based Spatial Clustering of Applications with Noise) clustering. It is designed to group memories in the agent's memory based on their similarity and proximity in the data space.

## Function Signature

```python
def cluster(epsilon, min_samples, category, filter_metadata=None, novel=False)
```

## Parameters

- `epsilon` (float): The maximum distance between two samples for one to be considered as in the neighborhood of the other.
- `min_samples` (int): The number of samples (or total weight) in a neighborhood for a point to be considered as a core point.
- `category` (str): The category of the collection to be clustered.
- `filter_metadata` (dict, optional): Additional metadata for filtering the memories before clustering. Defaults to None.
- `novel` (bool, optional): Whether to return only novel memories. Defaults to False.

## Memory Clustering

The `cluster` function updates memories directly with their cluster ID by performing the DBScan clustering algorithm. Memories with similar content and metadata will be grouped together into clusters. The clustering result will be reflected in the metadata of the memories.

## Memory Marking

- Memories with less than `min_samples` neighbors within a distance of `epsilon` will be marked as noise, and their cluster ID in the metadata will be set to "noise."
- Memories belonging to a cluster will have their cluster ID stored in the "cluster" field of the metadata.

## Usage

To perform clustering on a specific category of memories, call the `cluster` function with appropriate parameters:

```python
from agentmemory.clustering import cluster

# Example usage
epsilon = 0.1
min_samples = 3
category = "conversation"
filter_metadata = {"speaker": "HAL"}  # Optional metadata filter
novel = False  # Whether to return only novel memories

cluster(epsilon, min_samples, category, filter_metadata=filter_metadata, novel=novel)
```

## Note

- The clustering operation will directly update the memories' metadata in the specified category. Please make sure to have a backup of the data before performing clustering if necessary.

## References

For more information about DBScan clustering, refer to the original paper:
[DBScan Paper](https://www.aaai.org/Papers/KDD/1996/KDD96-037.pdf)

# Contributions Welcome

If you like this library and want to contribute in any way, please feel free to submit a PR and I will review it. Please note that the goal here is simplicity and accesibility, using common language and few dependencies.

<img src="resources/youcreatethefuture.jpg">
