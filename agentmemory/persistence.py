import json
from agentmemory import (
    create_memory,
    get_memories,
    wipe_all_memories,
)
from agentmemory.client import get_chroma_client


def export_memory_to_json(include_embeddings=True):
    """
    Export all memories to a dictionary, optionally including embeddings.

    Arguments:
        include_embeddings (bool, optional): Whether to include memory embeddings in the output.
                                             Defaults to True.

    Returns:
        dict: A dictionary with collection names as keys and lists of memories as values.

    Example:
        >>> export_memory_to_json()
    """

    collections = get_chroma_client().list_collections()

    collections_dict = {}

    # Iterate over all collections
    for collection in collections:
        print(collection)
        collection_name = collection.name
        print("collection_name")
        print(collection_name)

        collections_dict[collection_name] = []

        # Get all memories from the current collection
        memories = get_memories(collection_name, include_embeddings=include_embeddings)
        for memory in memories:
            # Append each memory to its corresponding collection list
            collections_dict[collection_name].append(memory)

    return collections_dict


def export_memory_to_file(path="./memory.json", include_embeddings=True):
    """
    Export all memories to a JSON file, optionally including embeddings.

    Arguments:
        path (str, optional): The path to the output file. Defaults to "./memory.json".
        include_embeddings (bool, optional): Whether to include memory embeddings in the output.
                                             Defaults to True.

    Example:
        >>> export_memory_to_file(path="/path/to/output.json")
    """

    # Export the database to a dictionary
    collections_dict = export_memory_to_json(include_embeddings)

    # Write the dictionary to a JSON file
    with open(path, "w") as outfile:
        json.dump(collections_dict, outfile)


def import_json_to_memory(data, replace=True):
    """
    Import memories from a dictionary into the current database.

    Arguments:
        data (dict): A dictionary with collection names as keys and lists of memories as values.
        replace (bool, optional): Whether to replace existing memories. If True, all existing memories
                                  will be deleted before import. Defaults to True.

    Example:
        >>> import_json_to_memory(data)
    """

    # If replace flag is set to True, wipe out all existing memories
    if replace:
        wipe_all_memories()

    # Iterate over all collections in the input data
    for category in data:
        # Iterate over all memories in the current collection
        for memory in data[category]:
            # Create a new memory in the current category
            create_memory(
                category,
                text=memory["document"],
                metadata=memory["metadata"],
                id=memory["id"],
                embedding=memory.get("embedding", None),
            )


def import_file_to_memory(path="./memory.json", replace=True):
    """
    Import memories from a JSON file into the current database.

    Arguments:
        path (str, optional): The path to the input file. Defaults to "./memory.json".
        replace (bool, optional): Whether to replace existing memories. If True, all existing memories
                                  will be deleted before import. Defaults to True.

    Example:
        >>> import_file_to_memory(path="/path/to/input.json")
    """

    # Read the input JSON file
    with open(path, "r") as infile:
        data = json.load(infile)

    # Import the data into the database
    import_json_to_memory(data, replace)
