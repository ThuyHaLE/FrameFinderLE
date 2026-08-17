# database/db_init.py

import json
import torch

import faiss
import multiprocessing

# Configure logging to output to the notebook
import logging

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

CONFIG_PATH = 'config/databases.json'

def load_database_configs(config_path=CONFIG_PATH):
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading database config from {config_path}: {e}")
        raise

def load_annotation(info_dict_path):
    try:
        with open(info_dict_path, 'r') as openfile:
            return json.load(openfile)
    except Exception as e:
        logger.error(f"Error loading annotation from {info_dict_path}: {e}")
        return None

def faiss_database_processing(database_name='hnsw_jinaclipv2', config_path=CONFIG_PATH):
    num_threads = multiprocessing.cpu_count()
    logger.info(f"Number of threads: {num_threads}")

    db_configs = load_database_configs(config_path)

    if database_name not in db_configs:
        raise ValueError(
            f"Unsupported database name '{database_name}'. "
            f"Choose one of: {list(db_configs.keys())}"
        )

    config = db_configs[database_name]
    database_path = config['index_path']
    info_dict_path = config['info_path']

    # Load metadata
    image_info_dict = load_annotation(info_dict_path)
    logger.info(f"Load annotation {info_dict_path}: DONE!")

    # Load FAISS index
    index = faiss.read_index(database_path)

    if config.get('index_type') == 'hnsw':
        ef_search = config.get('hnsw_ef_search', 128)
        index.hnsw.efSearch = ef_search
        logger.info(f"Set HNSW efSearch={ef_search}")

    logger.info(f"Load database {database_name}: DONE!")

    logger.info(f'Index loaded: ntotal={index.ntotal}, dimension={index.d}')
    logger.info(f'Metadata loaded: {len(image_info_dict)} entries')
    assert index.ntotal == len(image_info_dict), 'Mismatch between index entries and metadata entries!'

    _sample_key = next(iter(image_info_dict))
    logger.info(f"Sample metadata entry (key={_sample_key}):")
    logger.info(image_info_dict[_sample_key])

    logger.info(f"The index for {database_name} is ready!!!")

    return index, image_info_dict
    
def load_jinaclipv2_encoded_frames(device, database_name='jinaclipv2_encoded_frames', config_path=CONFIG_PATH):
    db_configs = load_database_configs(config_path)

    if database_name not in db_configs:
        raise ValueError(
            f"Unsupported database name '{database_name}'. "
            f"Choose one of: {list(db_configs.keys())}"
        )

    encoded_frames_path = db_configs[database_name]['encoded_frames_path']
    encoded_frames = torch.load(encoded_frames_path, map_location=device, weights_only=True)
    logger.info(f"Load encoded frames {encoded_frames_path}: DONE!")
    return encoded_frames