import os
import uuid

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
    memory_id = create_memory("test", "not document 1", metadata={"test": "test"})
    assert isinstance(uuid.UUID(memory_id), uuid.UUID)  # Validate it's a UUID
    
    export_memory_to_file("./test_memories.json")
    import_file_to_memory("./test_memories.json")
    os.remove("./test_memories.json")

    test_memories = get_memories("test")
    assert test_memories[0]["document"] == "not document 1"


def test_export_memory_to_json():
    memory_id = create_memory("test", "document 1", metadata={"test": "test"})
    assert isinstance(uuid.UUID(memory_id), uuid.UUID)  # Validate it's a UUID
    
    export_dict = export_memory_to_json()
    assert "test" in export_dict
    assert export_dict["test"][0]["document"] == "document 1"


def test_import_json_to_memory():
    data = {
        "test": [{"document": "document 1", "metadata": {"test": "test"}, "id": str(uuid.uuid4())}]  # Generating a UUID
    }
    import_json_to_memory(data)
    test_memories = get_memories("test")
    assert test_memories[0]["document"] == "document 1"


def test_import_file_to_memory():
    memory_id = create_memory("test", "document 1", metadata={"test": "test"})
    assert isinstance(uuid.UUID(memory_id), uuid.UUID)  # Validate it's a UUID
    
    export_memory_to_file("./test_memories.json")
    wipe_all_memories()
    import_file_to_memory("./test_memories.json")
    os.remove("./test_memories.json")
    
    test_memories = get_memories("test")
    assert test_memories[0]["document"] == "document 1"