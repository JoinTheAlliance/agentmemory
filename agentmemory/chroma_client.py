import os

import chromadb


def create_client():
    STORAGE_PATH = os.environ.get("STORAGE_PATH", "./memory")
    return chromadb.PersistentClient(path=STORAGE_PATH)
