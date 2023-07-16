import os

from agentmemory import (
    search_memory,
    get_memory,
    get_chroma_client,
    create_memory,
    get_memories,
    update_memory,
    delete_memory,
    count_memories,
    wipe_category,
    wipe_all_memories,
    set_storage_path,
    chroma_collection_to_list,
    list_to_chroma_collection,
    export_memory_to_file,
    import_file_to_memory,
)

# create 10 memories
for i in range(20):
    create_memory("test", "document " + str(i), metadata={"test": "test"})

memories = get_memories("test", n_results=10)

# assert length of memories is 10
assert len(memories) == 10

# assert that the first memory is document 19
assert memories[0]["document"] == "document 19"


wipe_all_memories()

create_memory("test", "not document 1", metadata={"test": "test"})
export_memory_to_file("./test_memories.json")
import_file_to_memory("./test_memories.json")
os.remove("./test_memories.json")

test_memories = get_memories("test")
assert test_memories[0]["document"] == "not document 1"

set_storage_path("./test")

wipe_category("test")

# rewrite as a for loop
for i in range(5):
    create_memory("test", "document " + str(i + 1), metadata={"test": "test"})

test_memories = get_memories("test")
test_id = test_memories[0]["id"]
memory = get_memory("test", test_id)
assert memory["document"] == "document 5"

num_memories = count_memories("test")
assert num_memories == 5

memory = get_memories("test")
assert memory[0]["document"] == "document 5"

# chroma_collection_to_list
collection = get_chroma_client().get_or_create_collection("test")
test_collection_data = collection.peek()
list = chroma_collection_to_list(test_collection_data)

assert list[0]["document"] == "document 1"

new_collection_data = list_to_chroma_collection(list)

assert test_collection_data["documents"][0] == "document 1"
print("Passed list_to_chroma_collection tests")

assert new_collection_data == test_collection_data
print("Passed equality of collection test")

search_results = search_memory(
    "test", "document 1", n_results=5, filter_metadata=None, contains_text=None
)

assert search_results[0]["document"] == "document 1"
print("Passed search_memory tests")

# Delete memory test
create_memory("test", "delete memory test", metadata={"test": "test"})
memories = get_memories("test")
memory_id = memories[0]["id"]
num_memories = count_memories("test")
# test delete_memory
delete_memory("test", memory_id)
assert count_memories("test") == num_memories - 1
print("Passed delete_memory tests")

# test wipe_category
wipe_category("test")
assert count_memories("test") == 0
print("Passed wipe_category tests")

for i in range(3):
    create_memory("test", "document " + str(i + 1), metadata={"test": "test"})
assert count_memories("test") == 3
print("Passed count_memories tests")

min_dist_limited_memories = search_memory("test", "document", min_distance=0.8)

assert len(min_dist_limited_memories) == 0

create_memory("test", "cinammon duck cakes")
max_dist_limited_memories = search_memory(
    "test", "cinammon duck cakes", max_distance=0.1
)

assert len(max_dist_limited_memories) == 1

create_memory("test", "update memory test", metadata={"test": "test"})
memories = get_memories("test")
memory_id = memories[0]["id"]

update_memory("test", memory_id, "doc 1 updated", metadata={"test": "test"})
assert get_memory("test", memory_id)["document"] == "doc 1 updated"
print("Passed update_memory tests")

wipe_all_memories()
assert count_memories("test") == 0
print("Passed wipe_all_memories tests")
