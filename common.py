# common.py

"""
Shared exception for routes NOT implemented.

All router imports NOT_IMPLEMENTED from here to use a common message,
avoiding repeating HTTPException(...) in each router file.
Note: HTTPException is an instance, not a class — using
`raise NOT_IMPLEMENTED` is sufficient, no need to call the constructor again.
"""

from fastapi import HTTPException

NOT_IMPLEMENTED = HTTPException(
    status_code=501,
    detail="Route chưa được implement. Frontend sẽ tự fallback về mock data.",
)
