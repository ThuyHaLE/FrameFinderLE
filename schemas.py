# schemas.py

"""
Pydantic request/response models shared across routers.

Separated from app.py and individual routers to:
  - Allow multiple routers (search_router, refine_router, ...) to import
    SearchRequest without importing each other.
  - Change fields/validation in one place only. 
"""

from typing import List, Optional
from pydantic import BaseModel

class SearchRequest(BaseModel):
    # Type 1 & 3
    query: Optional[str] = None
    # Type 2 — N ordered scene queries (2–5)
    queries: Optional[List[str]] = None
    strict: bool = True
    minOccurrences: Optional[int] = None
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
