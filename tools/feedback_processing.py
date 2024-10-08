##############################################
#--------------Helper Functions---------------
##############################################

# tools/feedback_processing.py

import torch
import torch.nn.functional as F
import random
import numpy as np
from collections import OrderedDict
from tools.faiss_retrieval import k_image_search


def convert2binary_scores(refined_indexes, 
                          feedback_status):
    """
    Converts the refined indices and feedback into binary values (like=1, dislike=-1, neutral=0).

    Args:
        refined_indexes (list): List of refined item indices.
        feedback_status (dict): Dictionary with feedback (like or dislike) for each item.

    Returns:
        torch.Tensor: A tensor with binary values indicating feedback (-1, 0, 1).
    """
    # Convert indices and feedback lists to tensors
    refined_indexes_tensor = torch.tensor(refined_indexes)
    like_lst = torch.tensor([db_idx for db_idx, action in feedback_status.items() if action == 'like'])
    dislike_lst = torch.tensor([db_idx for db_idx, action in feedback_status.items() if action == 'dislike'])

    # Initialize a tensor with zeros
    result_tensor = torch.zeros_like(refined_indexes_tensor, dtype=torch.int)

    # Set positions to 1 for likes and -1 for dislikes
    result_tensor[torch.isin(refined_indexes_tensor, like_lst)] = 1
    result_tensor[torch.isin(refined_indexes_tensor, dislike_lst)] = -1

    return result_tensor

def convert2binary_feedback(feedback_status):
    """
    Converts the feedback status into a binary list.

    Args:
        feedback_status (dict): Dictionary of feedback with keys as item indices and values as 'like' or 'dislike'.

    Returns:
        list: A binary list where like=1, dislike=-1, and neutral=0.
    """
  
    feedback_tensor = torch.tensor(list(feedback_status.keys()))
    like_lst = torch.tensor([db_idx for db_idx, action in feedback_status.items() if action == 'like'])
    dislike_lst = torch.tensor([db_idx for db_idx, action in feedback_status.items() if action == 'dislike'])

    # Initialize a tensor with zeros
    result_tensor = torch.zeros(len(feedback_status))

    # Set positions to 1 for likes and -1 for dislikes
    result_tensor[torch.isin(feedback_tensor, like_lst)] = 1
    result_tensor[torch.isin(feedback_tensor, dislike_lst)] = -1

    return result_tensor.tolist()


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

def calculate_feedback_factor(feedback, 
                              decay_factor=0.9, 
                              time_weight_ratio=0.3, 
                              window_size=5):
    """
    Calculates a feedback factor by considering recent interactions and applying decay over time.

    Args:
        feedback (list): List of binary feedback values.
        decay_factor (float): Decay factor controlling the influence of older feedback.
        time_weight_ratio (float): Weight applied to time-sensitive feedback adjustments.
        window_size (int): Number of recent interactions considered.

    Returns:
        float: Feedback factor calculated based on simple average and time-weighted average.
    """

    # Limit feedback to the defined window size
    if len(feedback) > window_size:
        feedback = feedback[-window_size:]
    
    # Calculate feedback statistics
    simple_sum = sum(feedback)
    weighted_sum = sum(f * (decay_factor ** i) for i, f in enumerate(reversed(feedback)))
    total_weight = sum(decay_factor ** i for i in range(len(feedback)))
    simple_avg = simple_sum / len(feedback)
    time_weighted_avg = weighted_sum / total_weight

    # Compute final feedback factor
    feedback_factor = ((1 - time_weight_ratio) * simple_avg) + (time_weight_ratio * time_weighted_avg)

    return feedback_factor

def define_exploration(refined_indices, feedback_status, 
                       exploration_ratio=0.2, like_weight=0.7, 
                       randomness=0.1):
    """
    Defines exploration strategy by selecting a subset of items based on feedback and exploration ratio.

    Args:
        refined_indices (list): List of refined item indices.
        feedback_status (dict): User feedback data (like or dislike).
        exploration_ratio (float, optional): Ratio of items to explore (default is 0.2).
        like_weight (float, optional): Weight for liked items (default is 0.7).
        randomness (float, optional): Factor controlling randomness in selection (default is 0.1).

    Returns:
        list: Indices selected for exploration.
    """

    n_explore = max(int(len(refined_indices) * exploration_ratio), 1)  # Ensure at least 1 item
    if not feedback_status:
        return random.sample(refined_indices[:n_explore * 2], n_explore)  # Some randomness in cold start
    like_lst = [k for k, v in feedback_status.items() if v == 'like']
    dislike_lst = [k for k, v in feedback_status.items() if v == 'dislike']

    # Remove disliked items and select candidates
    candidate_indices = [idx for idx in refined_indices if idx not in dislike_lst]
    if not candidate_indices:
        return random.sample(refined_indices, n_explore)
    
    # Determine how many liked items to include
    n_likes = min(int(n_explore * like_weight), len(like_lst))
    # Combine liked items and top-scoring items
    exploit_indices = like_lst[:n_likes] + [idx for idx in candidate_indices if idx not in like_lst][:n_explore - n_likes]
    
    # Introduce randomness
    for i in range(len(exploit_indices)):
        if random.random() < randomness:
            random_idx = random.choice(candidate_indices)
            exploit_indices[i] = random_idx

    return exploit_indices[:n_explore]

