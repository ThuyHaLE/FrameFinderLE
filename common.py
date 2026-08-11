"""
common.py — Shared exception cho các route chưa implement.
====================================================================
Mọi router import NOT_IMPLEMENTED từ đây để dùng chung 1 message,
tránh lặp lại HTTPException(...) ở mỗi file router.

Lưu ý: HTTPException là instance, không phải class — dùng
`raise NOT_IMPLEMENTED` là đủ, không cần gọi lại constructor.
"""

from fastapi import HTTPException

NOT_IMPLEMENTED = HTTPException(
    status_code=501,
    detail="Route chưa được implement. Frontend sẽ tự fallback về mock data.",
)
