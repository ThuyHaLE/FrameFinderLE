# tools/search_utils.py

"""
Search helpers shared for search_router.py

Includes:
    search(...)                 — encode 1 query, search FAISS, return top-k
    search_batch(...)           — encode lots of queries at once (more efficient)
    pair_boundary_results(...)  — get pairs (start, end) for Type 2

Architecture note:
functions here are designed to accept index/device/image_info_dict as PARAMETERS
(defaulting to model_state if not passed), so that:
    - Router can call with values from Depends() — keeping the DI pattern
        that deps.py has built (easy to mock for testing).
    - Notebook / standalone script can still call normally, without
        changing anything (if nothing is passed, it will default to model_state).

Note on field names: IMAGE_INFO_DICT uses the ORIGINAL names from the JSON annotation
(video_ID, time_in_seconds, frame_ID...), NOT the normalized names in state.ALL_FRAMES (video_id, timestamp_sec, db_idx...).
All comparisons/joins in this file must use the original names.
"""

from typing import List, Optional
import model_state
from tools.faiss_retrieval import k_image_search
from tools.query_encoding import encode_texts
from utils import build_thumbnail_url

"""
Lookup frame_path -> db_idx, build 1 time when module is imported.
Used to join FAISS results (which don't have db_idx) back to state.ALL_FRAMES
(which has db_idx, used for feedback/like-dislike).

IMPORTANT: only use this lookup if you've confirmed that frame_ID in
IMAGE_INFO_DICT does NOT overlap with db_idx in state.ALL_FRAMES.
If they do overlap, you can skip this join step and use info["frame_ID"] directly.
"""

try:
    import state
    _FRAME_PATH_TO_DB_IDX = {
        item["frame_path"]: item["db_idx"] for item in state.ALL_FRAMES
    }
except Exception:
    # Allow this file to run independently in a notebook without state.py
    _FRAME_PATH_TO_DB_IDX = {}


def _enrich(info: dict, dist: float, idx: int) -> dict:
    """Add faiss_idx, distance, db_idx, thumbnail to a result record."""
    info = dict(info)
    info["faiss_idx"] = int(idx)
    info["distance"] = float(dist)
    info["db_idx"] = _FRAME_PATH_TO_DB_IDX.get(info.get("frame_path"))
    info["thumbnail"] = build_thumbnail_url(info["frame_path"])
    return info


def search_batch(queries: List[str], k: int = 5, 
                 truncate_dim: Optional[int] = None,
                 index=None, device=None, 
                 image_info_dict: Optional[dict] = None,) -> List[List[dict]]:
    """
    Find top-k keyframes for multiple queries at once — more efficient than calling search() repeatedly
    because it encodes the queries only once.

    :param queries: list of query strings
    :param k: number of results to return for EACH query
    :param truncate_dim: MUST match the truncate_dim used when encoding images
    :param index: FAISS/HNSW index; defaults to model_state.CLIPV0_HNSW
    :param device: defaults to model_state.DEVICE
    :param image_info_dict: defaults to model_state.CLIPV0_IMAGE_INFO_DICT
    :return: list[list[dict]] — a list of results for each query, in the same order as the input
    """
    index = index if index is not None else model_state.CLIPV0_HNSW
    device = device if device is not None else model_state.DEVICE
    image_info_dict = (
        image_info_dict if image_info_dict is not None else model_state.CLIPV0_IMAGE_INFO_DICT
    )

    query_embeddings = encode_texts(queries, truncate_dim=truncate_dim, show_progress=False)

    distances, indices = k_image_search(
        query_vector=query_embeddings,
        index_hnsw=index,
        device=device,
        k_nums=k,
    )

    all_results = []
    for q_dist, q_idx in zip(distances, indices):
        results = []
        for dist, idx in zip(q_dist, q_idx):
            if idx == -1:
                continue
            info = image_info_dict[str(idx)]
            results.append(_enrich(info, dist, idx))
        all_results.append(results)
    return all_results


def search(query: str, k: int = 5, truncate_dim: Optional[int] = None,
           index=None, device=None, image_info_dict: Optional[dict] = None,) -> List[dict]:
    """Find top-keyframe matches for a single query. Wrapper around search_batch()."""
    return search_batch(
        [query], k=k, truncate_dim=truncate_dim,
        index=index, device=device, image_info_dict=image_info_dict,
    )[0]