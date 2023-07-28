import datetime

from agentmemory.helpers import (
    chroma_collection_to_list,
    debug_log,
    flatten_arrays,
    get_include_types,
)


from agentmemory.client import get_chroma_client, check_client_initialized


def create_memory(category, text, metadata={}, embedding=None, id=None):
    """
    Create a new memory in a collection.

    Arguments:
    category (str): Category of the collection.
    text (str): Document text.
    id (str): Unique id.
    metadata (dict): Metadata.

    Returns:
    None

    Example:
    >>> create_memory('sample_category', 'sample_text', id='sample_id', metadata={'sample_key': 'sample_value'})
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # get or create the collection
    memories = get_chroma_client().get_or_create_collection(category)

    # add timestamps to metadata
    metadata["created_at"] = datetime.datetime.now().timestamp()
    metadata["updated_at"] = datetime.datetime.now().timestamp()

    # if no id is provided, generate one based on count of documents in collection
    if id is None:
        id = str(memories.count())
        # pad the id with zeros to make it 16 digits long
        id = id.zfill(16)

    # for each field in metadata...
    # if the field is a boolean, convert it to a string
    for key, value in metadata.items():
        if isinstance(value, bool):
            print(f"WARNING: Boolean metadata field {key} converted to string")
            metadata[key] = str(value)

    # insert the document into the collection
    memories.upsert(
        ids=[str(id)],
        documents=[text],
        metadatas=[metadata],
        embeddings=[embedding] if embedding is not None else None,
    )

    debug_log(f"Created memory {id}: {text}", metadata)
    return id


def create_unique_memory(category, content, metadata={}, similarity=0.95):
    """
    Creates a new memory if there aren't any that are very similar to it

    Parameters:
    - content (str): The content of the memory.
    - metadata (dict, optional): Additional metadata for the memory.
        Defaults to empty dictionary.
    - similarity (float, optional): The threshold for determining similarity.
        Defaults to DEFAULT_SIMILARY_THRESHOLD.

    Returns: None
    """

    max_distance = 1.0 - similarity

    memories = search_memory(
        category,
        min_distance=0,
        max_distance=max_distance,
        search_text=content,
        n_results=1,
        filter_metadata={"unique": "True"},
    )

    if len(memories) == 0:
        metadata["unique"] = "True"
        create_memory(category, content, metadata=metadata)
        return

    metadata["unique"] = "False"
    metadata["related_to"] = memories[0]["id"]
    metadata["related_document"] = memories[0]["document"]
    create_memory(category, content, metadata=metadata)
    return id


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
    unique=False,
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
    unique (bool): Only include memories that are marked as unique

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
    memories = get_chroma_client().get_or_create_collection(category)

    if (memories.count()) == 0:
        return []

    # min n_results to prevent searching for more elements than are available
    n_results = min(n_results, memories.count())

    # get the types to include
    include_types = get_include_types(include_embeddings, include_distances)

    # filter_metadata is a dictionary of metadata to filter by
    if filter_metadata is not None and len(filter_metadata.keys()) > 1:
        # map each key:value in filter_metadata to an object shaped like { "key": { "$eq": "value" } }
        filter_metadata = [
            {key: {"$eq": value}} for key, value in filter_metadata.items()
        ]

        filter_metadata = {"$and": filter_metadata}

    if unique:
        if filter_metadata is None:
            filter_metadata = {}
        filter_metadata["unique"] = "True"

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
    memories = get_chroma_client().get_or_create_collection(category)

    # Get the types to include based on the function parameters
    include_types = get_include_types(include_embeddings, False)

    # Retrieve the memory with the given ID
    memory = memories.get(ids=[str(id)], limit=1, include=include_types)

    # Convert the collection to list format
    memory = chroma_collection_to_list(memory)

    debug_log(f"Got memory {id} from category {category}", memory)

    if len(memory) == 0:
        debug_log(
            f"WARNING: Tried to get memory {id} from category {category} but it does not exist",
            type="warning",
        )
        return None

    # Return the first (and only) memory in the list
    return memory[0]


def get_memories(
    category,
    sort_order="desc",
    contains_text=None,
    filter_metadata=None,
    n_results=20,
    include_embeddings=True,
    unique=False,
):
    """
    Retrieve a list of memories from a given category, sorted by ID, with optional filtering.

    Arguments:
        category (str): The category of the memories.
        sort_order (str, optional): The sorting order of the memories. Can be 'asc' or 'desc'. Defaults to 'desc'.
        filter_metadata (dict, optional): Filter to apply on metadata. Defaults to None.
        n_results (int, optional): The number of results to return. Defaults to 20.
        include_embeddings (bool, optional): Whether to include the embeddings. Defaults to True.
        unique (bool, optional): Whether to only include memories that are marked as unique. Defaults to False.

    Returns:
        list: List of retrieved memories.

    Example:
        >>> get_memories("books", sort_order="asc", n_results=10)
    """
    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = get_chroma_client().get_or_create_collection(category)

    # min n_results to prevent searching for more elements than are available
    n_results = min(n_results, memories.count())

    # Get the types to include based on the function parameters
    include_types = get_include_types(include_embeddings, False)

    where_document = None

    if contains_text is not None:
        where_document = {"$contains": contains_text}

    # filter_metadata is a dictionary of metadata to filter by
    if filter_metadata is not None and len(filter_metadata.keys()) > 1:
        # map each key:value in filter_metadata to an object shaped like { "key": { "$eq": "value" } }
        filter_metadata = [
            {key: {"$eq": value}} for key, value in filter_metadata.items()
        ]

        filter_metadata = {"$and": filter_metadata}

    if unique:
        if filter_metadata is None:
            filter_metadata = {}
        filter_metadata["unique"] = "True"

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


def update_memory(category, id, text=None, metadata=None):
    """
    Update a memory with new text and/or metadata.

    Arguments:
        category (str): The category of the memory.
        id (str/int): The ID of the memory.
        text (str, optional): The new text of the memory. Defaults to None.
        metadata (dict, optional): The new metadata of the memory. Defaults to None.

    Returns:
        None

    Raises:
        Exception: If neither text nor metadata is provided.

    Example:
        >>> update_memory("books", "1", text="New text", metadata={"author": "New author"})
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = get_chroma_client().get_or_create_collection(category)

    # If neither text nor metadata is provided, raise an exception
    if metadata is None and text is None:
        raise Exception("No text or metadata provided")
    if metadata is not None:
        # for each key value in metadata -- if the type is boolean, convert it to string
        for key, value in metadata.items():
            if isinstance(value, bool):
                print(f"WARNING: Boolean metadata field {key} converted to string")
                metadata[key] = str(value)

    metadata["updated_at"] = datetime.datetime.now().timestamp()

    documents = [text] if text is not None else None
    metadatas = [metadata] if metadata is not None else None

    # Update the memory with the new text and/or metadata
    memories.update(ids=[str(id)], documents=documents, metadatas=metadatas)

    debug_log(
        f"Updated memory {id} in category {category}",
        {"documents": documents, "metadatas": metadatas},
    )


