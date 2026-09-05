# tools/faiss_retrieval.py

import numpy as np

def k_image_search(query_vector, index, device, k_nums=5):
   """
   Retrieves the k-nearest neighbors to a query vector using a FAISS index.
   This function is a generic wrapper around FAISS's k-NN search and works with
   any FAISS index type (e.g. HNSW, FlatIP, FlatL2, IVF...) and any embedding
   model (image or text), as long as the query vector's dimension matches the
   index's dimension.

   Args:
      query_vector (torch.Tensor or np.ndarray): The query vector (embedding) to search for.
            Can be a 1D vector (single query) or a 2D array/tensor (batch of queries). 
            Must be produced by the same encoder/model (and preprocessing) that was used to build the target index — 
            e.g. an image embedding must be searched against an image index, a text embedding against a text index; 
            mixing encoders will yield meaningless results even if dimensions happen to match.

            Note: If the index uses the Inner Product metric (e.g. FlatIP) to compute cosine similarity, 
            query_vector must also be normalized before being passed in, the same way it was normalized when the index was built.

      index (faiss.Index): The FAISS index to search against. Can be any FAISS index type
            (HNSW, FlatIP, FlatL2, IVF, etc.) — this function does not depend on any specific index implementation.

      device (str): The device where the query vector currently resides. Should be either "cpu" or "cuda". 
            The function converts the vector to a CPU-compatible NumPy array as needed, 
            since FAISS does not operate on GPU tensors directly.

      k_nums (int): The number of nearest neighbors to retrieve. Default is 5, but this can be adjusted 
            depending on how many neighbors you need for your specific use case.

   Returns:
      tuple: A tuple containing:
               - distances (np.ndarray): The distances (or similarity scores, depending on
                                          the index's metric) from the query vector to its
                                          nearest neighbors in the index.
               - indices (np.ndarray): The indices of the nearest neighbors, which can be
                                        used to retrieve the actual items (images, text
                                        chunks, etc.) corresponding to those embeddings in
                                        the original dataset.

   Process:
      1. If the device is CUDA, the query vector is transferred from GPU to CPU and converted
         to a NumPy array, since FAISS does not operate directly on GPU tensors. If it's a CPU
         torch tensor, it is likewise converted to a NumPy array. Otherwise, it is coerced into
         a NumPy float32 array directly.
      2. The vector is reshaped to 2D (n_queries, dim) if it was passed in as a 1D vector,
         since FAISS expects a batch dimension even for a single query.
      3. The FAISS `search` method is called on the given index, returning the distances
         and indices of the k-nearest neighbors for the query vector(s).
      4. The function returns the distances and indices as a tuple, which can be used to
         fetch the corresponding items from the original dataset.
   """

   # Step 1: Convert query vector to NumPy array if running on CUDA, as FAISS operates on CPU-compatible data
   if device == "cuda":
      vector_data = query_vector.cpu().numpy().astype(np.float32)
   elif hasattr(query_vector, "numpy"):  # torch tensor on cpu
      vector_data = query_vector.numpy().astype(np.float32)
   else:
      vector_data = np.asarray(query_vector, dtype=np.float32)

   # Make sure vector must be 2D shape (n_queries, dim)
   if vector_data.ndim == 1:
      vector_data = vector_data.reshape(1, -1)

   # Step 2: Perform k-nearest neighbor search on the HNSW index using FAISS
   distances, indices = index.search(vector_data, k_nums)

   # Step 3: Return distances and indices as a tuple
   return distances, indices