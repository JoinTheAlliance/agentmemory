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


import json
import time
from agentmemory import create_memory


def seed(seed_input):
    """
    Seed the memory bank from a JSON object or file

    Parameters:
    - data (dict): the JSON object to seed from

    Returns:
    - None
    """
    if seed_input is False or seed_input is None:
        return

    def seed_from_file(filename="./seeds.json"):
        with open(filename, "r") as f:
            seed_from_json(json.load(f))

    def seed_from_json(data):
        timestamps = [time.time() - (10 * i) for i in range(len(data))]
        for i, entry in enumerate(data):
            timestamp = timestamps[i]
            entry["metadata"]["created_at"] = str(timestamp)
            create_memory(entry["collection"], entry["message"], entry["metadata"])

    # if seed is a dictionary, use it as the seed data
    if isinstance(seed_input, dict):
        seed_from_json(seed_input)

    elif isinstance(seed_input, str) and seed_input.endswith(".json"):
        seed_from_file(seed_input)

    elif seed_input is True:
        seed_from_file()
    # if seed is a string, try parsing it as a json file
    elif seed_input is not None:
        try:
            # parse string to dict
            seed_data = json.loads(seed_input)
            seed_from_json(seed_data)
        except:
            print("Invalid seed data. Must be a JSON file or a JSON string.")
            return
