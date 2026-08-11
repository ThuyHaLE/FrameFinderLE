"""
routers/data_router.py — Data Browser routes
====================================================================
Chứa:
    GET /api/data              — browse keyframes theo video_ID / timestamp
    GET /api/videos/l-options  — danh sách "L" cho dropdown (cùng nhóm data)

State (all_frames, video_index, l_options) được lấy qua Depends() từ
deps.py — router KHÔNG import trực tiếp `app` để tránh circular import.
"""

from typing import Dict, List

from fastapi import APIRouter, Depends

from deps import get_all_frames, get_l_options, get_video_index
from utils import paginate, parse_timestamp

router = APIRouter(prefix="/api", tags=["data"])


@router.get("/videos/l-options")
def get_l_options_route(l_options: List[str] = Depends(get_l_options)):
    """Trả danh sách giá trị L (VD: ["01","02",...]) có thật trong dataset hiện tại."""
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
    """Browse keyframes theo video_ID / khoảng timestamp."""

    # thumbnail đã được build sẵn lúc load — không cần transform lại

    # Lấy pool theo video_ID
    # - Không filter         → toàn bộ 200k frames
    # - Exact "L13_V001"     → O(1) lookup từ video_index
    # - Prefix "L13"         → gộp tất cả V của L đó (O(số video trong L))
    if not video_ID:
        items = all_frames
    elif "_V" in video_ID:
        # Exact match: "L13_V001"
        items = list(video_index.get(video_ID, []))
    else:
        # Prefix match: "L13" → lấy tất cả key bắt đầu bằng "L13_"
        prefix = f"{video_ID}_"
        items = []
        for vid_key, frames in video_index.items():
            if vid_key.startswith(prefix):
                items.extend(frames)
        # Sort theo video_id rồi timestamp_sec để kết quả có thứ tự nhất quán
        items.sort(key=lambda r: (r["video_id"], r["timestamp_sec"]))

    # Filter / sort theo timestamp (chỉ apply khi có video_ID để tránh sort 200k)
    # Dùng timestamp_sec (pre-computed float) thay vì parse string mỗi lần
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
            # Chỉ có start → sort theo frame gần nhất từ thời điểm đó
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