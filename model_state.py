"""
model_state.py — Load model & search index 1 lần lúc import.
====================================================================
Cùng pattern với state.py (dataset): mọi thứ nặng (model, FAISS
index, encoded_frames) được load 1 lần ở module-level khi module
này được import lần đầu — KHÔNG load lại mỗi request, KHÔNG gắn
vào app.state (để router không cần `Request` mới lấy được).

Router lấy các object này qua Depends() trong deps.py, ví dụ:
    from deps import get_model, get_clipv0_index
    def route(model = Depends(get_model)): ...
"""

from models.model_init import load_model
from database.db_init import (
    load_encoded_frames,
    faiss_database_processing,
)

DEVICE, MODEL = load_model()
ENCODED_FRAMES = load_encoded_frames(DEVICE)
CLIPV0_HNSW, IMAGE_INFO_DICT = faiss_database_processing("CLIP_v0")
