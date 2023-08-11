from agentmemory import create_memory, get_memories, wipe_category


def reset_epoch():
    """
    Resets the epoch in the agent's memory to 1.

    This function wipes the "epoch" category and creates a new memory of 1.
    """
    wipe_category("epoch")
    create_memory("epoch", str(1))


def set_epoch(epoch):
    """
    Sets the epoch in the agent's memory to the specified value.

    Args:
        epoch (int): The desired epoch value.

    This function creates a new memory in the "epoch" category with the desired epoch.
    """
    create_memory("epoch", str(epoch))


def increment_epoch():
    """
    Increments the current epoch value by 1.

    This function retrieves the current epoch from memory, increments it, and then writes the new epoch value to memory.

    Returns:
        int: The new epoch value after incrementing.
    """
    epoch = get_epoch()
    epoch = epoch + 1
    create_memory("epoch", str(epoch))
    return int(epoch)


def get_epoch():
    """
    Retrieves the current epoch value from the agent's memory.

    Returns:
        int: The current epoch value.
    """
    memories = get_memories("epoch")
    if len(memories) == 0:
        create_memory("epoch", str(1))
        return 1
    memory = memories[0]
    return int(memory["document"])


def create_event(text, metadata={}, embedding=None):
    """
    Creates a new event in the agent's memory.

    Args:
        text (str): The text content of the event.
        metadata (dict, optional): Additional metadata for the event. Defaults to {}.
        embedding (object, optional): An optional embedding for the event.

    The current epoch value is automatically included in the metadata.

    Returns:
        object: The memory object created for this event.
    """
    metadata["epoch"] = get_epoch()
    return create_memory("events", text, metadata=metadata, embedding=embedding)


def get_events(epoch=None, n_results=10, filter_metadata=None):
    """
    Retrieves events from the agent's memory.

    Args:
        epoch (int, optional): If specified, only retrieve events from this epoch.

    Returns:
        list: A list of memory objects for the retrieved events.
    """
    if epoch is not None:
        if filter_metadata is None:
            filter_metadata = {}
        filter_metadata["epoch"] = epoch
        return get_memories(
            "events", filter_metadata=filter_metadata, n_results=n_results
        )
    else:
        if filter_metadata is None:
            return get_memories("events", n_results=n_results)
        else:
            return get_memories(
                "events", filter_metadata=filter_metadata, n_results=n_results
            )
