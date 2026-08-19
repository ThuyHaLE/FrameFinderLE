# model_state.py

"""
Load model & search index once at import time.

With the same pattern as state.py (dataset):
everything heavy (model, FAISS index, encoded_frames) is loaded once at the module-level
when this module is first imported — DO NOT load again per request,
DO NOT attach to app.state (so that the router does not need `Request` to access them).
Router gets these objects via Depends() in deps.py, e.g.:
    from deps import get_model, get_clipv0_index
    def route(model = Depends(get_model)): ...
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict
import state

from models.model_init import load_model
from database.db_init import (
    load_jinaclipv2_encoded_frames,
    faiss_database_processing,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VectorDB:
    index: Any
    info_dict: Any  # HNSW: Dict[str, dict] (key = row index string); FLATIP: List[dict] (list of events)

logger.info("Loading jinaclipv2 model...")
DEVICE, JINACLIPV2_MODEL = load_model(model_name='jina-clip-v2')

logger.info("Loading dangvantuan model...")
_DANGVANTUAN_DEVICE, DANGVANTUAN_MODEL = load_model(model_name='dangvantuan')

if _DANGVANTUAN_DEVICE != DEVICE:
    logger.warning(
        "Device mismatch between models: jina-clip-v2 on '%s', dangvantuan on '%s'. "
        "Using '%s' as the shared DEVICE.",
        DEVICE, _DANGVANTUAN_DEVICE, DEVICE,
    )

logger.info("Loading jinaclipv2 encoded frames...")
JINACLIPV2_ENCODED_FRAMES = load_jinaclipv2_encoded_frames(DEVICE, database_name='jinaclipv2_encoded_frames')

logger.info("Loading hnsw_jinaclipv2 index...")
_hnsw_index, _hnsw_info_dict = faiss_database_processing("hnsw_jinaclipv2")
HNSW_JINACLIPV2 = VectorDB(index=_hnsw_index, info_dict=_hnsw_info_dict)

logger.info("Loading flatip_dangvantuan index...")
_flatip_index, _flatip_info_dict = faiss_database_processing("flatip_dangvantuan")
FLATIP_DANGVANTUAN = VectorDB(index=_flatip_index, info_dict=_flatip_info_dict)

logger.info("All model state loaded successfully.")

# ---------------------------------------------------------------------------
# ALL_FRAMES / FRAME_PATH — derived from HNSW_JINACLIPV2.info_dict (dict of events)
# ---------------------------------------------------------------------------

logger.info("Building ALL_FRAME_PATHS / FRAME_PATH from hnsw_jinaclipv2...")

# row index (0..N-1) in JINACLIPV2_ENCODED_FRAMES <-> frame_path
# Assumption: HNSW_JINACLIPV2.info_dict[idx_str]["frame_path"] as same format
# with state.ALL_FRAMES[i]["frame_path"].
_missing_frame_path = [
    idx_str for idx_str, info in HNSW_JINACLIPV2.info_dict.items()
    if "frame_path" not in info
]
if _missing_frame_path:
    raise ValueError(
        f"Missing 'frame_path' field in HNSW_JINACLIPV2.info_dict entries "
        f"(e.g. keys: {_missing_frame_path[:5]}{'...' if len(_missing_frame_path) > 5 else ''})"
    )

FRAME_PATH_TO_ROW: Dict[str, int] = {
    info["frame_path"]: int(idx_str)
    for idx_str, info in HNSW_JINACLIPV2.info_dict.items()
}

# ---------------------------------------------------------------------------
# ALL_EVENTS / EVENT_INDEX — derived from FLATIP_DANGVANTUAN.info_dict (list of events)
# ---------------------------------------------------------------------------

logger.info("Building ALL_EVENTS / EVENT_INDEX from flatip_dangvantuan...")

if not isinstance(FLATIP_DANGVANTUAN.info_dict, list):
    raise TypeError(
        f"Expected FLATIP_DANGVANTUAN.info_dict to be a list of events, "
        f"got {type(FLATIP_DANGVANTUAN.info_dict)}"
    )

_raw_events = FLATIP_DANGVANTUAN.info_dict

ALL_EVENTS: list = []
_skipped_no_video_id = 0
_skipped_no_frames = 0
for _event in _raw_events:
    # Lưu ý field-name casing: event-level dùng "video_id" (lowercase);
    # bên trong "keyframes" của mỗi event lại dùng "video_ID" (uppercase) — không nhầm 2 field này.
    _vid = _event.get("video_id")
    if _vid is None:
        logger.warning("Event missing 'video_id' field, skipped: event_id=%s", _event.get("event_id"))
        _skipped_no_video_id += 1
        continue

    # Join raw keyframes (frame_path only) -> full frame dict (db_idx, thumbnail,
    # timestamp_sec...) via state.FRAME_BY_PATH, same pattern used everywhere else
    # (search_router.py's /similar and /event-mention). Without this join, the
    # frontend has no db_idx/thumbnail to render images or wire feedback/similar buttons.
    _frames = []
    for _kf in _event.get("keyframes", []):
        _frame = state.FRAME_BY_PATH.get(_kf.get("frame_path"))
        if _frame is not None:
            _frames.append(_frame)

    if not _frames:
        logger.warning(
            "Event has no resolvable frames, skipped: video_id=%s event_id=%s (raw keyframes=%d)",
            _vid, _event.get("event_id"), len(_event.get("keyframes", [])),
        )
        _skipped_no_frames += 1
        continue

    ALL_EVENTS.append({
        "video_id":    _vid,
        "event_id":    _event.get("event_id"),
        "start":       _event.get("start"),
        "end":         _event.get("end"),
        "text":        _event.get("text"),
        "frames":      _frames,
        "frame_count": len(_frames),
    })

EVENT_INDEX: Dict[str, list] = {}
for _ev in ALL_EVENTS:
    EVENT_INDEX.setdefault(_ev["video_id"], []).append(_ev)

logger.info(
    "Loaded %d events across %d videos (skipped: %d no video_id, %d no resolvable frames).",
    len(ALL_EVENTS), len(EVENT_INDEX), _skipped_no_video_id, _skipped_no_frames,
)

# ---------------------------------------------------------------------------
# Design assumption check: HNSW_JINACLIPV2 (frame-level) is expected to cover
# every frame referenced inside FLATIP_DANGVANTUAN events. Not enforced (raise)
# because this is a data-completeness assumption, not a schema violation —
# log loudly instead so degraded coverage is visible without hard-crashing boot.
# ---------------------------------------------------------------------------

_event_frame_paths = {
    kf["frame_path"]
    for _event in ALL_EVENTS
    for kf in _event.get("keyframes", [])
}
_missing_in_hnsw = _event_frame_paths - FRAME_PATH_TO_ROW.keys()
if _missing_in_hnsw:
    logger.warning(
        "%d frame_path(s) referenced by FLATIP_DANGVANTUAN events are missing from "
        "HNSW_JINACLIPV2 FRAME_PATH_TO_ROW (design assumption 'HNSW covers FLATIP' violated). "
        "Example paths: %s",
        len(_missing_in_hnsw), list(_missing_in_hnsw)[:5],
    )