# routers/event_router.py

"""
Event Browser routes

Includes:
    GET /api/events — browse events (transcript-segmented, from FLATIP_DANGVANTUAN)
                       by video_ID, paginated.

Design note: FLATIP_DANGVANTUAN.info_dict is a flat list of events (each with
video_id/event_id/start/end/keyframes/text). ALL_EVENTS / EVENT_INDEX are
derived from it once at import time in model_state.py — same "load once,
never per-request" convention as state.py / HNSW.

Unlike /api/data (frame browsing), there is no timestamp filter here — an
event already IS a time range. Filtering is by video_ID, and optionally a
specific event_id once a single video (exact "L13_V001") is selected —
mirrors the "timestamp only unlocks after exact video" rule in data_router.py.

State (all_events, event_index) is retrieved via Depends() from deps.py —
router does NOT import `model_state` directly, same DI pattern as data_router.py.
"""

from typing import Dict, List

from fastapi import APIRouter, Depends

from deps import get_all_events, get_event_index
from utils import paginate

router = APIRouter(prefix="/api", tags=["events"])


def _serialize_event(e: dict) -> dict:
    """Map raw FLATIP event shape -> response shape expected by frontend (fetchEvents mock)."""
    keyframes = e.get("keyframes", [])
    return {
        "video_id": e["video_id"],
        "event_id": e["event_id"],
        "start": e["start"],
        "end": e["end"],
        "text": e.get("text", ""),
        "frames": keyframes,
        "frame_count": len(keyframes),
    }


@router.get("/events")
def get_events(
    page: int = 1,
    perPage: int = 50,
    video_ID: str = "",
    event_id: str = "",
    all_events: List[dict] = Depends(get_all_events),
    event_index: Dict[str, List[dict]] = Depends(get_event_index),
):
    """Browse events by video_ID, optionally a single event_id within an exact video."""

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

    # 2. event_id filter — only meaningful once a single video is selected,
    #    same rule as timestamp filter in data_router.py
    if "_V" in video_ID and event_id:
        items = [e for e in items if str(e["event_id"]) == event_id]

    # 3. Sort by video_id, then start time — deterministic, chronological within each video
    items = sorted(items, key=lambda e: (e["video_id"], e["start"]))

    # 4. Serialize -> map raw event shape to response shape
    serialized = [_serialize_event(e) for e in items]

    # 5. Paginate
    paged = paginate(serialized, page, perPage)
    return {
        "events": paged["items"],
        "total": paged["total"],
        "totalPages": paged["totalPages"],
        "page": paged["page"],
    }