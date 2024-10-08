
from functools import lru_cache
from typing import Optional
import time
from fastapi import FastAPI

from tools.query_encoding import encode_description
from tools.faiss_retrieval import k_image_search
from tools.results_display import display_option_results, get_keyframes, get_keyframes_w_filter
from tools.utils import re_ranking
from database.db_init import faiss_database_processing
from tools.graph_based_image_retrieval import retrieve_by_hashtags

import clip

# Configure logging to output to the notebook
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@lru_cache(maxsize=128)
def cached_get_keyframes(page: int, 
                         per_page: int, 
                         video_ID: Optional[str] = '', 
                         timestamp: Optional[str] = ''):
    """
    Retrieve keyframes from the database with optional filtering by video ID and timestamp.

    Args:
        page (int): The current page number for pagination.
        per_page (int): The number of keyframes to retrieve per page.
        video_ID (Optional[str]): The ID of the video to filter keyframes (default is an empty string).
        timestamp (Optional[str]): The timestamp to filter keyframes (default is an empty string).

    Returns:
        list: A list of keyframes retrieved from the database, either filtered or unfiltered based on the inputs.

    Process:
        1. Check if both video_ID and timestamp are not provided.
            - If true, call the `get_keyframes` function to retrieve all keyframes with pagination.
        2. If either video_ID or timestamp is provided, call the `get_keyframes_w_filter` function 
           to retrieve keyframes with the specified filters.

    Note:
        If both video_ID and timestamp are absent, all keyframes will be fetched based on the provided pagination parameters.
    """

    if not video_ID and not timestamp:
        return get_keyframes('database/index_caption_hashtag_dict_v2.json',
                             page=page,
                             per_page=per_page)
    else:
        return get_keyframes_w_filter('database/index_caption_hashtag_dict_v2.json',
                                      page=page,
                                      per_page=per_page,
                                      video_ID=video_ID,
                                      timestamp=timestamp or '00:00:00')
    
@lru_cache(maxsize=128)
def perform_search(db_idx: int, 
                   app: FastAPI):
    """
    Perform a search for images based on a specific database index.

    Args:
        db_idx (int): The index of the database entry for which to perform the search.
        app (FastAPI): The FastAPI application instance, containing necessary state information.

    Returns:
        list: A list of results containing images sorted according to the specified display option.

    Process:
        1. Retrieve the encoded frames from the application state.
        2. Extract the query vector corresponding to the given database index.
        3. Use the `k_image_search` function to perform a search in the HNSW index, retrieving the top 50 closest images.
        4. Specify the display option for sorting results (in this case, by frame index).
        5. Call the `display_option_results` function to format and retrieve the search results based on the distances and indices found.

    Note:
        The search is based on the encoded representation of the images, and results are sorted by frame index for presentation.
    """

    encoded_frames = app.state.encoded_frames
    query_vector = encoded_frames[db_idx].unsqueeze(0)

    clipv0_hnsw = app.state.clipv0_hnsw
    device = app.state.device
    clipv0_distances, clipv0_indexs = k_image_search(query_vector, 
                                                     clipv0_hnsw, 
                                                     device, k_nums=50)
    
    display_option = 'sort_by_frame_index'
    image_info_dict = app.state.image_info_dict
    results = display_option_results(display_option, 
                                     clipv0_distances, clipv0_indexs, 
                                     image_info_dict)
    
    return results

