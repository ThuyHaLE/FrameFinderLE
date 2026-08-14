# tools/search_similar.py

import torch
import torch.nn.functional as F
import model_state

def similarities_calculating(tensor_1, 
                             tensor_2, 
                             dim=2):
    """
    Calculates the cosine similarity between two tensors and normalizes the result.

    Args:
        tensor_1 (torch.Tensor): First tensor.
        tensor_2 (torch.Tensor): Second tensor.
        dim (int): Dimension along which similarity is calculated.

    Returns:
        tuple: Raw cosine similarities and normalized similarity weights.
    """

    # Calculate cosine similarity and normalize the result
    similarities = F.cosine_similarity(tensor_1, 
                                       tensor_2, 
                                       dim=dim)
    min_similarity = torch.min(similarities)
    max_similarity = torch.max(similarities)
    similarity_weights = (similarities - min_similarity) / (max_similarity - min_similarity)

    return similarities, similarity_weights

def search_similar(query_encoding, encoded_frames=None, top_k=50) -> tuple[list[float], list[int]]:
    """
    query_encoding: embedding of frame query, shape [D]
    encoded_frames: embedding of all frames in the database, shape [N, D]
    """

    # If encoded_frames is not provided, use the preloaded ENCODED_FRAMES from model_state
    encoded_frames = encoded_frames if encoded_frames is not None else model_state.ENCODED_FRAMES

    # Calculate cosine similarity between the query and each item in the database
    sims = F.cosine_similarity(query_encoding.unsqueeze(0), encoded_frames, dim=1)  # [N]

    # Get the top-k highest scores
    top_scores, top_indices = torch.topk(sims, k=top_k)

    return top_scores.tolist(), top_indices.tolist()