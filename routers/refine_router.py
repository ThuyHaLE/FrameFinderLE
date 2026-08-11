"""
routers/refine_router.py — Refine routes (Type 1, 2, 3)
====================================================================
Chứa:
    POST /api/search/frame/refine
    POST /api/search/event-boundary/refine
    POST /api/search/event-mention/refine

Feedback store lấy qua Depends(get_feedback_store) — giống cách
data_router lấy all_frames/video_index/l_options, KHÔNG import
`state` trực tiếp.
"""

from typing import Dict

from fastapi import APIRouter, Depends

from common import NOT_IMPLEMENTED
from deps import get_feedback_store
from schemas import SearchRequest

router = APIRouter(prefix="/api/search", tags=["refine"])


@router.post("/frame/refine")
def refine_frame(
    req: SearchRequest,
    feedback_store: Dict[str, dict] = Depends(get_feedback_store),
):
    """Refine Type 1 dựa trên feedback (immediate + aggregated)."""
    # TODO:
    # 1. đọc feedback_store[req.sessionId]
    # 2. chạy immediate_refining hoặc aggregated_refining
    # 3. paginate, trả về
    raise NOT_IMPLEMENTED


@router.post("/event-boundary/refine")
def refine_event_boundary(
    req: SearchRequest,
    feedback_store: Dict[str, dict] = Depends(get_feedback_store),
):
    raise NOT_IMPLEMENTED


@router.post("/event-mention/refine")
def refine_event_mention(
    req: SearchRequest,
    feedback_store: Dict[str, dict] = Depends(get_feedback_store),
):
    raise NOT_IMPLEMENTED
