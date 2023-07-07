"""
agentmemory

Simple agent memory, powered by chromadb
"""

__version__ = "0.1.8"
__author__ = "Moon (https://github.com/lalalune)"
__credits__ = "https://github.com/lalalune/agentmemory and https://www.trychroma.com/"

from .memory import (
    create_memory,
    get_memories,
    search_memory,
    get_memory,
    update_memory,
    delete_memory,
    count_memories,
    wipe_category,
    wipe_all_memories,
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
]
