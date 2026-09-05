# utils.py

"""
Helper functions shared between app.py and routers.

Separated so that routers (e.g., routers/data_router.py) can import
without depending on app.py (avoiding circular import).
"""

import math


def parse_timestamp(ts: str) -> float:
    """
    Parse timestamp string → seconds (float).
    Accepts:
        '0:00:08.300000'   annotation format
        '00:08:30'         hh:mm:ss (paste from video player)
        '00:08:30.500'     hh:mm:ss.SSS
        '0:08'             hh:mm (not seconds)
    """
    try:
        parts = ts.strip().split(":")
        h = int(parts[0])
        m = int(parts[1])
        s = float(parts[2]) if len(parts) > 2 else 0.0
        return h * 3600 + m * 60 + s
    except Exception:
        return 0.0


def build_thumbnail_url(frame_path: str) -> str:
    """
    'key_frame_folder_videos-l13/keyframe_L13_V001/0000207_8.3.jpg'
    → '/static/images/key_frame_folder_reduced/key_frame_folder_videos-l13_reduced/keyframe_L13_V001/0000207_8.3.webp'
    """
    folder, rest = frame_path.split("/", 1)
    new_path = f"{folder}_reduced/{rest}".replace(".jpg", ".webp")
    return f"/static/images/key_frame_folder_reduced/{new_path}"


def paginate(items: list, page: int, per_page: int) -> dict:
    total = len(items)
    total_pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    return {
        "items": items[start: start + per_page],
        "total": total,
        "totalPages": total_pages,
        "page": page,
    }
