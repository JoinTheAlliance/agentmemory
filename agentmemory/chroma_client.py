import os

import chromadb

from .client import CollectionMemory, AgentMemory

class ChromaCollectionMemory(CollectionMemory):
    def __init__(self, collection, metadata=None) -> None:
        self.collection = collection

    def count(self):
        return self.collection.count()

    def add(self, ids, documents=None, metadatas=None, embeddings=None):
        return self.collection.add(ids, documents, metadatas, embeddings)

    def get(
        self,
        ids=None,
        where=None,
        limit=None,
        offset=None,
        where_document=None,
        include=["metadatas", "documents"],
    ):
        return self.collection.get(ids, where, limit, offset, where_document, include)

    def peek(self, limit=10):
        return self.collection.peek(limit)

    def query(
        self,
        query_embeddings=None,
        query_texts=None,
        n_results=10,
        where=None,
        where_document=None,
        include=["metadatas", "documents", "distances"],
    ):
        return self.collection.query(query_embeddings, query_texts, n_results, where, where_document, include)

    def update(self, ids, documents=None, metadatas=None, embeddings=None):
        return self.collection.update(ids, embeddings, metadatas, documents)

    def upsert(self, ids, documents=None, metadatas=None, embeddings=None):
        # if no id is provided, generate one based on count of documents in collection
        if any(id is None for id in ids):
            origin = self.count()
            # pad the id with zeros to make it 16 digits long
            ids = [str(id_).zfill(16) for id_ in range(origin, origin+len(documents))]

        return self.collection.upsert(ids, embeddings, metadatas, documents)

    def delete(self, ids=None, where=None, where_document=None):
        return self.collection.delete(ids, where, where_document)


class ChromaMemory(AgentMemory):
    def __init__(self, path) -> None:
        self.chroma = chromadb.PersistentClient(path=path)

    def get_or_create_collection(self, category, metadata=None) -> CollectionMemory:
        memory = self.chroma.get_or_create_collection(category)
        return ChromaCollectionMemory(memory, metadata)

    def get_collection(self, category) -> CollectionMemory:
        memory = self.chroma.get_collection(category)
        return ChromaCollectionMemory(memory)

    def delete_collection(self, category):
        self.chroma.delete_collection(category)

    def list_collections(self):
        return self.chroma.list_collections()


def create_client():
    STORAGE_PATH = os.environ.get("STORAGE_PATH", "./memory")
    return ChromaMemory(path=STORAGE_PATH)
