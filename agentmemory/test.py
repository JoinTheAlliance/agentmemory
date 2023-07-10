from main import (
    search_memory,
    get_memory,
    get_client,
    create_memory,
    get_memories,
    update_memory,
    delete_memory,
    count_memories,
    wipe_category,
    wipe_all_memories,
    set_storage_path
)

from utils import (
    collection_to_list,
    list_to_collection,
)

wipe_all_memories()

set_storage_path("./test")

# create_memory tests
create_memory("test", "document 1", metadata={"test": "test"})
create_memory("test", "document 2", metadata={"test": "test"})
create_memory("test", "document 3", metadata={"test": "test"})
create_memory("test", "document 4", metadata={"test": "test"})
create_memory("test", "document 5", metadata={"test": "test"})

assert get_memory("test", 0)["document"] == "document 1"

num_memories = count_memories("test")
assert num_memories == 5
print("Passed count_memories tests")

memory = get_memories("test")
assert memory[0]["document"] == "document 5"
print("Passed create_memory tests")

# collection_to_list
collection = get_client().get_or_create_collection("test")
test_collection_data = collection.peek()
list = collection_to_list(test_collection_data)

assert list[0]["document"] == "document 1"
print("Passed collection_to_list tests")

new_collection_data = list_to_collection(list)

assert test_collection_data["documents"][0] == "document 1"
print("Passed list_to_collection tests")

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
count_memories("test")

update_memory("test", 0, "document 1 updated", metadata={"test": "test"})
assert get_memory("test", 0)["document"] == "document 1 updated"
print("Passed update_memory tests")

wipe_all_memories()
assert count_memories("test") == 0
print("Passed wipe_all_memories tests")
