##############################################
#--------------Helper Functions---------------
##############################################

# tools/utils.py
import math
import numpy as np
from datetime import timedelta

def str_to_timedelta(timestamp_str: str) -> timedelta:
    """
    Convert a timestamp string into a `timedelta` object.

    Args:
        timestamp_str (str): A string representing a timestamp in the format 'HH:MM:SS' 
                             (with optional fractional seconds).

    Returns:
        timedelta: A `timedelta` object representing the duration specified by the timestamp string.

    Process:
        1. Split the input string into its component parts (hours, minutes, seconds).
        2. If the string contains exactly three parts, convert each part to the appropriate integer or float.
        3. Create and return a `timedelta` object based on the extracted values.
        4. If the input string is not in the expected format, return a `timedelta` of zero.

    Note:
        The function supports fractional seconds for greater precision.
    """

    parts = timestamp_str.split(":")

    if len(parts) == 3:
        hours, minutes = int(parts[0]), int(parts[1])
        seconds = float(parts[2])  # Support fractional seconds
        return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    
    return timedelta(0)

def calculate_video_ranking_score(frame_info, 
                                  k_nums, 
                                  higher_is_better=False):
    """
    Calculate a ranking score for a video based on the scores of its frames.

    Args:
        frame_info (list): A list of dictionaries, each containing 'position' and 'score' for a frame of the video.
        k_nums (int): Total number of frames used as a reference for normalizing the frame's position.
        higher_is_better (bool): A flag indicating whether higher scores indicate better rankings (default is False).

    Returns:
        float: A final ranking score for the video. If `higher_is_better` is True, higher scores indicate better rankings.
                If False, lower scores indicate better rankings.

    Process:
        1. If the video has no frames (empty `frame_info`), return a very high or low value based on ranking preference.
        2. Calculate the weighted sum of frame scores based on their position and individual score.
           The weight is derived from the frame's position relative to the total number of frames (`k_nums`).
        3. Average the weighted scores over the total number of frames.
        4. Apply a logarithmic factor to the average score to boost videos with more frames, adjusting based on whether 
           higher or lower scores are preferred.
        5. Return the final ranking score, negating it if lower scores are better.
    """

    # Return a high or low score for videos without frames depending on ranking preference
    if not frame_info:
        return float('-inf') if higher_is_better else float('inf')
    n = len(frame_info)  # Number of frames for the video
    # Sum part of the formula: weighted contribution of each frame
    # The weight is based on the frame's position and score
    sum_part = sum(((k_nums - info['position']) / k_nums) * info['score'] for info in frame_info)
    # Average the weighted frame scores
    avg_score = sum_part / n
    # Apply the logarithmic factor: boosts videos with more frames
    log_factor = math.log2(n + 1) if higher_is_better else 1 / math.log2(n + 1)
    # Calculate the final score by multiplying the average score by the logarithmic factor
    final_score = avg_score * log_factor
    # Return the final score; negate it if lower scores are better
    return final_score if higher_is_better else -final_score

# Helper function to extract the ranking score from a video dictionary
def get_ranking_score(item):
    """
    Helper function to retrieve the ranking score from a video dictionary.

    Args:
        item: Dictionary containing video details, including the 'ranking_score' key.

    Returns:
        The ranking score value for the video.
    """

    return item['ranking_score']

def re_ranking(faiss_scores, faiss_indices, 
               graph_scores, graph_indices, 
               k_num, 
               boost_amount = 2):
    """
    Re-rank items based on scores from FAISS and Graph methods, combining their contributions with an optional boost.

    Args:
        faiss_scores (list): List of scores obtained from the FAISS search.
        faiss_indices (list): List of indices corresponding to the FAISS scores.
        graph_scores (list): List of scores obtained from the Graph-based retrieval.
        graph_indices (list): List of indices corresponding to the Graph scores.
        k_num (int): The number of top results to return after re-ranking.
        boost_amount (int, optional): A factor to boost the score if an index appears in both FAISS and Graph results (default is 2).

    Returns:
        tuple: A tuple containing:
            - refined_scores (list): The top k refined scores after re-ranking.
            - refined_indexes (list): The corresponding indices of the top k refined scores.

    Process:
        1. Convert the FAISS and Graph scores to NumPy arrays for easier manipulation.
        2. Normalize the FAISS scores (lower is better) and Graph scores (higher is better) to a [0, 1] scale.
        3. Create dictionaries to map indices to their normalized scores for both FAISS and Graph results.
        4. Merge all unique indices from both FAISS and Graph results.
        5. For each unique index, compute the final score as a weighted sum of the normalized FAISS and Graph scores.
        6. Apply a boost factor to the final score if the index is present in both results.
        7. Sort the final scores in descending order and return the top k scores and their corresponding indices.
    """

    # Convert FAISS and Graph scores to numpy arrays for easier manipulation
    faiss_scores = np.array(faiss_scores)
    graph_scores = np.array(graph_scores)

    # Normalize FAISS scores (lower original scores are better, so we invert the scale)
    faiss_min = np.min(faiss_scores)
    faiss_max = np.max(faiss_scores)
    normalized_faiss_scores = (faiss_max - faiss_scores) / (faiss_max - faiss_min)

    # Normalize Graph scores (higher original scores are better, so we keep the scale)
    graph_min = np.min(graph_scores)
    graph_max = np.max(graph_scores)
    normalized_graph_scores = (graph_scores - graph_min) / (graph_max - graph_min)

    # Create dictionaries for easy lookup of normalized scores by their indices
    faiss_dict = dict(zip(faiss_indices, normalized_faiss_scores))
    graph_dict = dict(zip(graph_indices, normalized_graph_scores))

    # Merge all unique indices from both FAISS and Graph results
    all_results = set(faiss_indices).union(set(graph_indices))

    # Initialize the final scores dictionary
    final_scores = {}

    # Calculate final scores for each unique result
    for result in all_results:
        # Retrieve normalized FAISS and Graph scores; default to 0.0 if not found
        faiss_score = faiss_dict.get(result, 0.0)
        graph_score = graph_dict.get(result, 0.0)

        # Calculate the weights for combining FAISS and Graph scores
        total_score = faiss_score + graph_score
        faiss_weight = faiss_score / total_score if total_score != 0 else 0
        graph_weight = graph_score / total_score if total_score != 0 else 0

        # Compute the base final score as a weighted sum of FAISS and Graph scores
        final_score = (faiss_weight * faiss_score + graph_weight * graph_score)

        # Apply a boost factor if the result is present in both FAISS and Graph indices
        boost_factor = boost_amount if (result in faiss_indices and result in graph_indices) else 1
        final_score *= boost_factor

        # Store the computed final score
        final_scores[result] = final_score

    # Sort the results based on final scores in descending order (higher score is better)
    sorted_results = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    refined_indexes = [result[0] for result in sorted_results][:k_num]
    refined_scores = [result[1] for result in sorted_results][:k_num]

    return refined_scores, refined_indexes

def remove_first_n_elements(d, n):
    """
    Remove the first n elements from a dictionary and return a new dictionary.

    Args:
        d (dict): The original dictionary from which elements will be removed.
        n (int): The number of elements to remove from the start of the dictionary.

    Returns:
        dict: A new dictionary containing the elements after the first n elements have been removed.

    Process:
        1. Convert the dictionary items into a list of (key, value) tuples.
        2. Slice the list to remove the first n elements.
        3. Convert the modified list of tuples back into a dictionary and return it.
    """

    items = list(d.items()) # Convert the dictionary items into a list of (key, value) tuples
    items = items[n:] # Remove the first n elements

    return dict(items)