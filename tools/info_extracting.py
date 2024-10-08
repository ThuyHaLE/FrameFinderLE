##############################################
#--------------Helper Functions---------------
##############################################

# tools/info_extracting.py
from tools.utils import calculate_video_ranking_score, get_ranking_score

def extract_information_w_ranking(distances, indices, 
                                  image_info_dict, 
                                  higher_is_better=False):
    """
    Group frames by their video ID, calculate ranking scores for each video based on its frames,
    and return a sorted list of videos.

    Args:
        distances: List of scores (e.g., similarity scores) corresponding to each frame, typically returned by FAISS.
        indices: List of frame indices corresponding to the distances.
        image_info_dict: Dictionary containing metadata for each frame, where keys are frame indices (as strings).
        higher_is_better: Boolean flag indicating whether higher scores are better (default is False).

    Returns:
        A sorted list of videos, where each video is represented by a dictionary containing:
        video_ID: The video ID.
        ranking_score: The calculated ranking score for the video.
        frame_info: List of dictionaries with detailed information about each frame in the video.

    Process:
        1. Frames are grouped by their video ID using the frame index and the `image_info_dict`.
        2. For each video, the ranking score is calculated based on the frame's position and score using
        the `calculate_video_ranking_score` function.
        3. The list of videos is then sorted based on the calculated ranking scores, in either ascending
        or descending order based on the `higher_is_better` flag.
    """
    
    info_dict = {}  # Dictionary to store frame info grouped by video ID
    
    k_nums = len(indices)  # Total number of frames (used for position weighting)
    
    # Group frames by their video ID
    for i, (score, idx) in enumerate(zip(distances, indices)):
        frame_info = image_info_dict[str(idx)]  # Get frame information by its index
        video_ID = frame_info['video_ID']  # Extract the video ID from the frame info
        # Initialize the list for a video if it's not already in the dictionary
        if video_ID not in info_dict:
            info_dict[video_ID] = []
        # Append frame details including position, score, and metadata to the corresponding video
        info_dict[video_ID].append({'position': i + 1,  # Use 1-based index for the frame's position
                                    'score': score,  # Frame's score (e.g., similarity score from FAISS)
                                    'db_idx': idx,  # Database index of the frame
                                    'idx': frame_info['frame_ID'],  # Frame ID
                                    'timestamp': frame_info['timestamp'],  # Frame timestamp
                                    'image_path': frame_info['frame_path'].replace('.jpg', '.webp')  # Path to the frame image
                                  })
    
    # List to store videos and their calculated ranking scores
    ranked_videos = []

    # For each video, calculate its ranking score based on its frames
    for video_ID, frame_info in info_dict.items():
        ranking_score = calculate_video_ranking_score(frame_info, k_nums, 
                                                      higher_is_better)
        ranked_videos.append({'video_ID': video_ID,  # Video ID
                              'ranking_score': ranking_score,  # Calculated ranking score
                              'frame_info': frame_info  # List of frames for the video
                              })
        
    # Sort videos by their ranking score (ascending or descending based on `higher_is_better`)
    sorted_videos = sorted(ranked_videos, 
                           key=get_ranking_score, 
                           reverse=higher_is_better)

    return sorted_videos  # Return the sorted list of videos

def extract_information(distances, indices, 
                        image_info_dict):
    """
    Extracts information from the retrieval results.

    Args:
        distances (list): List of distances from the query.
        indices (list): List of indices of the retrieved images.
        image_info_dict (dict): Dictionary containing image metadata.

    Returns:
        list: A list of dictionaries containing image information.
    """

    info_list = []

    for score, idx in zip(distances, indices):
        try:
            # Retrieve metadata for each image
            frame_ID = image_info_dict[str(idx)]['frame_ID']
            video_ID = image_info_dict[str(idx)]['video_ID']
            frame_path = image_info_dict[str(idx)]['frame_path'].replace('.jpg', '.webp')
            timestamp = image_info_dict[str(idx)]['timestamp']
            # Append the information to the list
            info_list.append({
                video_ID: {
                    'score': score,
                    'db_idx': idx,
                    'idx': frame_ID,
                    'timestamp': timestamp,
                    'image_path': frame_path
                }
            })
        except KeyError:
            continue  # Skip if there is a missing key

    return info_list