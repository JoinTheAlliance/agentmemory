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
    dump_memories,
    chroma_collection_to_list,
    list_to_chroma_collection,
)

wipe_all_memories()

set_storage_path("./test")

dump_memories("./testpath")

wipe_category("test")

# create_memory tests
create_memory("test", "document 1", metadata={"test": "test"})
create_memory("test", "document 2", metadata={"test": "test"})
create_memory("test", "document 3", metadata={"test": "test"})
create_memory("test", "document 4", metadata={"test": "test"})
create_memory("test", "document 5", metadata={"test": "test"})

assert get_memory("test", 0)["document"] == "document 1"

print('count_memories("test")')
print(count_memories("test"))
num_memories = count_memories("test")
assert num_memories == 5
print("Passed count_memories tests")

memory = get_memories("test")
assert memory[0]["document"] == "document 5"
print("Passed create_memory tests")

# chroma_collection_to_list
collection = get_chroma_client().get_or_create_collection("test")
test_collection_data = collection.peek()
list = chroma_collection_to_list(test_collection_data)

assert list[0]["document"] == "document 1"
print("Passed chroma_collection_to_list tests")

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

num_memories = count_memories("test")
# test delete_memory
delete_memory("test", 1)
assert count_memories("test") == num_memories - 1
print("Passed delete_memory tests")

# test wipe_category
wipe_category("test")
assert count_memories("test") == 0
print("Passed wipe_category tests")

# test wipe_all_memories
create_memory("test", "document 1", metadata={"test": "test"})
create_memory("test", "document 2", metadata={"test": "test"})
create_memory("test", "document 3", metadata={"test": "test"})

assert count_memories("test") == 3

min_dist_limited_memories = search_memory("test", "document", min_distance=0.8)

assert len(min_dist_limited_memories) == 0

create_memory("test", "cinammon duck cakes")
max_dist_limited_memories = search_memory("test", "cinammon duck cakes", max_distance=0.1)

assert len(max_dist_limited_memories) == 1

update_memory("test", 0, "document 1 updated", metadata={"test": "test"})
assert get_memory("test", 0)["document"] == "document 1 updated"
print("Passed update_memory tests")

wipe_all_memories()
assert count_memories("test") == 0
print("Passed wipe_all_memories tests")
