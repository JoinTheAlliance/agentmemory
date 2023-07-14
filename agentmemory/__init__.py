"""
agentmemory

Simple agent memory, powered by chromadb
"""

__version__ = "0.2.1"
__author__ = "Moon (https://github.com/lalalune)"
__credits__ = "https://github.com/lalalune/agentmemory and https://www.trychroma.com/"

from .main import (
    create_memory,
    get_memories,
    search_memory,
    get_memory,
    update_memory,
    delete_memory,
    count_memories,
    wipe_category,
    wipe_all_memories,
    set_storage_path,
    save_memory,
    get_chroma_client,
    chroma_collection_to_list,
    list_to_chroma_collection,
    export_memory_to_json,
    export_memory_to_file,
    import_json_to_memory,
    import_file_to_memory,
)

__all__ = [
    "create_memory",
    "get_memories",
    "search_memory",
    "get_memory",
    "update_memory",
    "delete_memory",
    "count_memories",
    "wipe_category",
    "wipe_all_memories",
    "set_storage_path",
    "save_memory",
    "get_chroma_client",
    "chroma_collection_to_list",
    "list_to_chroma_collection",
    "export_memory_to_json",
    "export_memory_to_file",
    "import_json_to_memory",
    "import_file_to_memory",
]
