import json
import torch

import faiss
import multiprocessing

# Configure logging to output to the notebook
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def faiss_database_processing(database_name='CLIP_v0'):
    num_threads = multiprocessing.cpu_count()
    logger.info(f"Number of threads: {num_threads}")

    # Load the FAISS index and image info dictionary based on the database name
    if database_name == 'CLIP_v0':
        database_path = 'static/databases/faiss-index-hnsw-jinaclipv2-v0/merged_index_hnsw_jinaclipv2_v0.bin'
        image_info_dict_path = 'static/databases/faiss-index-hnsw-jinaclipv2-v0/image_info_dict.json'
    else:
        raise ValueError("Unsupported database name. Choose 'CLIP_v0'.")
    logger.info(f"Load database {database_name}: DONE!")

    # Load the image info dictionary from the JSON file
    image_info_dict = load_annotation(image_info_dict_path)
    logger.info(f"Load annotation {image_info_dict_path}: DONE!")

    # Load the FAISS index from the binary file
    index_hnsw = faiss.read_index(database_path)
    # adjust runtime parameters for HNSW index, 
    # more higher = more accurate but slower, no need to rebuild     the index
    index_hnsw.hnsw.efSearch = 128  

    # Debugging: Log the number of entries in the index and metadata
    logger.info(f'Index loaded: ntotal={index_hnsw.ntotal}, dimension={index_hnsw.d}')
    logger.info(f'Metadata loaded: {len(image_info_dict)} entries')
    assert index_hnsw.ntotal == len(image_info_dict), 'Mismatch between index entries and metadata entries!'

    # Log a sample entry from the metadata for verification
    _sample_key = next(iter(image_info_dict))
    logger.info(f"Sample metadata entry (key={_sample_key}):")
    logger.info(image_info_dict[_sample_key])

    # Log that the HNSW index is ready
    logger.info(f"The HNSW index for {database_name} is ready!!!")

    return index_hnsw, image_info_dict

def load_annotation(image_info_dict_path):
    # Load the image info dictionary from a JSON file
    try:
        with open(image_info_dict_path, 'r') as openfile:
            image_info_dict = json.load(openfile)
        return image_info_dict
    except Exception as e:
        logger.error(f"Error loading annotation from {image_info_dict_path}: {e}")
        return None
    
def load_encoded_frames(device, encoded_frames_path = 'static/databases/encoded_frames/encoded_frames.pt'):
    # Load the encoded frames from a PyTorch file
    encoded_frames = torch.load(encoded_frames_path, 
                                map_location=device, 
                                weights_only=True)
    logger.info(f"Load encoded frames {encoded_frames_path}: DONE!")
    return encoded_frames