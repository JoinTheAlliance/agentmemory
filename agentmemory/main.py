import json
import os
import datetime

import chromadb

persistent_path = None
client = None


def create_memory(category, text, metadata={}, id=None, persist=True):
    """
    Create a new memory in a collection.

    Arguments:
    category (str): Category of the collection.
    text (str): Document text.
    id (str): Unique id.
    metadata (dict): Metadata.
    persist (bool, optional): Whether to persist the changes to disk. Defaults to True.

    Returns:
    None

    Example:
    >>> create_memory('sample_category', 'sample_text', id='sample_id', metadata={'sample_key': 'sample_value'})
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # get or create the collection
    memories = client.get_or_create_collection(category)

    # add timestamps to metadata
    metadata["created_at"] = datetime.datetime.now().timestamp()
    metadata["updated_at"] = datetime.datetime.now().timestamp()

    # if no id is provided, generate one based on count of documents in collection
    if id is None:
        id = str(memories.count())

    # insert the document into the collection
    memories.upsert(
        ids=[id],
        documents=[text],
        metadatas=[metadata],
    )

    if persist:
        persist_memory()

    debug_log(f"Created memory {id}: {text}", metadata)


def search_memory(
    category,
    search_text,
    n_results=5,
    filter_metadata=None,
    contains_text=None,
    include_embeddings=True,
    include_distances=True,
    max_distance=None,  # 0.0 - 1.0
    min_distance=None,  # 0.0 - 1.0
):
    """
    Cearch a collection with given query texts.

    Arguments:
    category (str): Category of the collection.
    search_text (str): Text to be searched.
    n_results (int): Number of results to be returned.
    filter_metadata (dict): Metadata for filtering the results.
    contains_text (str): Text that must be contained in the documents.
    include_embeddings (bool): Whether to include embeddings in the results.
    include_distances (bool): Whether to include distances in the results.
    max_distance (float): Only include memories with this distance threshold maximum.
        0.1 = most memories will be exluded, 1.0 = no memories will be excluded
    min_distance (float): Only include memories that are at least this distance
        0.0 = No memories will be excluded, 0.9 = most memories will be excluded

    Returns:
    list: List of search results.

    Example:
    >>> search_memory('sample_category', 'search_text', n_results=2, filter_metadata={'sample_key': 'sample_value'}, contains_text='sample', include_embeddings=True, include_distances=True)
    [{'metadata': '...', 'document': '...', 'id': '...'}, {'metadata': '...', 'document': '...', 'id': '...'}]
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # check if contains_text is provided and format it for the query
    if contains_text is not None:
        contains_text = {"$contains": contains_text}

    # get or create the collection
    memories = client.get_or_create_collection(category)

    # get the types to include
    include_types = get_include_types(include_embeddings, include_distances)

    # perform the query and get the response
    query = memories.query(
        query_texts=[search_text],
        where=filter_metadata,
        where_document=contains_text,
        n_results=n_results,
        include=include_types,
    )

    # flatten the arrays in the query response
    query = flatten_arrays(query)

    # convert the query response to list and return
    result_list = chroma_collection_to_list(query)

    if min_distance is not None and min_distance > 0:
        result_list = [res for res in result_list if res["distance"] >= min_distance]

    if max_distance is not None and max_distance < 1.0:
        result_list = [res for res in result_list if res["distance"] <= max_distance]

    debug_log(f"Searched memory: {search_text}", result_list)

    return result_list


def get_memory(category, id, include_embeddings=True):
    """
    Retrieve a specific memory from a given category based on its ID.

    Arguments:
        category (str): The category of the memory.
        id (str/int): The ID of the memory.
        include_embeddings (bool, optional): Whether to include the embeddings. Defaults to True.

    Returns:
        dict: The retrieved memory.

    Example:
        >>> get_memory("books", "1")
    """
    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = client.get_or_create_collection(category)

    # Get the types to include based on the function parameters
    include_types = get_include_types(include_embeddings, False)

    # Retrieve the memory with the given ID
    memory = memories.get(ids=[str(id)], limit=1, include=include_types)

    # Convert the collection to list format
    memory = chroma_collection_to_list(memory)

    debug_log(f"Got memory {id} from category {category}", memory)

    # Return the first (and only) memory in the list
    return memory[0]


