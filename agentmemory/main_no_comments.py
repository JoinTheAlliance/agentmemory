import datetime

from agentmemory.helpers import (
    chroma_collection_to_list,
    flatten_arrays,
    get_include_types,
)

from agentmemory.client import get_client

def create_memory(category, text, metadata={}, embedding=None, id=None):
    memories = get_client().get_or_create_collection(category)
    metadata["created_at"] = datetime.datetime.now().timestamp()
    metadata["updated_at"] = datetime.datetime.now().timestamp()
    if id is None:
        id = str(memories.count())
        id = id.zfill(16)
    for key, value in metadata.items():
        if isinstance(value, bool):
            metadata[key] = str(value)
    memories.upsert(
        ids=[str(id)],
        documents=[text],
        metadatas=[metadata],
        embeddings=[embedding] if embedding is not None else None,
    )
    return id


def create_unique_memory(category, content, metadata={}, similarity=0.95):
    max_distance = 1.0 - similarity
    memories = search_memory(
        category,
        min_distance=0,
        max_distance=max_distance,
        search_text=content,
        n_results=1,
        filter_metadata={"unique": "True"},
    )
    if len(memories) == 0:
        metadata["unique"] = "True"
        create_memory(category, content, metadata=metadata)
        return
    metadata["unique"] = "False"
    metadata["related_to"] = memories[0]["id"]
    metadata["related_document"] = memories[0]["document"]
    create_memory(category, content, metadata=metadata)
    return id

def search_memory(
    category,
    search_text,
    n_results=5,
    filter_metadata=None,
    contains_text=None,
    include_embeddings=True,
    include_distances=True,
    max_distance=None,  # 0.0 - 1.0
    min_distance=None,  # 0.0 - 1.0
    unique=False,
):
    if contains_text is not None:
        contains_text = {"$contains": contains_text}
    memories = get_client().get_or_create_collection(category)
    if (memories.count()) == 0:
        return []
    n_results = min(n_results, memories.count())
    include_types = get_include_types(include_embeddings, include_distances)
    if filter_metadata is not None and len(filter_metadata.keys()) > 1:
        # map each key:value in filter_metadata to an object shaped like { "key": { "$eq": "value" } }
        filter_metadata = [
            {key: {"$eq": value}} for key, value in filter_metadata.items()
        ]
        filter_metadata = {"$and": filter_metadata}
    if unique:
        if filter_metadata is None:
            filter_metadata = {}
        filter_metadata["unique"] = "True"
    query = memories.query(
        query_texts=[search_text],
        where=filter_metadata,
        where_document=contains_text,
        n_results=n_results,
        include=include_types,
    )
    query = flatten_arrays(query)
    result_list = chroma_collection_to_list(query)
    if min_distance is not None and min_distance > 0:
        result_list = [res for res in result_list if res["distance"] >= min_distance]
    if max_distance is not None and max_distance < 1.0:
        result_list = [res for res in result_list if res["distance"] <= max_distance]
    return result_list


def get_memory(category, id, include_embeddings=True):
    memories = get_client().get_or_create_collection(category)
    include_types = get_include_types(include_embeddings, False)
    memory = memories.get(ids=[str(id)], limit=1, include=include_types)
    if not isinstance(memory, list):
        memory = chroma_collection_to_list(memory)
    if len(memory) == 0:
        return None
    return memory[0]

def get_memories(
    category,
    sort_order="desc",
    contains_text=None,
    filter_metadata=None,
    n_results=20,
    include_embeddings=True,
    unique=False,
):
    memories = get_client().get_or_create_collection(category)
    n_results = min(n_results, memories.count())
    include_types = get_include_types(include_embeddings, False)
    where_document = None
    if contains_text is not None:
        where_document = {"$contains": contains_text}
    if filter_metadata is not None and len(filter_metadata.keys()) > 1:
        filter_metadata = [
            {key: {"$eq": value}} for key, value in filter_metadata.items()
        ]
        filter_metadata = {"$and": filter_metadata}
    if unique:
        if filter_metadata is None:
            filter_metadata = {}
        filter_metadata["unique"] = "True"
    memories = memories.get(
        where=filter_metadata, where_document=where_document, include=include_types
    )
    if not isinstance(memories, list):
        memories = chroma_collection_to_list(memories)
    memories.sort(key=lambda x: x["id"], reverse=sort_order == "desc")
    memories = memories[:n_results]
    return memories


def update_memory(category, id, text=None, metadata=None):
    memories = get_client().get_or_create_collection(category)
    if metadata is None and text is None:
        raise Exception("No text or metadata provided")
    if metadata is not None:
        for key, value in metadata.items():
            if isinstance(value, bool):
                metadata[key] = str(value)
    metadata["updated_at"] = datetime.datetime.now().timestamp()
    documents = [text] if text is not None else None
    metadatas = [metadata] if metadata is not None else None
    memories.update(ids=[str(id)], documents=documents, metadatas=metadatas)


def delete_memory(category, id):
    memories = get_client().get_or_create_collection(category)
    if memory_exists(category, id) is False:
        return
    memories.delete(ids=[str(id)])

def delete_memories(category, document=None, metadata=None):
    memories = get_client().get_or_create_collection(category)
    if document is not None:
        memories.delete(where_document={"$contains": document})
    if metadata is not None:
        memories.delete(where=metadata)
    return True


def delete_similar_memories(category, content, similarity_threshold=0.95):
    memories = search_memory(category, content)
    memories_to_delete = []
    if len(memories) > 0:
        for memory in memories:
            goal_similarity = 1.0 - memory["distance"]
            if goal_similarity > similarity_threshold:
                memories_to_delete.append(memory["id"])
            else:
                break
    if len(memories_to_delete) > 0:
        for memory in memories_to_delete:
            delete_memory(category, memory)
    return len(memories_to_delete) > 0


def memory_exists(category, id, includes_metadata=None):
    memories = get_client().get_or_create_collection(category)
    memory = memories.get(ids=[str(id)], where=includes_metadata, limit=1)
    exists = len(memory["ids"]) > 0
    return exists

def count_memories(category, unique=False):
    memories = get_client().get_or_create_collection(category)
    if unique:
        memories = memories.get(where={"unique": "True"})
    return memories.count()


def wipe_category(category):
    collection = None
    try:
        collection = get_client().get_collection(category) 
    except Exception:
        pass

    if collection is not None:
        get_client().delete_collection(category)


def wipe_all_memories():
    client = get_client()
    collections = client.list_collections()
    for collection in collections:
        client.delete_collection(collection.name)