"""
routers/search_router.py — Search routes (Type 1, 2, 3)
====================================================================
Chứa:
    POST /api/search/frame           — Type 1: Cảnh cụ thể (text-image)
    POST /api/search/event-boundary  — Type 2: Sự kiện đầu/cuối (text-image x2)
    POST /api/search/event-mention   — Type 3: Sự kiện trong transcript (text-text)

Router KHÔNG import trực tiếp `app` để tránh circular import.
"""

from fastapi import APIRouter, Depends

from common import NOT_IMPLEMENTED
from deps import get_device, get_model, get_clipv0_index, get_image_info_dict
from schemas import SearchRequest

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/frame")
def search_frame(
    req: SearchRequest,
    device=Depends(get_device),
    model=Depends(get_model),
    clipv0_index=Depends(get_clipv0_index),
    image_info_dict: dict = Depends(get_image_info_dict),
):
    """
    Type 1 — Cảnh cụ thể.
    Channel: text-image (query ↔ fused frame embedding).
    """
    # TODO:
    # 1. encode req.query + req.keywords bằng model (jina-clip-v2 text tower), trên `device`
    # 2. search clipv0_index (FAISS/HNSW, text-image channel), lấy top req.k
    #    → map kết quả về metadata thật qua image_info_dict
    # 3. apply display_option (sort / group)
    # 4. paginate và trả về
    raise NOT_IMPLEMENTED


@router.post("/event-boundary")
def search_event_boundary(req: SearchRequest):
    """
    Type 2 — Sự kiện cảnh đầu/cuối.
    Channel: text-image × 2 (start_query + end_query), pair by timestamp.
    """
    # TODO:
    # 1. encode req.start_query và req.end_query riêng biệt
    # 2. search FAISS 2 lần → top-K start frames, top-K end frames
    # 3. ghép cặp (start_frame, end_frame) theo ràng buộc ts_start < ts_end
    # 4. score cặp, paginate, trả về
    raise NOT_IMPLEMENTED


@router.post("/event-mention")
def search_event_mention(req: SearchRequest):
    """
    Type 3 — Sự kiện được đề cập trong transcript.
    Primary channel: text-text (query ↔ transcript segments).
    Secondary: text-image để re-rank (optional).
    """
    # TODO:
    # 1. encode req.query bằng Vietnamese text-embedding model
    # 2. search transcript index (text-text channel)
    # 3. (optional) re-rank top results bằng text-image score
    # 4. paginate, trả về
    raise NOT_IMPLEMENTED
