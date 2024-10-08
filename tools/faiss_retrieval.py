##############################################
#--------------Main Functions---------------
##############################################

# tools/faiss_retrieval.py
import numpy as np

def k_image_search(query_vector, 
                   index_hnsw, 
                   device, k_nums=5):
    """
    Retrieves the k-nearest images to the query vector using the FAISS library with an HNSW (Hierarchical Navigable 
    Small World) index. This function is typically used for fast approximate nearest neighbor search in high-dimensional
    spaces, such as image embeddings.

    Args:
        query_vector (torch.Tensor): The query vector (embedding) to search for. This vector represents the image or
                                     feature to find the nearest neighbors for in the index.
        index_hnsw (faiss.Index): The FAISS index for retrieval. This index should be built using the HNSW algorithm 
                                  to allow efficient k-nearest neighbor (k-NN) search.
        device (str): The device where the query vector is located. It should be either "cpu" or "cuda", and the function
                      will handle the data accordingly to ensure compatibility with the FAISS index.
        k_nums (int): The number of nearest neighbors to retrieve. Default is 5, but this can be adjusted depending 
                      on how many neighbors you need for your specific use case.

    Returns:
        tuple: A tuple containing:
               - valid_distances (list): The distances from the query vector to the nearest neighbors in the index. 
               - valid_indices (list): The indices of the nearest neighbors, which can be used to retrieve the actual
                                       images or items corresponding to those embeddings in the original dataset.

    Process:
        1. If the device is CUDA, the query vector is transferred from the GPU (CUDA) to the CPU and converted to 
           a NumPy array to ensure compatibility with the FAISS library. FAISS does not directly work with PyTorch 
           tensors on GPU, so this step is necessary.
        2. If the device is CPU, the query vector is used directly without conversion.
        3. The FAISS `search` function is then called on the HNSW index, which returns the distances and indices of 
           the k-nearest neighbors for the given query vector.
        4. Invalid indices (represented by -1) are filtered out from the results. These invalid indices usually indicate 
           that no valid neighbors were found within the search space.
        5. The corresponding distances for the valid indices are also retrieved to ensure the final output contains
           only valid (distance, index) pairs.
        6. The function returns the valid distances and valid indices as a tuple, which can be used to fetch the 
           corresponding images or items.
    """

    # Step 1: Convert query vector to NumPy array if running on CUDA, as FAISS operates on CPU-compatible data
    if device == "cuda":
        vector_data = query_vector.cpu().numpy().astype(np.float32)
    else:
        vector_data = query_vector

    # Step 2: Perform k-nearest neighbor search on the HNSW index using FAISS
    distances_hnsw, indices_hnsw = index_hnsw.search(vector_data, 
                                                     k_nums)

    # Step 3: Filter out invalid indices (-1) from the search results
    valid_indexs = [idx for idx in indices_hnsw[0] if idx != -1]  # Filter out invalid indices
    valid_distances = distances_hnsw[0][:len(valid_indexs)]  # Get distances corresponding to valid indices

    # Step 4: Return valid distances and valid indices as a tuple
    return valid_distances, valid_indexs