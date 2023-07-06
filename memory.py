import chromadb

client = chromadb.Client()

def collection_to_list(collection):
    # collection is a dictionary with keys "metadatas", "documents", "ids" and sometimes "embeddings"
    # we want to convert this to a list of unified objects
    # so we want to zip the metadatas, documents and ids together
    # and then we want to convert them to a list of dictionaries
    list = []

    if collection.get("embeddings", None) is None:
        for metadata, document, id in zip(collection["metadatas"], collection["documents"], collection["ids"]):
            list.append({
                "metadata": metadata,
                "document": document,
                "id": id
            }) 
        
        return list

    for metadata, document, id, embeddings in zip(collection["metadatas"], collection["documents"], collection["ids"], collection["embeddings"]):
        list.append({
            "metadata": metadata,
            "document": document,
            "embeddings": embeddings,
            "id": id
        })

    return list

def list_to_collection(list):
    # list is a list of dictionaries with keys "metadata", "document", "id" and sometimes "embeddings"
    # we want to convert this to a collection
    # so we want to unzip the metadatas, documents and ids
    # and then we want to convert them to a dictionary
    collection = {
        "metadatas": [],
        "documents": [],
        "ids": [],
        "embeddings": []
    }

    for item in list:
        collection["metadatas"].append(item["metadata"])
        collection["documents"].append(item["document"])
        collection["ids"].append(item["id"])
        if "embeddings" in item:
            collection["embeddings"].append(item["embeddings"])

    # if collection["embeddings"] == [], delete the key
    if collection["embeddings"] == []:
        del collection["embeddings"]

    return collection

def search_memory(
    category,
    search_text,
    n_results=5,
    filter_metadata=None,
    contains_text=None,
):
    """
    Search a collection with given query texts.
    """
    if contains_text is not None:
        contains_text = { "$contains": contains_text }
    memories = client.get_or_create_collection(category)
    query = memories.query(
        query_texts=[search_text],
        where=filter_metadata,
        where_document=contains_text,
        n_results=n_results,
        include=["metadatas", "documents", "embeddings"],
    )
    # query response is {'ids': [], 'documents': [], 'metadatas': [], 'embeddings': []}
    # zip the ids, documents, metadatas and embeddings together into a list of dictionaries
    # format to a list and return
    query = flatten_arrays(query)
    list = collection_to_list(query)

    return list

def flatten_arrays(collection):
    # collection is a dictionary with keys "metadatas", "documents", "ids" and sometimes "embeddings"
   # for each key in collection, get all of the arrays inside the array and flatten them into a single array
    for key in collection:
        if collection[key] == None:
            continue
        collection[key] = [item for sublist in collection[key] for item in sublist]

    return collection

def create_memory(category, text, metadata=None):
    memories = client.get_or_create_collection(category)
    memories.upsert(
        ids=[str(memories.count())],
        documents=[text],
        metadatas=[metadata],
    )


def get_memories(category, sort_order="desc", filter_metadata=None, n_results=20):
    # desc -> descending order, last to first
    # asc -> ascending order, first to last
    memories = client.get_or_create_collection(category)
    memories = memories.get(
        where=filter_metadata,
    )
    memories = collection_to_list(memories)
    # sort list by id
    memories.sort(key=lambda x: x["id"], reverse=sort_order == "desc")
    # remove all from memories after n_results length
    memories = memories[:n_results]
    return memories