def get_memories(
    category,
    sort_order="desc",
    contains_text=None,
    filter_metadata=None,
    n_results=20,
    include_embeddings=True,
):
    """
    Retrieve a list of memories from a given category, sorted by ID, with optional filtering.

    Arguments:
        category (str): The category of the memories.
        sort_order (str, optional): The sorting order of the memories. Can be 'asc' or 'desc'. Defaults to 'desc'.
        filter_metadata (dict, optional): Filter to apply on metadata. Defaults to None.
        n_results (int, optional): The number of results to return. Defaults to 20.
        include_embeddings (bool, optional): Whether to include the embeddings. Defaults to True.

    Returns:
        list: List of retrieved memories.

    Example:
        >>> get_memories("books", sort_order="asc", n_results=10)
    """
    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = client.get_or_create_collection(category)

    # Get the types to include based on the function parameters
    include_types = get_include_types(include_embeddings, False)

    where_document = None

    if contains_text is not None:
        where_document = {"$contains": contains_text}

    # Retrieve all memories that meet the given metadata filter
    memories = memories.get(
        where=filter_metadata, where_document=where_document, include=include_types
    )

    # Convert the collection to list format
    memories = chroma_collection_to_list(memories)

    # Sort memories by ID. If sort_order is 'desc', then the reverse parameter will be True, and memories will be sorted in descending order.
    memories.sort(key=lambda x: x["id"], reverse=sort_order == "desc")

    # Only keep the top n_results memories
    memories = memories[:n_results]

    debug_log(f"Got memories from category {category}", memories)

    return memories


def update_memory(category, id, text=None, metadata=None, persist=True):
    """
    Update a memory with new text and/or metadata.

    Arguments:
        category (str): The category of the memory.
        id (str/int): The ID of the memory.
        text (str, optional): The new text of the memory. Defaults to None.
        metadata (dict, optional): The new metadata of the memory. Defaults to None.
        persist (bool, optional): Whether to persist the changes to disk. Defaults to True.

    Returns:
        None

    Raises:
        Exception: If neither text nor metadata is provided.

    Example:
        >>> update_memory("books", "1", text="New text", metadata={"author": "New author"})
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = client.get_or_create_collection(category)

    # If neither text nor metadata is provided, raise an exception
    if metadata is None and text is None:
        raise Exception("No text or metadata provided")

    metadata["updated_at"] = datetime.datetime.now().timestamp()

    documents = [text] if text is not None else None
    metadatas = [metadata] if metadata is not None else None

    # Update the memory with the new text and/or metadata
    memories.update(ids=[str(id)], documents=documents, metadatas=metadatas)

    if persist:
        persist_memory()

    debug_log(
        f"Updated memory {id} in category {category}",
        {"documents": documents, "metadatas": metadatas},
    )


def delete_memory(category, id, persist=True):
    """
    Delete a memory by ID.

    Arguments:
        category (str): The category of the memory.
        id (str/int): The ID of the memory.
        persist (bool, optional): Whether to persist the changes to disk. Defaults to True.

    Returns:
        None

    Example:
        >>> delete_memory("books", "1")
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = client.get_or_create_collection(category)

    # Delete the memory
    memories.delete(ids=[str(id)])

    if persist:
        persist_memory()

    debug_log(f"Deleted memory {id} in category {category}")


