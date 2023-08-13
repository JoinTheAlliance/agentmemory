from agentmemory import cluster, create_memory, get_memories, wipe_category

# Sample data
memories_data = [
    {"id": "1", "document": "apple", "metadata": {}},
    {"id": "2", "document": "apple", "metadata": {}},
    {"id": "3", "document": "banana", "metadata": {}},
    {"id": "4", "document": "cherry", "metadata": {}},
    {"id": "5", "document": "apple", "metadata": {}},
]


def test_cluster_no_memories():
    # Set up empty memories
    wipe_category("fruits")

    # Run clustering
    cluster(epsilon=0.5, min_samples=2, category="fruits")

    # Check no memories are updated
    for memory in memories_data:
        assert memory.get("metadata", {}).get("cluster") is None


def test_cluster_no_neighbors():
    wipe_category("numbers")

    # Set up memories
    memories_data = [
        {"id": str(i), "document": str(i), "metadata": {}} for i in range(5)
    ]

    for memory in memories_data:
        create_memory("numbers", memory["document"])

    # Run clustering
    cluster(epsilon=0.5, min_samples=6, category="numbers")

    memories_data = get_memories("numbers")

    assert memories_data[0]['embedding'] is not None

    # All memories should be marked as noise since they have no neighbors
    for memory in memories_data:
        assert memory["metadata"].get("cluster") == "noise"

    wipe_category("numbers")


def test_cluster_insufficient_neighbors():
    wipe_category("fruits")
    # Setup memories
    memories_data = [
        {"id": "1", "document": "apple", "metadata": {}},
        {"id": "2", "document": "apple", "metadata": {}},
        {"id": "3", "document": "banana", "metadata": {}},
    ]

    for memory in memories_data:
        create_memory("fruits", memory["document"])

    # Run clustering
    cluster(epsilon=0.5, min_samples=3, category="fruits")

    memories_data = get_memories("fruits")

    # Only 'banana' should be marked as noise since 'apple' has 2 neighbors but needs 3
    for memory in memories_data:
        assert memory["metadata"].get("cluster") == "noise"
        
    wipe_category("fruits")


def test_cluster_with_enough_neighbors():
    wipe_category("fruits")

    # Setup memories
    memories_data = [
        {"id": "1", "document": "apple", "metadata": {}},
        {"id": "2", "document": "apple", "metadata": {}},
        {"id": "3", "document": "apple", "metadata": {}},
    ]

     # create memories
    for memory in memories_data:
        create_memory("fruits", memory["document"])

    # Run clustering
    cluster(epsilon=0.5, min_samples=2, category="fruits")

    memories_data = get_memories("fruits")

    # All memories should be marked with the same cluster
    clusters = {memory["metadata"].get("cluster") for memory in memories_data}
    assert len(clusters) == 1
    wipe_category("fruits")


def test_cluster_expansion():
    wipe_category("fruits")
    # Setup memories
    memories_data = [
        {"id": "1", "document": "apple", "metadata": {}},
        {"id": "2", "document": "apple", "metadata": {}},
        {"id": "3", "document": "banana", "metadata": {}},
        {"id": "4", "document": "banana", "metadata": {}},
        {"id": "5", "document": "banana", "metadata": {}},
    ]

    # create memories
    for memory in memories_data:
        create_memory("fruits", memory["document"])

    # Run clustering
    cluster(epsilon=0.5, min_samples=2, category="fruits")

    memories_data = get_memories("fruits")

    # There should be two clusters
    clusters = {memory["metadata"].get("cluster") for memory in memories_data}
    assert len(clusters) == 2
    wipe_category("fruits")
