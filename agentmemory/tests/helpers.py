import os

import pytest

from agentmemory import (
    chroma_collection_to_list,
    create_memory,
    get_client,
    list_to_chroma_collection,
    wipe_all_memories,
)
from agentmemory.helpers import flatten_arrays, get_include_types
from agentmemory.persistence import (
    export_memory_to_file,
    export_memory_to_json,
    import_file_to_memory,
    import_json_to_memory,
)


def test_chroma_collection_conversion():
    wipe_all_memories()
    create_memory("test", "document 1", metadata={"test": "test"})
    create_memory("test", "document 2", metadata={"test": "test"})
    collection = get_client().get_or_create_collection("test")
    test_collection_data = collection.peek()
    list_data = chroma_collection_to_list(test_collection_data)

    assert list_data[0]["document"] == "document 1"

    new_collection_data = list_to_chroma_collection(list_data)

    assert test_collection_data["documents"][0] == "document 1"
    assert new_collection_data == test_collection_data
    assert len(list_data) == 2, "List data should have length 2"
    assert (
        list_data[1]["document"] == "document 2"
    ), "Second document should be 'document 2'"

    # additional assert to check conversion from list back to collection
    assert (
        new_collection_data["documents"][1] == "document 2"
    ), "Second document in collection should be 'document 2'"
    assert (
        new_collection_data["metadatas"] == test_collection_data["metadatas"]
    ), "Metadatas should match"
    assert new_collection_data["ids"] == test_collection_data["ids"], "Ids should match"


def test_get_chroma_client():
    wipe_all_memories()
    client = get_client()
    assert client is not None, "Client should not be None"


def test_flatten_arrays():
    test_dict = {
        "metadatas": [["metadata1"], ["metadata2"]],
        "documents": [["document1"], ["document2"]],
        "ids": [["id1"], ["id2"]],
    }
    flattened = flatten_arrays(test_dict)
    assert flattened["metadatas"] == [
        "metadata1",
        "metadata2",
    ], "Flatten metadatas failed"
    assert flattened["documents"] == [
        "document1",
        "document2",
    ], "Flatten documents failed"
    assert flattened["ids"] == ["id1", "id2"], "Flatten ids failed"


def test_get_include_types():
    include_types = get_include_types(True, False)
    assert include_types == [
        "metadatas",
        "documents",
        "embeddings",
    ], "Include embeddings failed"

    include_types = get_include_types(False, True)
    assert include_types == [
        "metadatas",
        "documents",
        "distances",
    ], "Include distances failed"

    include_types = get_include_types(True, True)
    assert include_types == [
        "metadatas",
        "documents",
        "embeddings",
        "distances",
    ], "Include both failed"

    include_types = get_include_types(False, False)
    assert include_types == ["metadatas", "documents"], "Exclude both failed"


def test_export_memory_to_json():
    # Test with default parameters
    data = export_memory_to_json()
    assert isinstance(data, dict), "Data should be a dictionary"

    # Test without embeddings
    data = export_memory_to_json(include_embeddings=False)
    for collection in data.values():
        for memory in collection:
            assert "embedding" not in memory, "No memory should have embeddings"

    # Test with empty database
    wipe_all_memories()
    data = export_memory_to_json()
    assert len(data) == 0, "No collections should exist"


def test_export_memory_to_file():
    # Test with default parameters
    export_memory_to_file()
    assert os.path.isfile("./memory.json"), "File should be created"
    # rm file after test
    os.remove("./memory.json")

    # Test with specified path
    export_memory_to_file(path="./test_memory.json")
    assert os.path.isfile("./test_memory.json"), "File should be created"
    # rm file after test
    os.remove("./test_memory.json")

    # Test with invalid path
    with pytest.raises(Exception):
        export_memory_to_file(path="")


def test_import_json_to_memory():
    # Test with empty dictionary
    import_json_to_memory(data={})
    collections = get_client().list_collections()
    assert len(collections) == 0, "No collections should exist"

    # Test with replace=False
    create_memory("test", "document 1")
    data = export_memory_to_json()
    import_json_to_memory(data, replace=False)
    collections = get_client().list_collections()
    assert len(collections) == 1, "Only one collection should exist"

    # Test with invalid data
    with pytest.raises(Exception):
        import_json_to_memory(data="test")


def test_import_file_to_memory():
    create_memory("test", "document 1")
    # Test with default parameters
    export_memory_to_file()
    import_file_to_memory()
    assert get_client().list_collections(), "Collections should exist"

    # Test with specified path
    export_memory_to_file(path="./test_memory.json")
    import_file_to_memory(path="./test_memory.json")
    assert get_client().list_collections(), "Collections should exist"

    # Test with invalid path
    with pytest.raises(Exception):
        import_file_to_memory(path="")
