from agentmemory import search_memory, update_memory

def cluster(epsilon, min_samples, category, filter_metadata=None, novel=False):
    """
    DBScan clustering. Updates memories directly with their cluster id.
    """
    # Mark all memories as unvisited
    memories = search_memory(category, "", n_results=float("inf"), filter_metadata=filter_metadata, novel=novel)
    visited = {memory["id"]: False for memory in memories}
    
    cluster_id = 0
    for memory in memories:
        memory_id = memory["id"]
        if visited[memory_id]:
            continue
        visited[memory_id] = True

        # Finding neighboring memories based on the epsilon distance threshold
        neighbors = search_memory(category, memory["document"], n_results=float("inf"), max_distance=epsilon, filter_metadata=filter_metadata, novel=novel)

        # get the current metadata
        metadata = memory.get("metadata", {})

        if len(neighbors) <= min_samples:
            # Update the metadata to indicate it's noise
            metadata["cluster"] = "noise"
            # Update the memory's metadata directly to indicate it's noise
            update_memory(category, memory_id, metadata=metadata)
        else:
            cluster_id += 1
            metadata["cluster"] = str(cluster_id)
            # Mark the current memory as part of the new cluster
            update_memory(category, memory_id, metadata=metadata)
            _expand_cluster(memory, neighbors, cluster_id, visited, epsilon, min_samples, category, filter_metadata, novel)


def _expand_cluster(memory, neighbors, cluster_id, visited, epsilon, min_samples, category, filter_metadata, novel):
    """
    Helper function to expand the clusters.
    """
    idx = 0
    while idx < len(neighbors):
        neighbor_memory = neighbors[idx]
        neighbor_id = neighbor_memory["id"]

        if not visited[neighbor_id]:
            visited[neighbor_id] = True
            next_neighbors = search_memory(category, neighbor_memory["document"], n_results=float("inf"), max_distance=epsilon, filter_metadata=filter_metadata, novel=novel)
            if len(next_neighbors) >= min_samples:
                neighbors += next_neighbors

        metadata = neighbor_memory.get("metadata", {})
        
        # Update the metadata to indicate it's part of the cluster
        metadata["cluster"] = str(cluster_id)

        # Update the neighbor memory's metadata to indicate its cluster
        update_memory(category, neighbor_id, metadata=metadata)
        idx += 1
