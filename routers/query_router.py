"""
routers/query_router.py — Keyword graph suggestion route
====================================================================
Chứa:
    POST /api/process_query
"""

from fastapi import APIRouter

from common import NOT_IMPLEMENTED
from schemas import ProcessQueryRequest
from tools.keywords_utils import get_keywords

router = APIRouter(prefix="/api", tags=["query"])

@router.post("/process_query")
def process_query(req: ProcessQueryRequest):
    """Return suggested keywords from the keyword graph."""
    keywords = get_keywords(req.query_text) 
    return {"keywords": keywords}
    #raise NOT_IMPLEMENTED