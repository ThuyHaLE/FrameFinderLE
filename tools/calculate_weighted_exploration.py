import math

def calculate_weighted_exploration(refined_scores, k, max_expansion=2.0):
    """
    Calculate a new k value based on the distribution of similarity scores

    Parameters:
    refined_scores: list of similarity_score
    k: current top-k
    max_expansion: maximum multiplier to expand k (default: 2.0)

    Returns:
    tuple: (change_k: bool, k_new: int)
    """
    # Check if there are no results or k <= 0
    if not refined_scores or k <= 0:
        return False, max(1, k)
        
    mean_score = sum(refined_scores) / len(refined_scores)
    std_score = math.sqrt(sum((s - mean_score)**2 for s in refined_scores) / len(refined_scores))
    
    # Calculate exploration_ratio based on the distribution of scores
    if std_score < 0.1 and mean_score < 0.5:
        # Results are uniformly low - need to expand more
        exploration_ratio = 0.9
    elif std_score > 0.3:
        # Results are scattered - moderate expansion
        exploration_ratio = 0.5
    else:
        # Normal case - ratio inversely proportional to mean
        exploration_ratio = 1 - mean_score
    
    # Ensure k_new is a valid value and sufficiently different from the original k
    k_new = max(k + 1, int(min(max_expansion * k, exploration_ratio * max_expansion * k)))
    
    # Only expand if k_new is sufficiently larger than k
    if k_new > k + max(1, int(0.1 * k)):  # Ensure increase by at least 10% or +1
        return True, k_new
    else:
        return False, k