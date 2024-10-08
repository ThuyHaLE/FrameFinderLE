##############################################
#--------------Main Functions---------------
##############################################

# tools/graph_based_image_retrieval.py

import numpy as np
from collections import defaultdict, deque
from tools.hashtags_processing import calculate_score, initialize_queue_with_hashtags

import logging
# Set up logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def retrieve_by_hashtags(sparse_matrix, node_mapping, reverse_node_mapping, G,
                         query_hashtags, hashtag_embeddings, hashtag_index, clip, device, model, 
                         k_num=5, max_depth=5, alpha=0.7, similarity_num = 10,
                         min_score_threshold=0.01, max_keyframes=1000, max_iterations=10000):
    """
    Retrieve keyframes based on a list of query hashtags using a graph-based approach called Dynamic Hashtag Exploration.
    Combines neighbor frequency and path information to rank keyframes.
    
    Args:
    sparse_matrix (scipy.sparse.csr_matrix): Sparse matrix representing the hashtag co-occurrence graph.
    node_mapping (dict): Maps hashtags to indices in the sparse matrix.
    reverse_node_mapping (dict): Maps matrix indices back to hashtags.
    G (networkx.Graph): Graph of hashtag nodes and relationships.
    query_hashtags (list): Initial hashtags to start exploring the graph.
    hashtag_embeddings (dict): Precomputed embeddings for each hashtag.
    hashtag_index (dict): Mapping of hashtags to their respective indices in the embedding matrix.
    clip (model): CLIP model used for hashtag similarity search.
    device (torch.device): Device to run the model on (CPU or GPU).
    model (torch.nn.Module): The neural network model to compute embeddings.
    k_num (int): Number of top keyframes to retrieve (default is 5).
    max_depth (int): Maximum depth to explore in the graph (default is 5).
    alpha (float): Balances neighbor frequency vs path length in scoring (default is 0.7).
    similarity_num (int): Number of similar hashtags to consider for unseen hashtags (default is 10).
    min_score_threshold (float): Minimum score threshold to include a hashtag (default is 0.01).
    max_keyframes (int): Maximum number of keyframes to retrieve (default is 1000).
    max_iterations (int): Maximum number of iterations to perform (default is 10000).

    Returns:
    tuple: A tuple containing two lists:
        - scores: List of normalized scores for the top keyframes.
        - results: List of top keyframes based on the scores.
    
    Process:
    1. Initialize a queue with query hashtags and their embeddings to start exploration.
    2. Traverse the graph up to `max_depth`, visiting neighboring hashtags of the query hashtags.
    3. For each valid neighbor, calculate a score using a hybrid method combining neighbor frequency and path length.
    4. Track keyframe scores and update them using unique paths to avoid repetitive exploration.
    5. Normalize the scores and select the top `k_num` keyframes based on these scores.
    
    Stopping Criteria:
    - Stop when the number of processed keyframes exceeds `max_keyframes`.
    - Stop when the number of iterations exceeds `max_iterations`.
    - Stop exploring a hashtag if its score drops below `min_score_threshold`.

    Scoring:
    - Each keyframe score is adjusted by considering both the number of unique paths leading to it and the similarity
      of neighboring hashtags. The score grows logarithmically with the number of unique paths to avoid over-inflation
      from repeated paths.
    
    Exploration Strategy:
    - Dynamic exploration refines the depth exploration by prioritizing hashtags with high scores. If a hashtag's score
      exceeds the mean score at the current level, it is added to the next level's queue. Otherwise, it is deprioritized.
    
    Returns:
    - A list of scores and a list of keyframes, both sorted in descending order.
    """

    # Dictionary to accumulate scores for each keyframe
    global_weight_dict = defaultdict(float)
    # Dictionary to store unique paths leading to each keyframe
    path_dict = defaultdict(set)
    # Set to track visited hashtags
    visited = set()

    iteration_count = 0
    keyframe_count = 0

    # Initialize the exploration queue with the given query hashtags
    queue = initialize_queue_with_hashtags(query_hashtags, 
                                           hashtag_embeddings, 
                                           hashtag_index, 
                                           clip, device, model, 
                                           similarity_num)
    logger.info(f'Initial hashtags in queue: {list(queue)}')

    for depth in range(max_depth):
        # List to store scores of neighbors at the current depth
        level_scores = []
        # Queue for the next depth level
        next_level_queue = deque()

        while queue:  # Process the current level of the queue
            hashtag, current_depth, path, current_score = queue.popleft()

            # Check stopping criteria
            if current_score < min_score_threshold:
                continue
            if keyframe_count >= max_keyframes:
                logger.info(f"Stopped: Reached maximum number of keyframes ({max_keyframes})")
                break
            if iteration_count >= max_iterations:
                logger.info(f"Stopped: Reached maximum number of iterations ({max_iterations})")
                break

            iteration_count += 1

            # Skip already visited hashtags
            if hashtag in visited:
                continue
            visited.add(hashtag)

            # Skip hashtags not in the node mapping
            if hashtag not in node_mapping:
                continue

            # Skip invalid indices
            hashtag_idx = node_mapping[hashtag]
            if hashtag_idx >= sparse_matrix.shape[0]:
                continue

            # Retrieve and validate neighbors
            neighbors = sparse_matrix[hashtag_idx].nonzero()[1]
            valid_neighbors = [(neighbor_idx, reverse_node_mapping.get(neighbor_idx, None))
                               for neighbor_idx in neighbors if neighbor_idx < sparse_matrix.shape[1]]

            # Process each valid neighbor
            for neighbor_idx, neighbor in valid_neighbors:
                if neighbor is None:
                    continue

                new_path = path + (hashtag,)
                new_score = current_score * calculate_score(G, 
                                                            hashtag, 
                                                            neighbor, 
                                                            new_path, 
                                                            alpha)

                if G.nodes[neighbor].get('label') == 'keyframe':
                    # Update keyframe score based on the new score and unique paths
                    path_dict[neighbor].add(new_path)
                    unique_paths = len(path_dict[neighbor])
                    global_weight_dict[neighbor] += new_score * np.log(1 + unique_paths)
                    keyframe_count += 1
                else:
                    # Add neighbors to the next level queue
                    next_level_queue.append((neighbor, current_depth + 1, new_path, new_score))
                    level_scores.append(new_score)

        # Dynamic exploration based on mean score
        if level_scores:
            mean_score = np.mean(level_scores)
            # Prioritize high-scoring hashtags for the next level
            queue = deque(item for item in next_level_queue if item[3] >= mean_score)
            queue.extend(item for item in next_level_queue if item[3] < mean_score)

        # Check if we've reached any stopping criteria
        if keyframe_count >= max_keyframes or iteration_count >= max_iterations:
            break

    # Normalize scores to make them proportional
    total_weight = sum(global_weight_dict.values())
    if total_weight > 0:
        for keyframe in global_weight_dict:
            global_weight_dict[keyframe] /= total_weight

    # Sort keyframes by score and select the top k
    sorted_results = sorted(global_weight_dict.items(), key=lambda x: x[1], reverse=True)

    results = [keyframe for keyframe, _ in sorted_results[:k_num]]
    scores = [score for _, score in sorted_results[:k_num]]

    indices = [int(info[0]) for info in results]
    
    return scores, indices