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
)


def test_memory_creation_and_retrieval():
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


def test_memory_deletion():
    # Delete memory test
    create_memory("test", "delete memory test", metadata={"test": "test"})
    memories = get_memories("test")
    memory_id = memories[0]["id"]
    num_memories = count_memories("test")
    # test delete_memory
    delete_memory("test", memory_id)
    assert count_memories("test") == num_memories - 1


def test_memory_update():
    create_memory("test", "update memory test", metadata={"test": "test"})
    memories = get_memories("test")
    memory_id = memories[0]["id"]

    update_memory("test", memory_id, "doc 1 updated", metadata={"test": "test"})
    assert get_memory("test", memory_id)["document"] == "doc 1 updated"


def test_search_memory():
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


def test_wipe_category():
    # test wipe_category
    wipe_category("test")
    assert count_memories("test") == 0


def test_count_memories():
    for i in range(3):
        create_memory("test", "document " + str(i + 1), metadata={"test": "test"})
    assert count_memories("test") == 3


def test_memory_search_distance():
    create_memory("test", "cinammon duck cakes")
    max_dist_limited_memories = search_memory(
        "test", "cinammon duck cakes", max_distance=0.1
    )

    assert len(max_dist_limited_memories) == 1


def test_wipe_all_memories():
    wipe_all_memories()
    assert count_memories("test") == 0
