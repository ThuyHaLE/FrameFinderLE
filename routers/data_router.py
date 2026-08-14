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

    # thumbnail is already built at load time — no need to transform again

    # Get pool by video_ID
    # - NOT filter           → all ~200k frames
    # - Exact "L13_V001"     → O(1) lookup from video_index
    # - Prefix "L13"         → combine all V of that L (O(number of videos in L))
    if not video_ID:
        items = all_frames
    elif "_V" in video_ID:
        # Exact match: "L13_V001"
        items = list(video_index.get(video_ID, []))
    else:
        # Prefix match: "L13" → get all keys starting with "L13_"
        prefix = f"{video_ID}_"
        items = []
        for vid_key, frames in video_index.items():
            if vid_key.startswith(prefix):
                items.extend(frames)
        # Sort by video_id and timestamp_sec for consistent ordering
        items.sort(key=lambda r: (r["video_id"], r["timestamp_sec"]))

    # Filter / sort by timestamp (only apply when video_ID is specified to avoid sorting 200k items)
    # Use timestamp_sec (pre-computed float) instead of parsing string each time
    if timestamp and video_ID:
        start_sec = parse_timestamp(timestamp)
        if timestamp_end:
            end_sec = parse_timestamp(timestamp_end)
            items = [
                r for r in items
                if start_sec <= r["timestamp_sec"] <= end_sec
            ]
            items = sorted(items, key=lambda r: r["timestamp_sec"])
        else:
            # Only start timestamp provided → sort by the frame closest to that time
            items = sorted(
                items,
                key=lambda r: abs(r["timestamp_sec"] - start_sec),
            )

    paged = paginate(items, page, perPage)
    return {
        "keyframes": paged["items"],
        "total": paged["total"],
        "totalPages": paged["totalPages"],
        "page": paged["page"],
    }