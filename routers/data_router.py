# routers/data_router.py

"""
Data Browser routes

Includes:
    GET /api/data              — browse keyframes by video_ID / timestamp
    GET /api/videos/l-options  — list of "L" for dropdown (same data group)

State (all_frames, video_index, l_options) is retrieved via Depends() 
from deps.py — router does NOT import `app` directly to avoid circular import.
"""

from typing import Dict, List

from fastapi import APIRouter, Depends

from deps import get_all_frames, get_l_options, get_video_index
from utils import paginate, parse_timestamp

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/videos/l-options")
def get_l_options_route(l_options: List[str] = Depends(get_l_options)):
    """Returns a list of valid "L" values (e.g., ["01", "02", ...]) present in the current dataset."""
    return {"lOptions": l_options}


@router.get("/data")
def get_data(
    page: int = 1,
    perPage: int = 50,
    video_ID: str = "",
    timestamp: str = "",        # start time
    timestamp_end: str = "",    # end time (optional)
    all_frames: List[dict] = Depends(get_all_frames),
    video_index: Dict[str, List[dict]] = Depends(get_video_index),
):
    """Browse keyframes by video_ID / timestamp."""

    # 1. Get pool by video_ID
    if not video_ID:
        items = all_frames
    elif "_V" in video_ID:
        items = list(video_index.get(video_ID, []))
    else:
        prefix = f"{video_ID}_"
        items = []
        for vid_key, frames in video_index.items():
            if vid_key.startswith(prefix):
                items.extend(frames)

    # 2. Filter & Sort by timestamp
    if video_ID:
        if timestamp:
            start_sec = parse_timestamp(timestamp)
            if timestamp_end:
                end_sec = parse_timestamp(timestamp_end)
                items = [r for r in items if start_sec <= r["timestamp_sec"] <= end_sec]
            else:
                items = [r for r in items if r["timestamp_sec"] >= start_sec]

        # Sort by video_id and timestamp_sec
        items.sort(key=lambda r: (r["video_id"], r["timestamp_sec"]))

    # 3. Paginate
    paged = paginate(items, page, perPage)
    return {
        "keyframes": paged["items"],
        "total": paged["total"],
        "totalPages": paged["totalPages"],
        "page": paged["page"],
    }