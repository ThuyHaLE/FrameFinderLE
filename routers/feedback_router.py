"""
routers/feedback_router.py — Feedback route
====================================================================
Chứa:
    POST /api/update_feedback

Route này đã có logic thật (không raise 501) — chỉ lưu like/dislike
vào FEEDBACK_STORE lấy qua Depends(get_feedback_store).
"""

from typing import Dict

from fastapi import APIRouter, Depends

from deps import get_feedback_store
from schemas import FeedbackRequest

router = APIRouter(prefix="/api", tags=["feedback"])


@router.post("/update_feedback")
def update_feedback(
    req: FeedbackRequest,
    feedback_store: Dict[str, dict] = Depends(get_feedback_store),
):
    """
    Lưu like/dislike vào FEEDBACK_STORE.
    Route này đơn giản — implement sớm nhất vì không cần model/DB.
    """
    # TODO (optional): persist sang DB thật thay vì in-memory
    session = feedback_store.setdefault(req.session_id, {})
    session[req.db_idx] = req.action
    return {"feedbackStatus": req.action, "dbIdx": req.db_idx}
