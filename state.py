"""
state.py — Load & cache dataset một lần lúc process khởi động.
====================================================================
Code ở top-level chỉ chạy 1 LẦN khi module được import lần đầu
(Python cache module trong sys.modules) — dù được import từ
app.py, deps.py, hay bất kỳ router nào, JSON vẫn chỉ load 1 lần
trong 1 process.

Lưu ý: nếu chạy nhiều worker (uvicorn --workers N / gunicorn),
mỗi worker là 1 process riêng → mỗi worker sẽ load JSON riêng,
không share RAM giữa các worker (điều này không liên quan tới
việc tách file, bản gốc gộp trong app.py cũng vậy).
"""

import json
import os
import re
from typing import Any, Dict, List

from utils import build_thumbnail_url, parse_timestamp

# ---------------------------------------------------------------------------
# Load annotation (~200k items) — chạy 1 lần khi module được import
# ---------------------------------------------------------------------------

_ANNOTATION_PATH = os.path.join(
    os.getcwd(), "static", "images", "key_frame_folder_reduced",
    "combined_keyframe_annotation.json"
)
with open(_ANNOTATION_PATH, encoding="utf-8") as _f:
    _raw = json.load(_f)

# Flatten thành list với db_idx, normalize field names, pre-compute
# timestamp_sec và thumbnail URL ngay lúc load → tránh transform lặp
# lại mỗi request.
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

# Index theo video_id để filter O(1)
VIDEO_INDEX: Dict[str, List[dict]] = {}
for _item in ALL_FRAMES:
    VIDEO_INDEX.setdefault(_item["video_id"], []).append(_item)

# Danh sách "L" (VD: "01", "21"...) lấy trực tiếp từ video_ID có trong data
_L_PREFIX_RE = re.compile(r"^L(\d+)_V")
_l_set = set()
for _vid in VIDEO_INDEX.keys():
    _m = _L_PREFIX_RE.match(_vid)
    if _m:
        _l_set.add(_m.group(1).zfill(2))
L_OPTIONS: List[str] = sorted(_l_set, key=lambda s: int(s))

# In-memory feedback store (mất khi restart — đã note TODO ở app.py:
# persist sang DB thật khi cần).
FEEDBACK_STORE: Dict[str, Any] = {}
