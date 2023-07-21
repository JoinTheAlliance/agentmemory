import chromadb

from agentmemory.helpers import debug_log

storage_path = "./memory"
client = chromadb.PersistentClient(storage_path)


def check_client_initialized():
    """
    Check if the client has been initialized, and initialize it if not.

    Example:
        >>> check_client_initialized()
    """
    if get_chroma_client() is None:
        set_chroma_client(chromadb.PersistentClient(storage_path))


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
    global storage_path
    if client is None:
        client = chromadb.PersistentClient(path=storage_path)
    return client


def set_chroma_client(data_storage_path=storage_path):
    """
    Set the chromadb client.

    Args:
        storage_path (string): The path to the new directory.

    Returns:
        None

    Example:
        >>> set_chroma_client(new_client)
    """
    global client
    global storage_path
    storage_path = data_storage_path
    client = chromadb.PersistentClient(storage_path)
    debug_log("Set chroma client", {"storage_path": storage_path}, "system")
