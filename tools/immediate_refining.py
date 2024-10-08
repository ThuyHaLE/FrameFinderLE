##############################################
#--------------Main Functions---------------
##############################################

# tools/immediate_refining.py

import torch
from tools.feedback_processing import convert2binary_scores, similarities_calculating

def immediate_refining(initialDBIdx, initialDBScore, feedback_status, encoded_frames):
    """
    Refine the current set of database scores based on user feedback (likes/dislikes) and similarity calculations.

    Args:
        initialDBIdx (list): Indices of the initial database entries.
        initialDBScore (list): Initial scores associated with the database entries.
        feedback_status (dict): A dictionary containing feedback status with the key as the index of the item
                                and the value as either 'like', 'dislike', or neutral (any other value).
        encoded_frames (Tensor): Precomputed tensor of encoded frames representing database entries for similarity calculations.

    Returns:
        tuple: A tuple containing:
            - sorted_scores (list): Updated list of scores sorted in descending order based on feedback adjustments.
            - sorted_indices (list): Indices of the database entries sorted by their updated scores.

    Process:
        1. Convert the feedback statuses into binary scores using `convert2binary_scores` for items in `initialDBIdx`.
        2. Extract the encoded representations of the initial database indices from `encoded_frames`.
        3. Iterate through each feedback item:
            - For 'like' feedback, increase the score based on similarity between the current item and other items.
            - For 'dislike' feedback, reduce the score similarly.
            - If the action is neutral, no score modification is done.
        4. After feedback adjustments, sort the updated scores in descending order and return them with the corresponding sorted indices.
    """

    # Convert feedback to binary tensor representation
    feedback_tensor = convert2binary_scores(initialDBIdx, feedback_status)
    
    # Retrieve the encoded representation of the initial database indices
    initialDBIdx_encoding = encoded_frames[torch.tensor(initialDBIdx)].unsqueeze(0)

    # Convert initial scores to tensor
    current_scores = torch.tensor(initialDBScore)

    # Loop through each feedback item
    for idx, action in feedback_status.items():
        # Retrieve the encoded representation of the feedback item
        fb_encoding = encoded_frames[torch.tensor([idx])].unsqueeze(1)
        # Calculate similarity and similarity weights between feedback item and the initial database items
        similarities, similarity_weights = similarities_calculating(fb_encoding, 
                                                                    initialDBIdx_encoding, 
                                                                    dim=2)
        # Update scores based on feedback type (like or dislike)
        if action == 'like':
            new_scores = current_scores + (similarity_weights * feedback_tensor).sum(dim=0, 
                                                                                     keepdim=True)
        elif action == 'dislike':
            new_scores = current_scores + (similarity_weights * feedback_tensor).sum(dim=0, 
                                                                                     keepdim=True)
        else:
            # No change for neutral feedback
            new_scores = current_scores
        # Update the current scores with the new ones
        current_scores = new_scores

    # Sort the updated scores in descending order and retrieve sorted indices
    sorted_scores, indices = torch.sort(current_scores, 
                                        dim=1, descending=True)
    
    # Map the sorted indices back to the original database indices
    sorted_indices = [initialDBIdx[int(i)] for i in indices[0]]

    return sorted_scores[0].tolist(), sorted_indices