def memory_exists(category, id, includes_metadata=None):
    """
    Check if a memory with a specific ID exists in a given category.

    Arguments:
        category (str): The category of the memory.
        id (str/int): The ID of the memory.
        includes_metadata (dict, optional): Metadata that the memory should include. Defaults to None.

    Returns:
        bool: True if the memory exists, False otherwise.

    Example:
        >>> memory_exists("books", "1")
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = client.get_or_create_collection(category)

    # Check if there's a memory with the given ID and metadata
    memory = memories.get(ids=[str(id)], where=includes_metadata, limit=1)

    exists = len(memory["ids"]) > 0

    debug_log(
        f"Checking if memory {id} exists in category {category}. Exists: {exists}"
    )

    # Return True if at least one memory was found, False otherwise
    return exists


def wipe_category(category, persist=True):
    """
    Delete an entire category of memories.

    Arguments:
        category (str): The category to delete.
        persist (bool, optional): Whether to persist the changes to disk. Defaults to True.

    Example:
        >>> wipe_category("books")
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Delete the entire category
    client.delete_collection(category)

    if persist:
        persist_memory()

    debug_log(f"Wiped category {category}")


def count_memories(category):
    """
    Count the number of memories in a given category.

    Arguments:
        category (str): The category of the memories.

    Returns:
        int: The number of memories.

    Example:
        >>> count_memories("books")
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = client.get_or_create_collection(category)

    debug_log(f"Counted memories in {category}: {memories.count()}")

    # Return the count of memories
    return memories.count()


def wipe_all_memories(persist=True):
    """
    Delete all memories across all categories.

    Arguments:
        persist (bool, optional): Whether to persist the changes to disk. Defaults to True.

    Example:
        >>> wipe_all_memories()
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Reset the entire client, which deletes all collections and their memories
    client.reset()

    if persist:
        persist_memory()

    debug_log(f"Wiped all memories")


def check_client_initialized():
    """
    Check if the client has been initialized, and initialize it if not.

    Example:
        >>> check_client_initialized()
    """
    global client
    if client is None:
        if persistent_path is not None:
            client = chromadb.Client(
                chromadb.Settings(
                    chroma_db_impl="duckdb+parquet", persist_directory=persistent_path
                )
            )
        else:
            client = chromadb.Client(
                chromadb.Settings(
                    chroma_db_impl="duckdb+parquet", persist_directory="./memory"
                )
            )

    debug_log(f"Checking if client is initialized")


def set_storage_path(path):
    """
    Set the path to persist the database to.

    Arguments:
        path (string): the path to save to

    Example:
        >>> set_storage_path("path/to/persistent/directory")
    """
    global persistent_path
    global client
    persistent_path = path
    if client is not None:
        persist_memory()
    client = chromadb.Client(
        chromadb.Settings(
            chroma_db_impl="duckdb+parquet", persist_directory=persistent_path
        )
    )

    debug_log(f"Set storage path to {path}")


def save_memory():
    """
    Save the database to disk.

    Example:
        >>> save_to_disk()
    """
    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized
    persist_memory()

    debug_log(f"Saved memory")


### LOW LEVEL FUNCTIONS ###


def debug_log(message, dict=None):
    # Check if the DEBUG_MEMORY environment variable is set to 'true'
    if os.getenv("DEBUG_MEMORY", "false").lower() == "true":
        if dict is not None:
            message = message + f" ({json.dumps(dict)})"
        print(message)


def persist_memory():
    if persistent_path is not None:
        client.persist()
        debug_log(f"Persisted memory")


def get_chroma_client():
    """
    Get the chromadb client.

    Returns:
    chromadb.Client: Chromadb client.

    Example:
    >>> get_chroma_client()
    <chromadb.client.Client object at 0x7f7b9c2f0d00>
    """
    global client
    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized
    debug_log(f"Getting chroma client")
    return client


