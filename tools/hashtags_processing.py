##############################################
#--------------Helper Functions---------------
##############################################

# tools/hashtags_processing.py

import torch
import numpy as np
from collections import deque

import spacy
# Load the spaCy model for English
nlp = spacy.load('en_core_web_sm')

import logging
# Set up logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def encode_hashtag(hashtag, 
                   clip, 
                   device, 
                   model):
    """
    Encode a given hashtag into a feature vector using the CLIP model.

    Args:
        hashtag (str): The hashtag to encode.

    Returns:
        torch.Tensor: The normalized feature vector of the encoded hashtag.
    """
    text_inputs = clip.tokenize([hashtag], truncate=True).to(device)  # Tokenize and move to device (e.g., GPU)

    with torch.no_grad():
        text_features = model.encode_text(text_inputs)

    text_features /= text_features.norm(dim=-1, 
                                        keepdim=True)  # Normalize the features
    
    return text_features

def similarity_score(distance):
    """
    Calculate the similarity score based on the given distance.

    Args:
        distance (float): The distance between two items, where a lower distance indicates higher similarity.

    Returns:
        float: The calculated similarity score, normalized to be in the range [0, 1].
    """

    return 1 / (1 + distance)

def find_similar_hashtags(unseen_hashtag, 
                          hashtag_embeddings, 
                          index, clip, 
                          device, model, k = 10):
    """
    Find hashtags that are semantically similar to an unseen hashtag.

    Args:
        unseen_hashtag (str): The hashtag to find similar hashtags for.
        hashtag_embeddings (dict): A dictionary mapping hashtags to their embeddings.

    Returns:
        list: A list of hashtags that are similar to the unseen hashtag.
    """

    unseen_embedding = encode_hashtag(unseen_hashtag, 
                                      clip, device, model)

    word_list = list(hashtag_embeddings.keys())

    # Perform the similarity search
    distances, indices = index.search(unseen_embedding, 
                                      k)
    
    similar_hashtags = [word_list[idx] for dist, idx in zip(distances[0], indices[0]) 
                        if similarity_score(dist) >= 0.85]
    
    return similar_hashtags

def calculate_score(G, hashtag, 
                    neighbor, 
                    path, alpha=0.7):
    """
    Calculate the score for a neighbor based on both neighbor frequency and path length.

    Args:
        G (networkx.Graph): Graph containing hashtag nodes and their relationships.
        hashtag (str): The current hashtag for which the score is being calculated.
        neighbor (str): The neighbor hashtag whose score is to be computed.
        path (tuple): The path from the original hashtag to the current neighbor.
        alpha (float): Weight for balancing neighbor frequency and path length (0-1, default is 0.7).

    Returns:
        float: Calculated score combining neighbor frequency and path length.
    """

    # Get the frequency of the edge between the current hashtag and the neighbor
    neighbor_freq = G[hashtag][neighbor]['weight']

    # Calculate the path length factor, which decreases with longer paths
    path_length = len(path)
    path_factor = 1 / (1 + np.log(path_length))

    # Combine neighbor frequency and path factor into a single score
    score = alpha * neighbor_freq + (1 - alpha) * path_factor

    return score

def initialize_queue_with_hashtags(query_hashtags, 
                                   hashtag_embeddings, 
                                   hashtag_index, 
                                   clip, device, model, 
                                   k = 10):
    """
    Initialize a queue with known hashtags or find similar hashtags if not directly available.
    
    Args:
        query_hashtags (list): A list of hashtags to initialize the queue with.
        hashtag_embeddings (dict): A dictionary mapping hashtags to their embeddings.
        hashtag_index (dict): A mapping of hashtags to their respective indices in the embedding matrix.
        clip (model): CLIP model used for hashtag similarity search.
        device (torch.device): Device to run the model on (CPU or GPU).
        model (torch.nn.Module): The neural network model to compute embeddings.
        k (int): Number of similar hashtags to find for unseen hashtags (default is 10).

    Returns:
        deque: A deque containing tuples with hashtags, their exploration depth, path, and initial score.
    """

    queue = deque()

    for hashtag in query_hashtags:
        if hashtag in hashtag_embeddings:
            # Directly add known hashtags to the queue with an initial score of 1.0
            queue.append((hashtag, 0, (), 1.0))
        else:
            # Find similar hashtags if the current hashtag is not directly available
            logger.info(f"{hashtag} is not in hashtag_embeddings!!!")
            similar_hashtags = find_similar_hashtags(hashtag, 
                                                     hashtag_embeddings, 
                                                     hashtag_index, 
                                                     clip, 
                                                     device, model, 
                                                     k)
            queue.extend((h, 0, (), 1.0) for h in similar_hashtags)  # Add similar hashtags with initial score of 1.0

    return queue
