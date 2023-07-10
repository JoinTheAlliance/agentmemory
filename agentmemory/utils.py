def collection_to_list(collection):
    """
    Function to convert collection (dictionary) to list.

    Parameters:
    collection (dict): Dictionary to be converted.

    Returns:
    list: Converted list of dictionaries.

    Example:
    >>> collection_to_list(collection)
    [{'metadata': '...', 'document': '...', 'id': '...'}]
    """

    list = []

    # If there are no embeddings, zip metadatas, documents and ids together
    if collection.get("embeddings", None) is None:
        for metadata, document, id in zip(
            collection["metadatas"], collection["documents"], collection["ids"]
        ):
            # append the zipped data as dictionary to the list
            list.append({"metadata": metadata, "document": document, "id": id})

        return list

    # if distance is none, zip metadatas, documents, ids and embeddings together
    if collection.get("distances", None) is None:
        for metadata, document, id, embedding in zip(
            collection["metadatas"],
            collection["documents"],
            collection["ids"],
            collection["embeddings"],
        ):
            # append the zipped data as dictionary to the list
            list.append(
                {"metadata": metadata, "document": document, "embedding": embedding, "id": id}
            )

        return list


    # if embeddings are present, zip all data including embeddings and distances
    for metadata, document, id, embedding, distance in zip(
        collection["metadatas"],
        collection["documents"],
        collection["ids"],
        collection["embeddings"],
        collection.get("distances"),
    ):
        # append the zipped data as dictionary to the list
        list.append({
                "metadata": metadata,
                "document": document,
                "embedding": embedding,
                "distance": distance,
                "id": id,
        })

    return list


def list_to_collection(list):
    """
    Function to convert list (of dictionaries) to collection (dictionary).

    Parameters:
    list (list): List to be converted.

    Returns:
    dict: Converted dictionary.

    Example:
    >>> list_to_collection(list)
    {'metadatas': ['...'], 'documents': ['...'], 'ids': ['...'], 'embeddings': ['...'], 'distances': ['...']}
    """
    collection = {
        "metadatas": [],
        "documents": [],
        "ids": [],
        "embeddings": [],
        "distances": [],
    }

    # iterate over items in list
    for item in list:
        # add corresponding values to respective keys in collection
        collection["metadatas"].append(item["metadata"])
        collection["documents"].append(item["document"])
        collection["ids"].append(item["id"])
        # check for presence of embeddings, and add if present
        if "embedding" in item:
            collection["embeddings"].append(item["embedding"])

        if "distance" in item:
            collection["distances"].append(item["distance"])

    # delete keys from collection if no values are present
    if len(collection["embeddings"]) == 0:
        del collection["embeddings"]

    if len(collection["distances"]) == 0:
        del collection["distances"]

    return collection

def flatten_arrays(collection):
    """
    Function to flatten the arrays in the collection.

    Parameters:
    collection (dict): Dictionary with nested arrays.

    Returns:
    dict: Flattened dictionary.

    Example:
    >>> flatten_arrays(collection)
    {'metadatas': ['...'], 'documents': ['...'], 'ids': ['...'], 'embeddings': ['...'], 'distances': ['...']}
    """

    # Iterate over each key in collection
    for key in collection:
        # If no values, continue to next iteration
        if collection[key] == None:
            continue
        # Flatten the arrays into a single array for each key
        collection[key] = [item for sublist in collection[key] for item in sublist]

    return collection

def get_include_types(include_embeddings, include_distances):
    """
    Function to get the types to include in results.

    Parameters:
    include_embeddings (bool): Whether to include embeddings in the results.
    include_distances (bool): Whether to include distances in the results.

    Returns:
    list: List of types to be included.

    Example:
    >>> get_include_types(True, False)
    ['metadatas', 'documents', 'embeddings']
    """
    # always include metadatas and documents
    include_types = ["metadatas", "documents"]

    # include embeddings if specified
    if include_embeddings:
        include_types.append("embeddings")

    # include distances if specified
    if include_distances:
        include_types.append("distances")

    return include_types