def delete_memory(category, id):
    """
    Delete a memory by ID.

    Arguments:
        category (str): The category of the memory.
        id (str/int): The ID of the memory.

    Returns:
        None

    Example:
        >>> delete_memory("books", "1")
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = get_chroma_client().get_or_create_collection(category)

    if memory_exists(category, id) is False:
        debug_log(
            f"WARNING: Tried could not delete memory {id} in category {category}",
            type="warning",
        )
        return
    # Delete the memory
    memories.delete(ids=[str(id)])

    debug_log(f"Deleted memory {id} in category {category}")


def delete_memories(category, document=None, metadata=None):
    """
    Delete all memories in the category either by document, or by metadata, or by both.

    Arguments:
        category (str): The category of the memories.
        document (str, optional): The text of the memories to delete. Defaults to None.
        metadata (dict, optional): The metadata of the memories to delete. Defaults to None.

    Returns:
        bool: True if memories are deleted, False otherwise.

    Example:
        >>> delete_memories("books", document="Harry Potter", metadata={"author": "J.K. Rowling"})
    """
    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = get_chroma_client().get_or_create_collection(category)

    # Create a query to match either the document or the metadata
    if document is not None:
        memories.delete(where_document={"$contains": document})
    if metadata is not None:
        memories.delete(where=metadata)

    debug_log(f"Deleted memories from category {category}")

    return True


def delete_similar_memories(category, content, similarity_threshold=0.95):
    """
    Search for memories that are similar to the item that contains the content and removes it.

    Parameters:
    - content (str): The content to search for.
    - similarity_threshold (float, optional): The threshold for determining similarity. Defaults to DEFAULT_SIMILARY_THRESHOLD.

    Returns: bool - True if the memory item is found and removed, False otherwise.
    """

    memories = search_memory(category, content)
    memories_to_delete = []

    # find similar memories
    if len(memories) > 0:
        for memory in memories:
            goal_similarity = 1.0 - memory["distance"]
            if goal_similarity > similarity_threshold:
                memories_to_delete.append(memory["id"])
            else:
                # responses are sorted by similarity, so ignore the rest
                break

    if len(memories_to_delete) > 0:
        debug_log(
            f"Deleting similar memories to {content} in category {category}",
            memories_to_delete,
        )
        for memory in memories_to_delete:
            delete_memory(category, memory)
    debug_log(
        f"WARNING: Tried to delete similar memories to {content} in category {category} but none were found",
        type="warning",
    )
    return len(memories_to_delete) > 0


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
    memories = get_chroma_client().get_or_create_collection(category)

    # Check if there's a memory with the given ID and metadata
    memory = memories.get(ids=[str(id)], where=includes_metadata, limit=1)

    exists = len(memory["ids"]) > 0

    debug_log(
        f"Checking if memory {id} exists in category {category}. Exists: {exists}"
    )

    # Return True if at least one memory was found, False otherwise
    return exists


def count_memories(category, unique=False):
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
    memories = get_chroma_client().get_or_create_collection(category)

    if unique:
        memories = memories.get(where={"unique": "True"})

    debug_log(f"Counted memories in {category}: {memories.count()}")

    # Return the count of memories
    return memories.count()


def wipe_category(category):
    """
    Delete an entire category of memories.

    Arguments:
        category (str): The category to delete.

    Example:
        >>> wipe_category("books")
    """

    collection = None

    try:
        collection = get_chroma_client().get_collection(
            category
        )  # Check if the category exists
    except Exception:
        debug_log(
            f"WARNING: Tried to wipe category {category} but it does not exist",
            type="warning",
        )

    if collection is not None:
        # Delete the entire category
        get_chroma_client().delete_collection(category)


def wipe_all_memories():
    """
    Delete all memories across all categories.

    Example:
        >>> wipe_all_memories()
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized
    client = get_chroma_client()
    collections = client.list_collections()

    # Iterate over all collections
    for collection in collections:
        client.delete_collection(collection.name)

    debug_log("Wiped all memories", type="system")
