import time
from agentmemory import (
    search_memory,
    get_memory,
    create_memory,
    get_memories,
    update_memory,
    delete_memory,
    count_memories,
    wipe_category,
    wipe_all_memories,
    delete_memories,
)
from agentmemory.main import create_unique_memory, delete_similar_memories


def test_memory_creation_and_retrieval():
    wipe_category("test")
    # create 10 memories
    for i in range(20):
        create_memory(
            "test", "document " + str(i), metadata={"test": "test", "test2": "test2"}
        )

    memories = get_memories(
        "test", filter_metadata={"test": "test", "test2": "test2"}, n_results=10
    )

    # assert length of memories is 10
    assert len(memories) == 10

    # assert that the first memory is document 19
    assert memories[0]["document"] == "document 19"
    wipe_category("test")


def test_memory_deletion():
    wipe_category("test")
    # Delete memory test
    create_memory("test", "delete memory test", metadata={"test": "test"})
    memories = get_memories("test")
    memory_id = memories[0]["id"]
    num_memories = count_memories("test")
    # test delete_memory
    delete_memory("test", memory_id)
    assert count_memories("test") == num_memories - 1
    wipe_category("test")


def test_memory_update():
    wipe_category("test")
    create_memory("test", "update memory test", metadata={"test": "test"})
    memories = get_memories("test")
    memory_id = memories[0]["id"]

    update_memory("test", memory_id, "doc 1 updated no", metadata={"test": "test"})
    update_memory("test", memory_id, "doc 1 updated", metadata={"test": "test"})

    assert get_memory("test", memory_id)["document"] == "doc 1 updated"

    create_memory("test", "new memory test", metadata={"test": "test"})
    memories = get_memories("test")
    memory_id = memories[0]["id"]
    update_memory("test", memory_id, "doc 2 updated", metadata={"test": "test"})
    assert get_memory("test", memory_id)["document"] == "doc 2 updated"

    wipe_category("test")


def test_search_memory():
    wipe_category("test")
    # rewrite as a for loop
    for i in range(5):
        create_memory(
            "test",
            "document " + str(i + 1),
            metadata={"test": "test", "test2": "test2", "test3": "test3"},
        )

    search_results = search_memory(
        "test",
        "document 1",
        n_results=5,
        filter_metadata={"test": "test", "test2": "test2"},
        contains_text=None,
    )

    assert search_results[0]["document"] == "document 1"
    wipe_category("test")


def test_wipe_category():
    # test wipe_category
    wipe_category("test")
    for i in range(3):
        create_memory("test", "document " + str(i + 1), metadata={"test": "test"})
    assert count_memories("test") == 3
    wipe_category("test")
    assert count_memories("test") == 0


def test_count_memories():
    wipe_category("test")
    for i in range(3):
        create_memory("test", "document " + str(i + 1), metadata={"test": "test"})
    assert count_memories("test") == 3
    wipe_category("test")


def test_delete_memories():
    wipe_category("books")
    # create a memory to be deleted
    create_memory("books", "Foundation", metadata={"author": "Isaac Asimov"}, id="1")
    create_memory("books", "Foundation and Empire", metadata={"author": "Isaac Asimov"}, id="2")
    create_memory("books", "Second Foundation", metadata={"author": "Isaac Asimov"}, id="3")

    # assert the memory exists
    assert get_memory("books", "1") is not None

    # delete the memory
    assert delete_memories("books", "Foundation")
    assert delete_memories("books", metadata={"author": "Isaac Asimov"})

    # assert the memory does not exist anymore
    assert get_memory("books", "1") is None
    wipe_category("books")
    

def test_wipe_all_memories():
    create_memory("test", "test document")
    wipe_all_memories()
    assert count_memories("test") == 0


def test_memory_search_distance():
    wipe_category("test")
    create_memory("test", "cinammon duck cakes")
    max_dist_limited_memories = search_memory(
        "test", "cinammon duck cakes", max_distance=0.1
    )

    assert len(max_dist_limited_memories) == 1
    wipe_category("test")


def test_delete_similar_memories():
    wipe_category("test")
    # Create a memory and a similar memory
    create_memory("test", "similar_memory_1")
    create_memory("test", "similar_memory_2")

    # Test deleting a similar memory
    assert (
        delete_similar_memories(
            "test", "similar_memory_1", similarity_threshold=0.999999
        )
        is True
    )
    memories = get_memories("test")
    assert len(memories) == 1

    # Test deleting a non-similar memory
    assert delete_similar_memories("test", "not_similar_memory") is False
    memories = get_memories("test")
    assert len(memories) == 1
    wipe_category("test")


def test_create_unique_memory():
    wipe_category("test")
    # Test creating a novel memory
    create_unique_memory("test", "unique_memory_1", similarity=0.1)
    memories = get_memories("test")
    assert len(memories) == 1
    assert memories[0]["metadata"]["novel"] == "True"

    # Test creating a non-novel memory similar to the existing one
    create_unique_memory("test", "unique_memory_1", similarity=0.1)
    memories = get_memories("test")
    assert len(memories) == 2
    assert memories[0]["metadata"]["novel"] == "False"

    # Test creating a non-novel memory similar to the existing one
    create_unique_memory("test", "common_object_a", similarity=0.9)
    memories = get_memories("test")
    assert len(memories) == 3
    assert memories[0]["metadata"]["novel"] == "True"
    wipe_category("test")