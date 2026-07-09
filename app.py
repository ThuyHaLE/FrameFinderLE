"""
app.py — SceneSeek Backend
===========================
Pattern: mỗi route trả 501 khi chưa implement.
Client (client.js) sẽ catch 501 và tự fallback về mock data ở frontend.

Để "activate" một route:
1. Implement logic thật bên trong hàm đó.
2. Xoá dòng `raise NOT_IMPLEMENTED`.
3. Client sẽ tự nhận ra HTTP 200 và dùng data thật — không cần đổi gì ở frontend.

Chạy:
    pip install fastapi uvicorn pydantic
    uvicorn app:app --reload --port 8000
"""

import math
import os
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="SceneSeek API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # thu hẹp lại khi deploy production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Shared exception — dùng cho mọi route chưa implement
# ---------------------------------------------------------------------------

NOT_IMPLEMENTED = HTTPException(
    status_code=501,
    detail="Route chưa được implement. Frontend sẽ tự fallback về mock data.",
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_timestamp(ts: str) -> float:
    """
    Parse timestamp string → seconds (float).
    Accepts:
        '0:00:08.300000'   annotation format
        '00:08:30'         hh:mm:ss (paste từ video player)
        '00:08:30.500'     hh:mm:ss.SSS
        '0:08'             hh:mm (không có giây)
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


# ---------------------------------------------------------------------------
# App state — load model/database ở đây khi sẵn sàng
# ---------------------------------------------------------------------------

# TODO: load jina-clip-v2 encoder
# TODO: load FAISS index (text-image channel)
# TODO: load Vietnamese text-embedding model (text-text channel)
# TODO: load keyword graph
# TODO: load encoded frames (cho feedback refine)

import json

# Load annotation (~200k items) một lần lúc startup
_ANNOTATION_PATH = os.path.join(
    os.getcwd(), "static", "images", "key_frame_folder_reduced",
    "combined_keyframe_annotation.json"
)
with open(_ANNOTATION_PATH, encoding="utf-8") as _f:
    _raw = json.load(_f)

# Flatten thành list với db_idx, build thumbnail URL ngay lúc load
# để tránh transform 200k items mỗi request
_ALL_FRAMES: List[dict] = []
for _k, _v in _raw.items():
    _ALL_FRAMES.append({
        "db_idx": int(_k),
        **_v,
        "thumbnail": build_thumbnail_url(_v["frame_path"]),
    })

# Index theo video_ID để filter O(1) thay vì O(n) linear scan
_VIDEO_INDEX: Dict[str, List[dict]] = {}
for _item in _ALL_FRAMES:
    _VIDEO_INDEX.setdefault(_item["video_ID"], []).append(_item)

app.state.all_frames   = _ALL_FRAMES    # toàn bộ 200k frames
app.state.video_index  = _VIDEO_INDEX   # { video_ID: [frame, ...] }

app.state.FEEDBACK_STORE: Dict[str, Any] = {}

# ---------------------------------------------------------------------------
# Static files — keyframe images
# ---------------------------------------------------------------------------

KEYFRAME_DIR = os.path.join(os.getcwd(), "static", "images", "key_frame_folder_reduced")
if os.path.isdir(KEYFRAME_DIR):
    app.mount(
        "/static/images/key_frame_folder_reduced",
        StaticFiles(directory=KEYFRAME_DIR),
        name="key_frame_folder_reduced",
    )

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    # Type 1 & 3
    query: Optional[str] = None
    # Type 2
    start_query: Optional[str] = None
    end_query: Optional[str] = None
    # Options
    keywords: List[str] = []
    k: int = 100
    displayOption: str = "sort_by_frame_index"
    page: int = 1
    imagesPerPage: int = 50
    sessionId: Optional[str] = None


class FeedbackRequest(BaseModel):
    db_idx: int
    action: str        # 'like' | 'dislike' | None
    session_id: str


class ProcessQueryRequest(BaseModel):
    query_text: str


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Search routes
# ---------------------------------------------------------------------------

@app.post("/api/search/frame")
def search_frame(req: SearchRequest):
    """
    Type 1 — Cảnh cụ thể.
    Channel: text-image (query ↔ fused frame embedding).
    """
    # TODO:
    # 1. encode req.query + req.keywords bằng jina-clip-v2 text tower
    # 2. search FAISS index (text-image channel), lấy top req.k
    # 3. apply display_option (sort / group)
    # 4. paginate và trả về
    raise NOT_IMPLEMENTED


@app.post("/api/search/event-boundary")
def search_event_boundary(req: SearchRequest):
    """
    Type 2 — Sự kiện cảnh đầu/cuối.
    Channel: text-image × 2 (start_query + end_query), pair by timestamp.
    """
    # TODO:
    # 1. encode req.start_query và req.end_query riêng biệt
    # 2. search FAISS 2 lần → top-K start frames, top-K end frames
    # 3. ghép cặp (start_frame, end_frame) theo ràng buộc ts_start < ts_end
    # 4. score cặp, paginate, trả về
    raise NOT_IMPLEMENTED


@app.post("/api/search/event-mention")
def search_event_mention(req: SearchRequest):
    """
    Type 3 — Sự kiện được đề cập trong transcript.
    Primary channel: text-text (query ↔ transcript segments).
    Secondary: text-image để re-rank (optional).
    """
    # TODO:
    # 1. encode req.query bằng Vietnamese text-embedding model
    # 2. search transcript index (text-text channel)
    # 3. (optional) re-rank top results bằng text-image score
    # 4. paginate, trả về
    raise NOT_IMPLEMENTED


# ---------------------------------------------------------------------------
# Refine routes
# ---------------------------------------------------------------------------

@app.post("/api/search/frame/refine")
def refine_frame(req: SearchRequest):
    """Refine Type 1 dựa trên feedback (immediate + aggregated)."""
    # TODO:
    # 1. đọc feedback từ app.state.FEEDBACK_STORE[req.sessionId]
    # 2. chạy immediate_refining hoặc aggregated_refining
    # 3. paginate, trả về
    raise NOT_IMPLEMENTED


@app.post("/api/search/event-boundary/refine")
def refine_event_boundary(req: SearchRequest):
    raise NOT_IMPLEMENTED


@app.post("/api/search/event-mention/refine")
def refine_event_mention(req: SearchRequest):
    raise NOT_IMPLEMENTED


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

@app.post("/api/update_feedback")
def update_feedback(req: FeedbackRequest):
    """
    Lưu like/dislike vào FEEDBACK_STORE.
    Route này đơn giản — implement sớm nhất vì không cần model/DB.
    """
    # TODO (optional): persist sang DB thật thay vì in-memory
    session = app.state.FEEDBACK_STORE.setdefault(req.session_id, {})
    session[req.db_idx] = req.action
    return {"feedbackStatus": req.action, "dbIdx": req.db_idx}


# ---------------------------------------------------------------------------
# Keyword graph suggestions
# ---------------------------------------------------------------------------

@app.post("/api/process_query")
def process_query(req: ProcessQueryRequest):
    """
    Trả keyword gợi ý từ keyword graph.
    """
    # TODO:
    # 1. word-segment req.query_text bằng underthesea/pyvi
    # 2. chuẩn hoá Unicode NFC
    # 3. graph expansion → trả top keywords
    raise NOT_IMPLEMENTED


# ---------------------------------------------------------------------------
# Data browser
# ---------------------------------------------------------------------------

@app.get("/api/data")
def get_data(
    page: int = 1,
    perPage: int = 50,
    video_ID: str = "",
    timestamp: str = "",        # start time
    timestamp_end: str = "",    # end time (optional)
):
    """Browse keyframes theo video_ID / khoảng timestamp."""
    video_index = app.state.video_index
    all_frames  = app.state.all_frames

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
        # Sort theo video_ID rồi timestamp để kết quả có thứ tự nhất quán
        items.sort(key=lambda r: (r["video_ID"], r["timestamp"]))

    # Filter / sort theo timestamp (chỉ apply khi có video_ID để tránh sort 200k)
    if timestamp and video_ID:
        start_sec = parse_timestamp(timestamp)
        if timestamp_end:
            end_sec = parse_timestamp(timestamp_end)
            items = [
                r for r in items
                if start_sec <= parse_timestamp(r["timestamp"]) <= end_sec
            ]
            items = sorted(items, key=lambda r: parse_timestamp(r["timestamp"]))
        else:
            # Chỉ có start → sort theo frame gần nhất từ thời điểm đó
            items = sorted(
                items,
                key=lambda r: abs(parse_timestamp(r["timestamp"]) - start_sec),
            )

    paged = paginate(items, page, perPage)
    return {
        "keyframes": paged["items"],
        "total": paged["total"],
        "totalPages": paged["totalPages"],
    }


# ---------------------------------------------------------------------------
# Serve React production build
# (comment out khi đang dev với 2 server riêng — Vite + FastAPI)
# Uncomment sau khi chạy `npm run build` và muốn deploy 1 server duy nhất.
# ---------------------------------------------------------------------------

dist_dir = os.path.join(os.path.dirname(__file__), "sceneseek-frontend", "dist")
if os.path.isdir(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")
    
@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    return FileResponse(os.path.join(dist_dir, "index.html"))

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)