def min_max_scale(scores):
    """
    Scales the scores to the range [0, 1] using min-max normalization.

    Args:
        scores (list): List of scores to normalize.

    Returns:
        numpy.ndarray: Normalized scores.
    """
    scores = np.array(scores)

    return (scores - np.min(scores)) / (np.max(scores) - np.min(scores))

def max_min_scale(scores):
    """
    Scales the scores using max-min normalization (inverse normalization).

    Args:
        scores (list): List of scores to normalize.

    Returns:
        numpy.ndarray: Inversely normalized scores.
    """
    scores = np.array(scores)

    return (np.max(scores) - scores) / (np.max(scores) - np.min(scores))

def perform_exploit(db_idx: int, 
                    encoded_frames, 
                    clipv0_hnsw, 
                    device, k_nums = 50):
    """
    Performs nearest-neighbor retrieval to find items similar to the given index.

    Args:
        db_idx (int): Database index for the query item.
        encoded_frames (torch.Tensor): Encoded frame features for the items.
        clipv0_hnsw (faiss.Index): FAISS index for retrieval.
        device (str): Device used for processing ("cpu" or "cuda").
        k_nums (int, optional): Number of items to retrieve (default is 50).

    Returns:
        tuple: Retrieved distances and indices.
    """

    query_vector = encoded_frames[db_idx].unsqueeze(0)
    clipv0_distances, clipv0_indexs = k_image_search(query_vector, 
                                                     clipv0_hnsw, 
                                                     device, k_nums)

    return clipv0_distances, clipv0_indexs

def diverse_exploration(refined_indices, refined_scores, 
                        feedback_status, encoded_frames, 
                        clipv0_hnsw, device, k_nums = 50,
                        exploration_ratio=0.2, original_weight=0.7):
    """
    Applies exploration to refine scores and indices, balancing feedback and exploration.

    Args:
        refined_indices (list): List of refined item indices.
        refined_scores (list): List of corresponding scores.
        feedback_status (dict): User feedback data.
        encoded_frames (torch.Tensor): Encoded frame features for retrieval.
        clipv0_hnsw (faiss.Index): FAISS index for nearest-neighbor retrieval.
        device (str): Device used for processing ("cpu" or "cuda").
        k_nums (int, optional): Number of items for retrieval (default is 50).
        exploration_ratio (float, optional): Exploration ratio (default is 0.2).
        original_weight (float, optional): Weight of original scores in final results (default is 0.7).

    Returns:
        tuple: Refined scores and indices after exploration.
    """

    # Define items for exploration based on feedback
    exploit_indices = define_exploration(refined_indices, feedback_status,
                                         exploration_ratio=exploration_ratio,
                                         like_weight=0.7, randomness=0.1)

    expanded_indexes = []
    expanded_distances = []

    # Perform exploitation for each selected index
    for idx in exploit_indices:
        try:
            clipv0_distances, clipv0_indexes = perform_exploit(idx, 
                                                               encoded_frames, 
                                                               clipv0_hnsw, 
                                                               device, k_nums)

            expanded_indexes.extend(clipv0_indexes)
            expanded_distances.extend(clipv0_distances)
        except Exception as e:
            print(f"Error in perform_search for index {idx}: {str(e)}")

    # Remove duplicates and preserve order
    expanded_results = OrderedDict((idx, score) for idx, score in zip(expanded_indexes, expanded_distances)
                                   if idx not in exploit_indices and idx not in refined_indices)

    # Normalize the expanded scores and combine with original scores
    expanded_scores = max_min_scale(list(expanded_results.values()))
    expanded_indexes = list(expanded_results.keys())

    new_indices = refined_indices + expanded_indexes
    new_scores = (min_max_scale(refined_scores) * original_weight).tolist() + (expanded_scores * (1 - original_weight)).tolist()

    # Create final scores dictionary and sort results
    new_final_scores = dict(zip(new_indices, new_scores))
    # Sort the results based on final scores in descending order (higher score is better)
    new_sorted_results = sorted(new_final_scores.items(), key=lambda x: x[1], reverse=True)

    new_refined_indexes = [result[0] for result in new_sorted_results]
    new_refined_scores = [result[1] for result in new_sorted_results]

    return new_refined_scores, new_refined_indexes