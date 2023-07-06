from memory import client, search_memory, create_memory, get_memories, collection_to_list, list_to_collection

client.reset()

# create_memory tests
create_memory("test", "1", metadata={"test": "test"})
create_memory("test", "2", metadata={"test": "test"})
create_memory("test", "3", metadata={"test": "test"})
create_memory("test", "4", metadata={"test": "test"})
create_memory("test", "5", metadata={"test": "test"})

memory = get_memories("test")
assert memory[0]["document"] == "5"
print("Passed create_memory tests")

# collection_to_list
collection = client.get_or_create_collection("test")
test_collection_data = collection.peek()
list = collection_to_list(test_collection_data)

assert list[0]["document"] == "1"
print("Passed collection_to_list tests")

# # list_to_collection
new_collection_data = list_to_collection(list)

assert test_collection_data["documents"][0] == "1"
print("Passed list_to_collection tests")

# # assert collection == new_collection
assert new_collection_data == test_collection_data
print("Passed equality of collection test")

search_results = search_memory("test", "1", n_results=5, filter_metadata=None, contains_text=None)

assert search_results[0]["document"] == "1"
print("Passed search_memory tests")