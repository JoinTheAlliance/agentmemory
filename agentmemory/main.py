import datetime
import chromadb

persistent_path = None
client = None

from utils import (
    collection_to_list,
    flatten_arrays,
    get_include_types,
)

def get_client():
    """
    Get the chromadb client.

    Returns:
    chromadb.Client: Chromadb client.

    Example:
    >>> get_client()
    <chromadb.client.Client object at 0x7f7b9c2f0d00>
    """
    global client
    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized
    return client


def create_memory(category, text, metadata=None, id=None, persist=True):
    """
    Function to create a new memory in a collection.

    Parameters:
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
        client.persist()


def search_memory(
    category,
    search_text,
    n_results=5,
    filter_metadata=None,
    contains_text=None,
    include_embeddings=True,
    include_distances=True,
):
    """
    Function to search a collection with given query texts.

    Parameters:
    category (str): Category of the collection.
    search_text (str): Text to be searched.
    n_results (int): Number of results to be returned.
    filter_metadata (dict): Metadata for filtering the results.
    contains_text (str): Text that must be contained in the documents.
    include_embeddings (bool): Whether to include embeddings in the results.
    include_distances (bool): Whether to include distances in the results.

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
    list = collection_to_list(query)
    return list


def get_memory(category, id, include_embeddings=True):
    """
    Retrieve a specific memory from a given category based on its ID.

    Args:
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
    memory = collection_to_list(memory)

    # Return the first (and only) memory in the list
    return memory[0]


def get_memories(
    category,
    sort_order="desc",
    filter_metadata=None,
    n_results=20,
    include_embeddings=True,
):
    """
    Retrieve a list of memories from a given category, sorted by ID, with optional filtering.

    Args:
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

    # Retrieve all memories that meet the given metadata filter
    memories = memories.get(where=filter_metadata, include=include_types)

    # Convert the collection to list format
    memories = collection_to_list(memories)

    # Sort memories by ID. If sort_order is 'desc', then the reverse parameter will be True, and memories will be sorted in descending order.
    memories.sort(key=lambda x: x["id"], reverse=sort_order == "desc")

    # Only keep the top n_results memories
    memories = memories[:n_results]

    return memories


def update_memory(category, id, text=None, metadata=None, persist=True):
    """
    Update a specific memory with new text and/or metadata.

    Args:
        category (str): The category of the memory.
        id (str/int): The ID of the memory.
        text (str, optional): The new text of the memory. Defaults to None.
        metadata (dict, optional): The new metadata of the memory. Defaults to None.
        persist (bool, optional): Whether to persist the changes to disk. Defaults to True.

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
        client.persist()


def delete_memory(
    category, id, contains_metadata=None, contains_text=None, persist=True
):
    """
    Delete a specific memory based on its ID and optionally on matching metadata and/or text.

    Args:
        category (str): The category of the memory.
        id (str/int): The ID of the memory.
        contains_metadata (dict, optional): Metadata that the memory should contain. Defaults to None.
        contains_text (str, optional): Text that the memory should contain. Defaults to None.
        persist (bool, optional): Whether to persist the changes to disk. Defaults to True.

    Example:
        >>> delete_memory("books", "1")
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = client.get_or_create_collection(category)

    # If contains_text is provided, convert it to a $contains query
    if contains_text is not None:
        contains_text = {"$contains": contains_text}

    # Delete the memory
    memories.delete(
        ids=[str(id)], where=contains_metadata, where_document=contains_text
    )

    if persist:
        client.persist()


def memory_exists(category, id, includes_metadata=None):
    """
    Check if a memory with a specific ID exists in a given category.

    Args:
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

    # Return True if at least one memory was found, False otherwise
    return len(memory["ids"]) > 0


def wipe_category(category, persist=True):
    """
    Delete an entire category of memories.

    Args:
        category (str): The category to delete.
        persist (bool, optional): Whether to persist the changes to disk. Defaults to True.

    Example:
        >>> wipe_category("books")
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Delete the entire category
    client.delete_collection(category)

    if persist:
        client.persist()


def count_memories(category):
    """
    Count the number of memories in a given category.

    Args:
        category (str): The category of the memories.

    Returns:
        int: The number of memories.

    Example:
        >>> count_memories("books")
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Get or create the collection for the given category
    memories = client.get_or_create_collection(category)

    # Return the count of memories
    return memories.count()


def wipe_all_memories(persist=True):
    """
    Delete all memories across all categories.

    Args:
        persist (bool, optional): Whether to persist the changes to disk. Defaults to True.

    Example:
        >>> wipe_all_memories()
    """

    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized

    # Reset the entire client, which deletes all collections and their memories
    client.reset()

    if persist:
        client.persist()


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
                chromadb.Settings(chroma_db_impl="duckdb+parquet",persist_directory=persistent_path)
            )
        else:
            client = chromadb.Client(chromadb.Settings(chroma_db_impl="duckdb+parquet",persist_directory="./memory"))


def set_storage_path(path):
    """
    Set the path to persist the database to.

    Example:
        >>> set_storage_path("path/to/persistent/directory")
    """
    global persistent_path
    global client
    persistent_path = path
    if client is not None:
        client.persist()
    client = chromadb.Client(chromadb.Settings(chroma_db_impl="duckdb+parquet",persist_directory=persistent_path))


def save_memory():
    """
    Save the database to disk.

    Example:
        >>> save_to_disk()
    """
    check_client_initialized()  # client is lazy loaded, so make sure it is is initialized
    client.persist()
