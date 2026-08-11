"""
routers/query_router.py — Keyword graph suggestion route
====================================================================
Chứa:
    POST /api/process_query
"""

from fastapi import APIRouter

from common import NOT_IMPLEMENTED
from schemas import ProcessQueryRequest

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/process_query")
def process_query(req: ProcessQueryRequest):
    """
    Trả keyword gợi ý từ keyword graph.
    """
    # TODO:
    # 1. word-segment req.query_text bằng underthesea/pyvi
    # 2. chuẩn hoá Unicode NFC
    # 3. graph expansion → trả top keywords
    raise NOT_IMPLEMENTED
