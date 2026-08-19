# routers/event_router.py

"""
Event Browser routes

Includes:
    GET /api/events — browse events (transcript-segmented, from FLATIP_DANGVANTUAN)
                       by video_ID, optionally range-filtered by event_id.

Unlike /api/data (frame browsing, filtered by timestamp), events are filtered
by event_id range instead of a time range:
    - event_id_start: defaults to 0 (first event of the video) when omitted
    - event_id_end:   defaults to -1, a sentinel meaning "last event of the
                       video" (resolved server-side to that video's max event_id)

IMPORTANT: event_id is LOCAL to each video (resets to 0 per video, per the
FLATIP_DANGVANTUAN data format) — filtering by event_id therefore only makes
sense when exactly one video is selected (video_ID like "L21_V001"), not a
bare "L21" prefix covering many videos. The filter is silently skipped
otherwise; the frontend enforces the exact-video requirement before sending
the range so this should not normally be hit.

Filtering is done by matching the event_id VALUE, not list position, because
ALL_EVENTS (built in model_state.py) drops events whose frames could not all
be resolved via frame_by_path — the event_id sequence for a video may have
gaps, so index-based slicing would be wrong.

State (all_events, event_index) is retrieved via Depends() from deps.py —
router does NOT import `model_state` directly, same DI pattern as data_router.py.
"""

from typing import Dict, List

from fastapi import APIRouter, Depends

from deps import get_all_events, get_event_index
from utils import paginate

router = APIRouter(prefix="/api", tags=["events"])


def _parse_event_id(raw: str, default: int) -> int:
    """Parse an event_id query param, falling back to `default` on empty/invalid input."""
    raw = (raw or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@router.get("/events")
def get_events(
    page: int = 1,
    perPage: int = 50,
    video_ID: str = "",
    event_id_start: str = "",   # empty -> 0
    event_id_end: str = "",     # empty or "-1" -> last event_id of the video
    all_events: List[dict] = Depends(get_all_events),
    event_index: Dict[str, List[dict]] = Depends(get_event_index),
):
    """Browse events by video_ID, optionally range-filtered by event_id."""

    is_exact_video = "_V" in video_ID

    # 1. Get pool by video_ID
    if not video_ID:
        items = all_events
    elif is_exact_video:
        items = list(event_index.get(video_ID, []))
    else:
        prefix = f"{video_ID}_"
        items = []
        for vid_key, events in event_index.items():
            if vid_key.startswith(prefix):
                items.extend(events)

    # 2. Compute max_event_id from the FULL pool for this video, BEFORE the
    #    range filter is applied and independent of pagination — this is what
    #    the frontend uses to show the real "last event" value in the UI
    #    (placeholder / ▲▼ shift fallback), so it must not be affected by
    #    event_id_start/event_id_end or by perPage.
    max_event_id = max((e["event_id"] for e in items), default=None) if is_exact_video else None

    # 3. Filter by event_id range -- only meaningful (and only applied) when
    #    exactly one video is selected, since event_id restarts per video.
    if is_exact_video and (event_id_start or event_id_end) and items:
        start_id = _parse_event_id(event_id_start, default=0)
        raw_end = _parse_event_id(event_id_end, default=-1)
        end_id = max_event_id if raw_end < 0 else raw_end
        items = [e for e in items if start_id <= e["event_id"] <= end_id]

    # 4. Sort by video_id, then event_id (chronological within a video,
    #    since event_id is assigned in transcript-segment order)
    items = sorted(items, key=lambda e: (e["video_id"], e["event_id"]))

    # 5. Paginate
    paged = paginate(items, page, perPage)
    return {
        "events": paged["items"],
        "total": paged["total"],
        "totalPages": paged["totalPages"],
        "page": paged["page"],
        "maxEventId": max_event_id,  # null when video_ID isn't an exact "L..._V..." id
    }