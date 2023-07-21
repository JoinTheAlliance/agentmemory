import chromadb

persist_directory = "./memory"
client = chromadb.PersistentClient(persist_directory)

def check_client_initialized():
    """
    Check if the client has been initialized, and initialize it if not.

    Example:
        >>> check_client_initialized()
    """
    if get_chroma_client() is None:
        set_chroma_client(chromadb.PersistentClient(persist_directory))

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
    global persist_directory
    if client is None:
        client = chromadb.PersistentClient(path=persist_directory)
    return client


def set_chroma_client(storage_path):
    """
    Set the chromadb client.

    Args:
        persist_directory (string): The path to the new directory.

    Returns:
        None

    Example:
        >>> set_chroma_client(new_client)
    """
    global client
    global persist_directory
    persist_directory = storage_path
    client = chromadb.PersistentClient(persist_directory)

