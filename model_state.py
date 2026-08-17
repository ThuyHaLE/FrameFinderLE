# model_state.py

"""
Load model & search index once at import time.

With the same pattern as state.py (dataset):
everything heavy (model, FAISS index, encoded_frames) is loaded once at the module-level
when this module is first imported — DO NOT load again per request,
DO NOT attach to app.state (so that the router does not need `Request` to access them).
Router gets these objects via Depends() in deps.py, e.g.:
    from deps import get_model, get_clipv0_index
    def route(model = Depends(get_model)): ...
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict

from models.model_init import load_model
from database.db_init import (
    load_jinaclipv2_encoded_frames,
    faiss_database_processing,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VectorDB:
    index: Any
    info_dict: Dict[str, Any]

logger.info("Loading jinaclipv2 model...")
DEVICE, JINACLIPV2_MODEL = load_model(model_name='jina-clip-v2')

logger.info("Loading dangvantuan model...")
_DANGVANTUAN_DEVICE, DANGVANTUAN_MODEL = load_model(model_name='dangvantuan')

if _DANGVANTUAN_DEVICE != DEVICE:
    logger.warning(
        "Device mismatch between models: jina-clip-v2 on '%s', dangvantuan on '%s'. "
        "Using '%s' as the shared DEVICE.",
        DEVICE, _DANGVANTUAN_DEVICE, DEVICE,
    )

logger.info("Loading jinaclipv2 encoded frames...")
JINACLIPV2_ENCODED_FRAMES = load_jinaclipv2_encoded_frames(DEVICE, database_name='jinaclipv2_encoded_frames')

logger.info("Loading hnsw_jinaclipv2 index...")
_hnsw_index, _hnsw_info_dict = faiss_database_processing("hnsw_jinaclipv2")
HNSW_JINACLIPV2 = VectorDB(index=_hnsw_index, info_dict=_hnsw_info_dict)

logger.info("Loading flatip_dangvantuan index...")
_flatip_index, _flatip_info_dict = faiss_database_processing("flatip_dangvantuan")
FLATIP_DANGVANTUAN = VectorDB(index=_flatip_index, info_dict=_flatip_info_dict)

logger.info("All model state loaded successfully.")

# row index (0..N-1) trong JINACLIPV2_ENCODED_FRAMES <-> frame_path
# GIẢ ĐỊNH: HNSW_JINACLIPV2.info_dict[idx_str]["frame_path"] cùng format
# với state.ALL_FRAMES[i]["frame_path"]. Nếu field tên khác, đổi ở đây.
_missing_frame_path = [
    idx_str for idx_str, info in HNSW_JINACLIPV2.info_dict.items()
    if "frame_path" not in info
]
if _missing_frame_path:
    raise ValueError(
        f"Missing 'frame_path' field in HNSW_JINACLIPV2.info_dict entries "
        f"(e.g. keys: {_missing_frame_path[:5]}{'...' if len(_missing_frame_path) > 5 else ''})"
    )

FRAME_PATH_TO_ROW: Dict[str, int] = {
    info["frame_path"]: int(idx_str)
    for idx_str, info in HNSW_JINACLIPV2.info_dict.items()
}