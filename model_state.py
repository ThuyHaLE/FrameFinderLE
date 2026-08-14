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

from typing import Dict
from models.model_init import load_model
from database.db_init import (
    load_encoded_frames,
    faiss_database_processing,
)

DEVICE, MODEL = load_model()
ENCODED_FRAMES = load_encoded_frames(DEVICE)
CLIPV0_HNSW, CLIPV0_IMAGE_INFO_DICT = faiss_database_processing("CLIP_v0")

# row index (0..N-1) trong ENCODED_FRAMES <-> frame_path
# GIẢ ĐỊNH: CLIPV0_IMAGE_INFO_DICT[idx_str]["frame_path"] cùng format
# với state.ALL_FRAMES[i]["frame_path"]. Nếu field tên khác, đổi ở đây.
FRAME_PATH_TO_ROW: Dict[str, int] = {
    info["frame_path"]: int(idx_str)
    for idx_str, info in CLIPV0_IMAGE_INFO_DICT.items()
}