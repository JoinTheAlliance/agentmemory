import os

from agentmemory import (
    create_memory,
    export_memory_to_file,
    export_memory_to_json,
    get_memories,
    import_file_to_memory,
    import_json_to_memory,
    wipe_all_memories,
)


def test_memory_export_import():
    wipe_all_memories()
    create_memory("test", "not document 1", metadata={"test": "test"})
    export_memory_to_file("./test_memories.json")
    import_file_to_memory("./test_memories.json")
    os.remove("./test_memories.json")

    test_memories = get_memories("test")
    assert test_memories[0]["document"] == "not document 1"


def test_export_memory_to_json():
    create_memory("test", "document 1", metadata={"test": "test"})
    export_dict = export_memory_to_json()
    assert "test" in export_dict
    assert export_dict["test"][0]["document"] == "document 1"


def test_import_json_to_memory():
    data = {
        "test": [{"document": "document 1", "metadata": {"test": "test"}, "id": "1"}]
    }
    import_json_to_memory(data)
    test_memories = get_memories("test")
    assert test_memories[0]["document"] == "document 1"


def test_import_file_to_memory():
    create_memory("test", "document 1", metadata={"test": "test"})
    export_memory_to_file("./test_memories.json")
    # Wipe out all memories
    wipe_all_memories()
    # Now import from the file we exported
    import_file_to_memory("./test_memories.json")
    # Remove the file after test
    os.remove("./test_memories.json")
    test_memories = get_memories("test")
    assert test_memories[0]["document"] == "document 1"
