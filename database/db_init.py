import json
import torch

import faiss
import multiprocessing
import pickle

# Configure logging to output to the notebook
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def load_grafa_database(grafa_path = 'database/graph_data_full.pkl'):
    with open(grafa_path, 'rb') as f:
        data = pickle.load(f)
        G = data['G']
        sparse_matrix = data['sparse_matrix']
        node_mapping = data['node_mapping']
        reverse_node_mapping = data['reverse_node_mapping']
        logger.info(f"Load GRAFA database {grafa_path}: DONE!")
    return G, sparse_matrix, node_mapping, reverse_node_mapping

def load_hashtag_embeddings(hashtag_embeddings_path = 'database/hashtag_embeddings.pkl'):
    with open(hashtag_embeddings_path, 'rb') as f:
        hashtag_embeddings = pickle.load(f)
    logger.info(f"Load hashtag embeddings {hashtag_embeddings_path}: DONE!")
    return hashtag_embeddings

def load_hashtag_embedding_bin(hashtag_embedding_bin_path = 'database/hashtag_embeddings.bin'):
    num_threads = multiprocessing.cpu_count()
    logger.info(f"Number of threads: {num_threads}")
    faiss.omp_set_num_threads(num_threads)
    hashtag_embedding_index = faiss.read_index(hashtag_embedding_bin_path, faiss.IO_FLAG_MMAP)
    logger.info(f"The IndexFlatL2 index {hashtag_embedding_bin_path} is ready!!!")
    return hashtag_embedding_index

def load_annotation(image_info_dict_path = 'database/index_caption_hashtag_dict_v2.json'):
    with open(image_info_dict_path, 'r') as openfile:
        image_info_dict = json.load(openfile)
    logger.info(f"Load annotation {image_info_dict_path}: DONE!")
    return image_info_dict

def load_encoded_frames(device, encoded_frames_path = 'database/encoded_frames.pt'):
    encoded_frames = torch.load(encoded_frames_path, 
                                map_location=device, 
                                weights_only=True)
    logger.info(f"Load encoded frames {encoded_frames_path}: DONE!")
    return encoded_frames

def faiss_database_processing(database_name):
    num_threads = multiprocessing.cpu_count()
    logger.info(f"Number of threads: {num_threads}")
    if database_name == 'CLIP_v0':
        database_path = 'database/merged_index_hnsw_baseline_v0.bin'
    elif database_name == 'CLIP_v2':
        database_path = 'database/merged_index_hnsw_baseline_v2.bin'
    else:
        raise ValueError("Unsupported database name. Choose 'CLIP_v0' or 'CLIP_v2'.")
    logger.info(f"Load database {database_name}: DONE!")
    faiss.omp_set_num_threads(num_threads)
    index_hnsw = faiss.read_index(database_path, faiss.IO_FLAG_MMAP)
    logger.info(f"The HNSW index for {database_name} is ready!!!")
    return index_hnsw