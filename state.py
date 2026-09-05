# state.py

"""
Load & cache dataset once at process startup.

Code at top-level runs ONCE when the module is first imported
(Python caches the module in sys.modules) — whether imported from
app.py, deps.py, or any router, the JSON is only loaded once per process.

Note: if running multiple workers (uvicorn --workers N / gunicorn),
      each worker is a separate process → each worker will load its own JSON,
      RAM is not shared between workers (this is unrelated to file separation,
      the original combined app.py would behave the same way).
"""

import json
import os
import re
from typing import Any, Dict, List

from utils import build_thumbnail_url, parse_timestamp

# ---------------------------------------------------------------------------
# Load annotation (~200k items) — run once when module is imported
# ---------------------------------------------------------------------------

_ANNOTATION_PATH = os.path.join(
    os.getcwd(), "static", "images", "key_frame_folder_reduced",
    "combined_keyframe_annotation.json"
)
with open(_ANNOTATION_PATH, encoding="utf-8") as _f:
    _raw = json.load(_f)

# Flatten into list with db_idx, normalize field names, pre-compute
# timestamp_sec and thumbnail URL at loading time → avoid transform repeat at each request.
#
# Format JSON:
#   { "frame_ID": int, "frame_idx": int, "frame_path": str,
#     "video_ID": str, "timestamp": str, "time_in_seconds": float }
ALL_FRAMES: List[dict] = []
for _k, _v in _raw.items():
    ALL_FRAMES.append({
        "db_idx":        int(_k),
        "video_id":      _v["video_ID"],
        "frame_id":      _v["frame_ID"],
        "frame_idx":     _v["frame_idx"],
        "frame_path":    _v["frame_path"],
        "timestamp":     _v["timestamp"],
        "thumbnail":     build_thumbnail_url(_v["frame_path"]),
        "timestamp_sec": _v.get("time_in_seconds", parse_timestamp(_v["timestamp"])),
    })

# Lookup O(1) by db_idx / frame_path — use for similar-search
FRAME_BY_ID: Dict[int, dict] = {item["db_idx"]: item for item in ALL_FRAMES}
FRAME_BY_PATH: Dict[str, dict] = {item["frame_path"]: item for item in ALL_FRAMES}

# Index by video_id to filter O(1)
VIDEO_INDEX: Dict[str, List[dict]] = {}
for _item in ALL_FRAMES:
    VIDEO_INDEX.setdefault(_item["video_id"], []).append(_item)

# List of "L" (VD: "01", "21"...) to get directly from video_ID in data
_L_PREFIX_RE = re.compile(r"^L(\d+)_V")
_l_set = set()
for _vid in VIDEO_INDEX.keys():
    _m = _L_PREFIX_RE.match(_vid)
    if _m:
        _l_set.add(_m.group(1).zfill(2))
L_OPTIONS: List[str] = sorted(_l_set, key=lambda s: int(s))

# In-memory feedback store (loss when restart — note TODO in app.py: persist into DB when ready)    
FEEDBACK_STORE: Dict[str, Any] = {}