@lru_cache(maxsize=128)
def cached_results(query_text: str, hiddenHashtags: str,
                   database_name: str, k: int, display_option: str,
                   app: FastAPI):
    
    """
    Retrieve and cache results based on a user query and optional hashtags.

    Args:
        query_text (str): The text query to search for in the database.
        hiddenHashtags (str): A comma-separated string of hashtags to filter results.
        database_name (str): The name of the database to query.
        k (int): The number of top results to return.
        display_option (str): The display option for formatting results.
        app (FastAPI): The FastAPI application instance for accessing shared state.

    Returns:
        tuple: A tuple containing:
        results (list): The filtered results based on the query and hashtags.
        hiddenInitialDBIdx (list): The indices of the initial database entries.
        hiddenInitialDBScore (list): The scores associated with the initial database entries.

    Process:
        1. Parse and log incoming data for debugging.
        2. Retrieve relevant components from the FastAPI application state, including the model and embeddings.
        3. Determine which retrieval method to use based on the presence of the query text and hashtags:
            - If both are provided, perform FAISS and graph-based retrieval.
            - If only hashtags are provided, perform graph-based retrieval.
            - If only the query text is provided, perform FAISS-based retrieval.
        4. Filter and display the results according to the specified display option.
        5. Return the results along with the corresponding indices and scores.

    Logging:
        Logs incoming parameters, execution status, and execution time for debugging and monitoring purposes.
    """
    
    # Log incoming data for debugging
    hashtags_list = hiddenHashtags.split(',') if hiddenHashtags else []
    logger.info(f"Received query_text: {query_text}")
    logger.info(f"Received hashtags: {type(hashtags_list)}, {hashtags_list}")
    logger.info(f"Received database_name: {database_name}")
    logger.info(f"Received k number: {k}")
    logger.info(f"Received display_option: {display_option}")

    if not query_text and not hiddenHashtags:
      logger.info(f"status_code=400, detail=At least one of query text or hashtags must be provided.")

    model = app.state.model
    device = app.state.device
    sparse_matrix = app.state.sparse_matrix
    node_mapping = app.state.node_mapping
    node_mapping = app.state.node_mapping
    reverse_node_mapping = app.state.reverse_node_mapping
    G = app.state.G
    hashtag_embeddings = app.state.hashtag_embeddings
    hashtag_index = app.state.hashtag_embedding_index
    image_info_dict = app.state.image_info_dict


    start_time = time.time()

    if len(hashtags_list) != 0 and query_text != '':
      #FAISS database Processing
      index_hnsw = faiss_database_processing(database_name)
      #FAISS and GRAPH based retrieval process
      query_vector = encode_description(model, device, query_text)
      distances_hnsw, indices_hnsw = k_image_search(query_vector, index_hnsw, device, k_nums=k)
      graph_scores, graph_indices = retrieve_by_hashtags(sparse_matrix, node_mapping, reverse_node_mapping, G,
                                                         hashtags_list, hashtag_embeddings, hashtag_index, clip, device, model,
                                                         k_num=k, max_depth=5, alpha=0.7, similarity_num = 10,
                                                         min_score_threshold=0.01, max_keyframes=10000, max_iterations=10000)
      refined_scores, refined_indexes = re_ranking(distances_hnsw, indices_hnsw,
                                                   graph_scores, graph_indices,
                                                   k_num=k, boost_amount = 2)
      #Filter and Display Results
      results = display_option_results(display_option,
                                       refined_scores, refined_indexes,
                                       image_info_dict, graph=True)
      execution_time = time.time() - start_time
      logger.info("The result-extracting process is completed!!!")
      logger.info(f"Program Executed in {execution_time}")

    if len(hashtags_list) != 0 and not query_text:
      #GRAPH based retrieval process
      graph_scores, graph_indices = retrieve_by_hashtags(sparse_matrix, node_mapping, reverse_node_mapping, G,
                                                         hashtags_list, hashtag_embeddings, hashtag_index, clip, device, model,
                                                         k_num=k, max_depth=5, alpha=0.7, similarity_num = 10,
                                                         min_score_threshold=0.01, max_keyframes=10000, max_iterations=10000)
      logger.info("The retrieval process is completed!!!")
      #Filter and Display Results
      results = display_option_results(display_option,
                                       graph_scores, graph_indices,
                                       image_info_dict, graph=True)
      execution_time = time.time() - start_time
      logger.info("The result-extracting process is completed!!!")
      logger.info(f"Program Executed in {execution_time}")

    if query_text != '' and len(hashtags_list) == 0:
      #FAISS database Processing
      index_hnsw = faiss_database_processing(database_name)
      #FAISS based retrieval process
      query_vector = encode_description(model, device, query_text)
      distances_hnsw, indices_hnsw = k_image_search(query_vector, index_hnsw,
                                                    device, k_nums=k)
      logger.info("The retrieval process is completed!!!")
      #Filter and Display Results
      results = display_option_results(display_option,
                                       distances_hnsw, indices_hnsw,
                                       image_info_dict)
      execution_time = time.time() - start_time
      logger.info("The result-extracting process is completed!!!")
      logger.info(f"Program Executed in {execution_time}")

    hiddenInitialDBIdx = [[data['db_idx'] for data in result.values()][0] for result in results]
    hiddenInitialDBScore = [[data['score'] for data in result.values()][0] for result in results]

    return results, hiddenInitialDBIdx, hiddenInitialDBScore

def paginate_results(results, 
                     page: int, 
                     images_per_page: int):
    """
    Paginate a list of results for display purposes.

    Args:
        results (list): A list of results to be paginated.
        page (int): The page number to retrieve.
        images_per_page (int): The number of images to display per page.

    Returns:
        tuple: A tuple containing:
        paginated_results (list): A subset of results for the requested page.
        total_images (int): The total number of images in the results.
        total_pages (int): The total number of pages based on the number of images per page.

    Process:
        1. Calculate the total number of images from the results.
        2. Determine the total number of pages based on the images per page.
        3. Validate the requested page number to ensure it falls within the valid range.
        4. Calculate the start and end indices for slicing the results list to get the paginated results.
        5. Return the sliced results along with total images and total pages.

    Logging:
        Logs the total number of results, total pages, current page, and paginated results for debugging purposes.
    """

    total_images = len(results)
    logger.info(f"Total results: {[[data['db_idx'] for data in result.values()][0] for result in results]}")
    total_pages = (total_images + images_per_page - 1) // images_per_page
    logger.info(f"Total page: {total_pages}")
    # Validate page number
    page = max(1, min(page, total_pages))
    logger.info(f"Current page: {page}")
    start_idx = (page - 1) * images_per_page
    end_idx = min(start_idx + images_per_page, total_images)
    paginated_results = results[start_idx:end_idx]
    logger.info(f"Paginated results: {[[data['db_idx'] for data in result.values()][0] for result in paginated_results]}")
    return paginated_results, total_images, total_pages