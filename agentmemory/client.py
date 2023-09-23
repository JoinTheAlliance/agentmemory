import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Callable

import pluggy

hookspec = pluggy.HookspecMarker("agentmemory")
hookimpl = pluggy.HookimplMarker("agentmemory")


class ClientFactorySpec:
    @hookspec
    def declare_client(self, factory_map: Dict[str, Callable]):
        return factory_map


class ChromaFactory:
    @hookimpl
    def declare_client(self, factory_map: Dict[str, Callable]):
        def make_chroma_client():
            from .chroma_client import create_client
            return create_client()
        factory_map["CHROMA"] = make_chroma_client
        return factory_map


class PostgresFactory:
    @hookimpl
    def declare_client(self, factory_map: Dict[str, Callable]):
        def make_postgres_client():
            from .postgres import create_client
            return create_client()
        factory_map["POSTGRES"] = make_postgres_client
        return factory_map

plugin_manager = None

def get_plugin_manager():
    global plugin_manager
    if plugin_manager is not None:
        return plugin_manager
    pm = pluggy.PluginManager("agentmemory")
    pm.add_hookspecs(ClientFactorySpec)
    pm.register(ChromaFactory())
    pm.register(PostgresFactory())
    pm.load_setuptools_entrypoints("agentmemory")
    plugin_manager = pm
    return plugin_manager


class CollectionMemory(ABC):
    @abstractmethod
    def count(self):
        raise NotImplementedError()

    @abstractmethod
    def add(self, ids, documents=None, metadatas=None, embeddings=None):
        raise NotImplementedError()

    @abstractmethod
    def get(
        self,
        ids=None,
        where=None,
        limit=None,
        offset=None,
        where_document=None,
        include=["metadatas", "documents"],
    ):
        raise NotImplementedError()

    @abstractmethod
    def peek(self, limit=10):
        raise NotImplementedError()

    @abstractmethod
    def query(
        self,
        query_embeddings=None,
        query_texts=None,
        n_results=10,
        where=None,
        where_document=None,
        include=["metadatas", "documents", "distances"],
    ):
        raise NotImplementedError()

    @abstractmethod
    def update(self, ids, documents=None, metadatas=None, embeddings=None):
        raise NotImplementedError()

    @abstractmethod
    def upsert(self, ids, documents=None, metadatas=None, embeddings=None):
        raise NotImplementedError()

    @abstractmethod
    def delete(self, ids=None, where=None, where_document=None):
        raise NotImplementedError()

@dataclass
class AgentCollection():
    name: str


class AgentMemory(ABC):
    @abstractmethod
    def get_or_create_collection(self, category, metadata=None) -> CollectionMemory:
        raise NotImplementedError()

    @abstractmethod
    def delete_collection(self, category):
        raise NotImplementedError()

    @abstractmethod
    def list_collections(self) -> List[AgentCollection]:
        raise NotImplementedError()


DEFAULT_CLIENT_TYPE = "CHROMA"
CLIENT_TYPE = os.environ.get("CLIENT_TYPE", DEFAULT_CLIENT_TYPE)

client = None


def get_client(client_type=None):
    global client
    if client is not None:
        return client

    client_type = client_type or CLIENT_TYPE

    factory_map = {}
    pm = get_plugin_manager()
    pm.hook.declare_client(factory_map=factory_map)
    if client_type not in factory_map:
        raise RuntimeError("Unknown client type: {client_type}")
    client = factory_map[client_type]()

    return client
