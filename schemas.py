"""
schemas.py — Pydantic request/response models dùng chung cho các router.
====================================================================
Tách riêng khỏi app.py và khỏi từng router để:
  - Nhiều router (search_router, refine_router, ...) cùng import
    SearchRequest mà không phải import lẫn nhau.
  - Đổi field / validation chỉ cần sửa 1 chỗ.
"""

from typing import List, Optional

from pydantic import BaseModel


class SearchRequest(BaseModel):
    # Type 1 & 3
    query: Optional[str] = None
    # Type 2
    start_query: Optional[str] = None
    end_query: Optional[str] = None
    # Options
    keywords: List[str] = []
    k: int = 100
    displayOption: str = "sort_by_frame_index"
    page: int = 1
    imagesPerPage: int = 50
    sessionId: Optional[str] = None


class FeedbackRequest(BaseModel):
    db_idx: int
    action: str        # 'like' | 'dislike' | None
    session_id: str


class ProcessQueryRequest(BaseModel):
    query_text: str
