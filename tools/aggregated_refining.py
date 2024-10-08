##############################################
#--------------Main Functions---------------
##############################################

# tools/aggregated_refining.py
import torch
from tools.feedback_processing import diverse_exploration, convert2binary_feedback, calculate_feedback_factor, convert2binary_scores

def aggregated_refining(refined_indices, refined_scores, 
                        feedback_status, encoded_frames, 
                        clipv0_hnsw, device,
                        exploration_ratio=0.2, original_weight=0.7,
                        decay_factor=0.9, window_size=50, time_weight_ratio=0.5,):
    
    """
    Refines a list of indices and their associated scores by incorporating user feedback and applying an 
    exploration mechanism to balance exploration and exploitation, often used in recommendation systems.

    Args:
        refined_indices (list): List of indices corresponding to refined items (e.g., recommended items).
        refined_scores (list): List of scores corresponding to the items in `refined_indices`.
        feedback_status (list): List representing user feedback for each item (positive, neutral, negative).
        encoded_frames (tensor): Encoded features or frames to be used in the exploration process.
        clipv0_hnsw (faiss.Index): FAISS index used for nearest-neighbor retrieval in the exploration process.
        device (str): Device where operations are performed ("cpu" or "cuda").
        exploration_ratio (float, optional): Factor controlling the balance between exploration and exploitation 
                                             (default is 0.2).
        original_weight (float, optional): Weight applied to the original scores during exploration (default is 0.7).
        decay_factor (float, optional): Controls how feedback influence decays over time (default is 0.9).
        window_size (int, optional): Number of recent interactions considered for feedback (default is 50).
        time_weight_ratio (float, optional): Weight applied to time-sensitive feedback adjustments (default is 0.5).

    Returns:
        list: Refined and adjusted scores based on feedback and exploration.
        list: Corresponding indices of the sorted items based on the refined scores.

    Process:
        1. The function first applies exploration to the `refined_scores` using the `diverse_exploration` method, 
           which adjusts the scores based on the exploration ratio and original weight.
        2. If no feedback is provided (`feedback_status` is empty), the refined scores and indices are returned as is.
        3. If feedback is present, it is converted into binary form, and the feedback factor is calculated using 
           `calculate_feedback_factor`. The feedback factor is used to adjust the weights for positive, negative, 
           or neutral feedback.
        4. A feedback tensor is generated, and scores are adjusted accordingly based on the feedback factor.
        5. The adjusted feedback scores are added to the original refined scores, and the final scores are sorted in 
           descending order.
        6. The function returns the top `k_num` refined scores and their corresponding indices.
    """

    k_num = len(refined_indices) # Number of refined items

    # Step 1: Apply exploration to the refined scores using the diverse exploration method
    new_refined_scores, new_refined_indexes = diverse_exploration(refined_indices, refined_scores, feedback_status, 
                                                                  encoded_frames, clipv0_hnsw, device, k_num,
                                                                  exploration_ratio, original_weight)

    # Step 2: If no feedback is available, return the newly refined scores and indices
    if not feedback_status:
      return new_refined_scores[:k_num], new_refined_indexes[:k_num]

    else:
      # Step 3: Convert feedback to binary form and compute feedback factor
      binary_feedback = convert2binary_feedback(feedback_status)
      fb_factor = calculate_feedback_factor(binary_feedback, 
                                            decay_factor, time_weight_ratio, window_size)

      # Step 4: Convert feedback to binary tensor (like=1, dislike=-1, neutral=0)
      feedback_tensor = convert2binary_scores(new_refined_indexes, 
                                              feedback_status)

      # Step 5: Adjust scores based on feedback
      if fb_factor < 0:
        # Adjust scores for negative feedback
        alpha_diff = torch.where(feedback_tensor == 1, 0, feedback_tensor)
        adjusted_scores = torch.where(alpha_diff == -1, fb_factor, alpha_diff)
      elif fb_factor > 0:
        # Adjust scores for positive feedback
        alpha_diff = torch.where(feedback_tensor == 1, fb_factor, feedback_tensor)
        adjusted_scores = torch.where(alpha_diff == -1, 0, alpha_diff)
      else:
        # Neutral feedback adjustment
        alpha_diff = torch.where(feedback_tensor == 1, 0, feedback_tensor)
        adjusted_scores = torch.where(alpha_diff == -1, 0, alpha_diff)

      # Step 6: Refine final scores by adding feedback adjustments and sorting
      new_scores =  torch.tensor(new_refined_scores) + adjusted_scores
      sorted_scores, indices = torch.sort(new_scores, 
                                          descending=True) # Sort scores in descending order
      sorted_indices = [new_refined_indexes[i] for i in indices] # Get corresponding indices

    # Return top `k_num` scores and indices
    return sorted_scores.tolist()[:k_num], sorted_indices[:k_num]