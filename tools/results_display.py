##############################################
#--------------Helper Functions---------------
##############################################

# tools/results_display.py
import json
import logging
from typing import Optional
from tools.utils import str_to_timedelta
from tools.info_extracting import extract_information_w_ranking, extract_information

# Set up logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def convert_results_4display(results, 
                             higher_is_better=False):
    """
    Convert the video ranking results into a display-ready format by sorting frames within each video 
    and cleaning up unnecessary data.

    Args:
        results: List of dictionaries, where each dictionary contains:
        video_ID: The unique ID of the video.
        frame_info: List of dictionaries with detailed information about each frame.
        higher_is_better: Boolean flag indicating whether higher frame scores are better (default is False).

    Returns:
        list: A list of dictionaries, where each dictionary represents a frame and its associated video.
        The frames within each video are sorted by their score, either in ascending or descending order 
        based on the `higher_is_better` flag. The 'position' field is removed from each frame's information, 
        as it's not needed for display.
    """

    new_results = []  # List to store the modified results for display 

    # Iterate through each video result
    for videoID_dict in results:
        video_ID = videoID_dict['video_ID']  # Get the video ID
        frame_info = videoID_dict['frame_info']  # Get the list of frames for the video
        # Sort frames by their score (ascending or descending based on `higher_is_better`)
        sorted_frames = sorted(frame_info, key=lambda x: x['score'], reverse=higher_is_better)
        # Iterate through the sorted frames and prepare them for display
        for frame in sorted_frames:
            if 'position' in frame:
                frame.pop('position')  # Remove the 'position' field from the frame information 
            # Append the video ID and frame information to the results list
            new_results.append({video_ID: frame})

    return new_results  # Return the modified list of results

def display_option_results(display_option, 
                           distances_hnsw, indices_hnsw, 
                           image_info_dict, graph=False):
    """
    Extracts and converts search results based on the specified display option.

    Args:
        display_option (str): Determines how results are displayed. Options are 'group_by_videoid' or other.
        distances_hnsw (np.ndarray): Array of distances from the FAISS index search.
        indices_hnsw (np.ndarray): Array of indices from the FAISS index search.
        image_info_dict (dict): Dictionary with image information used for result extraction.

    Returns:
        list: A list of results formatted for display based on the selected display option.
    """
    logger.info(f"Processing display option: {display_option}")
    if display_option == 'group_by_videoid':
        if graph==True:
            sorted_results = extract_information_w_ranking(distances_hnsw, indices_hnsw, 
                                                           image_info_dict, 
                                                           higher_is_better=True)
            results = convert_results_4display(sorted_results, 
                                               higher_is_better=True)
        else:
            sorted_results = extract_information_w_ranking(distances_hnsw, indices_hnsw, 
                                                           image_info_dict)
            results = convert_results_4display(sorted_results)
    elif display_option == 'sort_by_frame_index':
        results = extract_information(distances_hnsw, indices_hnsw, 
                                      image_info_dict)
    else:
        raise ValueError("Unsupported display option. Choose 'group_by_videoid' or 'sort_by_frame_index'.")
    logger.info(f"Results ready for display based on option: {display_option}")
    return results

def get_keyframes(image_info_dict_path: str, 
                  page: int, 
                  per_page: int):
    """
    Reads a JSON file containing keyframe information and returns a paginated list of keyframes
    for a specified page and number of items per page. Each keyframe entry contains the frame ID, 
    modified frame path (replacing image folder path and converting '.jpg' to '.webp'), video ID, 
    and timestamp.

    Args:
        image_info_dict_path (str): Path to the JSON file containing the keyframe information.
        page (int): The page number to return.
        per_page (int): The number of keyframes to return per page.

    Returns:
        paginated_keyframes (list): A list of dictionaries, each representing a keyframe with 
        'frame_ID', 'frame_path', 'video_ID', and 'timestamp' fields.
        total_keyframes (int): The total number of keyframes available.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        json.JSONDecodeError: If there is an issue decoding the JSON file.
    """

    try:
        # Attempt to open and load the JSON file
        with open(image_info_dict_path, 'r') as openfile:
            image_info_dict = json.load(openfile)
    except FileNotFoundError:
        logger.error(f"File {image_info_dict_path} not found.")
        raise
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file {image_info_dict_path}.")
        raise

    # Process and format keyframe information
    keyframes = [{
        'frame_ID': frame_info['frame_ID'],
        'frame_path': frame_info['frame_path'].replace('.jpg', '.webp'),
        'video_ID': frame_info['video_ID'],
        'timestamp': frame_info['timestamp']
    } for frame_info in image_info_dict.values()]

    # Pagination logic
    start = (page - 1) * per_page
    end = start + per_page
    paginated_keyframes = keyframes[start:end]

    # Return the paginated list of keyframes and total keyframe count
    return paginated_keyframes, len(keyframes)

def get_keyframes_w_filter(image_info_dict_path: str,
                           page: int,
                           per_page: int,
                           video_ID: Optional[str] = '',
                           timestamp: Optional[str] = ''):
    """
    Retrieves a paginated list of keyframes from a JSON file, with optional filters based on 
    video ID and timestamp. The function processes the keyframes to return only those that match 
    the specified filters.

    Args:
        image_info_dict_path (str): Path to the JSON file containing the keyframe information.
        page (int): The page number for pagination.
        per_page (int): The number of keyframes to return per page.
        video_ID (Optional[str]): The ID of the video to filter keyframes by. Defaults to an empty string.
        timestamp (Optional[str]): The timestamp to filter keyframes by. Defaults to an empty string.

    Returns:
        paginated_keyframes (list): A list of dictionaries representing the filtered keyframes, 
        each containing 'frame_ID', 'frame_path', 'video_ID', and 'timestamp'.
        total_keyframes (int): The total number of keyframes after applying the filters.

    Raises:
        FileNotFoundError: If the specified JSON file does not exist.
        json.JSONDecodeError: If there is an issue decoding the JSON file.

    Logging:
        Logs received parameters and the modified filter time.
        Logs the number of keyframes after filtering.
    """

    try:
        # Attempt to open and load the JSON file
        with open(image_info_dict_path, 'r') as openfile:
            image_info_dict = json.load(openfile)
    except FileNotFoundError:
        logger.error(f"File {image_info_dict_path} not found.")
        raise
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from file {image_info_dict_path}.")
        raise

    logger.info(f"Received video_ID: {video_ID}")
    logger.info(f"Received timestamp: {type(timestamp)}, {timestamp}")

    # Convert timestamp to a timedelta if provided
    filter_time = str_to_timedelta(timestamp) if timestamp else None
    logger.info(f"Modified filter_time: {type(filter_time)}, {filter_time}")

    # Filter keyframes based on video_ID and timestamp
    keyframes = [{'frame_ID': frame_info['frame_ID'],
                  'frame_path': frame_info['frame_path'].replace('.jpg', '.webp'),
                  'video_ID': frame_info['video_ID'],
                  'timestamp': frame_info['timestamp']} for frame_info in image_info_dict.values() 
                  if video_ID and frame_info['video_ID'] == video_ID and 
                  str_to_timedelta(frame_info['timestamp']) > filter_time]

    # Pagination logic
    start = (page - 1) * per_page
    end = start + per_page
    paginated_keyframes = keyframes[start:end]
    logger.info(f"Number of keyframes after filtering: {len(keyframes)}")

    # Return the paginated list of filtered keyframes and total count
    return paginated_keyframes, len(keyframes)