# routers/event_router.py

"""
Event Browser routes

Includes:
    GET /api/events — browse events (transcript-segmented, from FLATIP_DANGVANTUAN)
                       by video_ID, paginated.

Unlike /api/data (frame browsing), there is no timestamp_start/timestamp_end
filter here — an event already IS a time range (start/end), so filtering is
by video_ID only. If range-overlap filtering is wanted later, add
timestamp/timestamp_end query params here mirroring data_router.py's pattern.

State (all_events, event_index) is retrieved via Depends() from deps.py —
router does NOT import `model_state` directly, same DI pattern as data_router.py.
"""

from typing import Dict, List

from fastapi import APIRouter, Depends

from deps import get_all_events, get_event_index
from utils import paginate

router = APIRouter(prefix="/api", tags=["events"])


@router.get("/events")
def get_events(
    page: int = 1,
    perPage: int = 50,
    video_ID: str = "",
    all_events: List[dict] = Depends(get_all_events),
    event_index: Dict[str, List[dict]] = Depends(get_event_index),
):
    """Browse events by video_ID."""

    # 1. Get pool by video_ID (same prefix-matching convention as /api/data:
    #    exact "L13_V001" -> single video; "L13" prefix -> all V of that L)
    if not video_ID:
        items = all_events
    elif "_V" in video_ID:
        items = list(event_index.get(video_ID, []))
    else:
        prefix = f"{video_ID}_"
        items = []
        for vid_key, events in event_index.items():
            if vid_key.startswith(prefix):
                items.extend(events)

    # 2. Sort by video_id, then start time — deterministic, chronological within each video
    items = sorted(items, key=lambda e: (e["video_id"], e["start"]))

    # 3. Paginate
    paged = paginate(items, page, perPage)
    return {
        "events": paged["items"],
        "total": paged["total"],
        "totalPages": paged["totalPages"],
        "page": paged["page"],
    }