def chroma_collection_to_list(collection):
    """
    Function to convert collection (dictionary) to list.

    Arguments:
    collection (dict): Dictionary to be converted.

    Returns:
    list: Converted list of dictionaries.

    Example:
    >>> chroma_collection_to_list(collection)
    [{'metadata': '...', 'document': '...', 'id': '...'}]
    """

    list = []

    # If there are no embeddings, zip metadatas, documents and ids together
    if collection.get("embeddings", None) is None:
        for metadata, document, id in zip(
            collection["metadatas"], collection["documents"], collection["ids"]
        ):
            # append the zipped data as dictionary to the list
            list.append({"metadata": metadata, "document": document, "id": id})

        return list

    # if distance is none, zip metadatas, documents, ids and embeddings together
    if collection.get("distances", None) is None:
        for metadata, document, id, embedding in zip(
            collection["metadatas"],
            collection["documents"],
            collection["ids"],
            collection["embeddings"],
        ):
            # append the zipped data as dictionary to the list
            list.append(
                {
                    "metadata": metadata,
                    "document": document,
                    "embedding": embedding,
                    "id": id,
                }
            )

        return list

    # if embeddings are present, zip all data including embeddings and distances
    for metadata, document, id, embedding, distance in zip(
        collection["metadatas"],
        collection["documents"],
        collection["ids"],
        collection["embeddings"],
        collection.get("distances"),
    ):
        # append the zipped data as dictionary to the list
        list.append(
            {
                "metadata": metadata,
                "document": document,
                "embedding": embedding,
                "distance": distance,
                "id": id,
            }
        )
    debug_log(f"Collection to list", {"collection": collection, "list": list})
    return list


def list_to_chroma_collection(list):
    """
    Function to convert list (of dictionaries) to collection (dictionary).

    Arguments:
    list (list): List to be converted.

    Returns:
    dict: Converted dictionary.

    Example:
    >>> list_to_chroma_collection(list)
    {'metadatas': ['...'], 'documents': ['...'], 'ids': ['...'], 'embeddings': ['...'], 'distances': ['...']}
    """
    collection = {
        "metadatas": [],
        "documents": [],
        "ids": [],
        "embeddings": [],
        "distances": [],
    }

    # iterate over items in list
    for item in list:
        # add corresponding values to respective keys in collection
        collection["metadatas"].append(item["metadata"])
        collection["documents"].append(item["document"])
        collection["ids"].append(item["id"])
        # check for presence of embeddings, and add if present
        if "embedding" in item:
            collection["embeddings"].append(item["embedding"])

        if "distance" in item:
            collection["distances"].append(item["distance"])

    # delete keys from collection if no values are present
    if len(collection["embeddings"]) == 0:
        del collection["embeddings"]

    if len(collection["distances"]) == 0:
        del collection["distances"]

    debug_log(f"List to collection", {"collection": collection, "list": list})
    return collection


def flatten_arrays(collection):
    """
    Function to flatten the arrays in the collection.

    Arguments:
    collection (dict): Dictionary with nested arrays.

    Returns:
    dict: Flattened dictionary.

    Example:
    >>> flatten_arrays(collection)
    {'metadatas': ['...'], 'documents': ['...'], 'ids': ['...'], 'embeddings': ['...'], 'distances': ['...']}
    """

    # Iterate over each key in collection
    for key in collection:
        # If no values, continue to next iteration
        if collection[key] == None:
            continue
        # Flatten the arrays into a single array for each key
        collection[key] = [item for sublist in collection[key] for item in sublist]

    return collection


def get_include_types(include_embeddings, include_distances):
    """
    Function to get the types to include in results.

    Arguments:
    include_embeddings (bool): Whether to include embeddings in the results.
    include_distances (bool): Whether to include distances in the results.

    Returns:
    list: List of types to be included.

    Example:
    >>> get_include_types(True, False)
    ['metadatas', 'documents', 'embeddings']
    """
    # always include metadatas and documents
    include_types = ["metadatas", "documents"]

    # include embeddings if specified
    if include_embeddings:
        include_types.append("embeddings")

    # include distances if specified
    if include_distances:
        include_types.append("distances")

    debug_log(f"Get include types", {"include_types": include_types})
    return include_types
