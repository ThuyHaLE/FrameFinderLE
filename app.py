"""
app.py — Mock backend for SceneSeek frontend
=============================================
Mục đích: chạy frontend mà KHÔNG cần model CLIP, FAISS hay database thật.
Toàn bộ dữ liệu trả về đều là mock data được sinh tự động.

Chạy:
    pip install fastapi uvicorn
    uvicorn app:app --reload --port 8000

Frontend (Vite dev server) cần chạy song song tại port khác (thường 5173).
Nhớ set `API_BASE = "http://localhost:8000"` trong src/api/client.js
và đổi `USE_MOCK = false` để dùng backend này thay vì mock ở frontend.
"""

import math
import random
import time
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title="SceneSeek Mock API", version="0.1.0")

# Cho phép Vite dev server (port 5173) hoặc bất kỳ origin nào gọi API.
# Khi deploy production thì thu hẹp lại.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory stores (thay thế app.state.FEEDBACK_STORE)
# ---------------------------------------------------------------------------

FEEDBACK_STORE: Dict[str, Any] = {}      # { session_id: { db_idx: action } }
TEMP_FEEDBACK_STORE: Dict[str, Any] = {} # tạm thời trước khi commit

# ---------------------------------------------------------------------------
# Mock data helpers
# ---------------------------------------------------------------------------

VIDEO_IDS = [f"L{str(l).zfill(2)}_V{str(v).zfill(3)}" for l in range(1, 4) for v in range(1, 6)]


def make_mock_result(db_idx: int, video_id: Optional[str] = None, score: float = 1.0) -> dict:
    """Tạo một frame result giả."""
    vid = video_id or random.choice(VIDEO_IDS)
    frame_num = db_idx * 24  # giả sử 24fps
    return {
        "db_idx": db_idx,
        "video_id": vid,
        "frame_id": f"F{str(db_idx).zfill(4)}",
        "timestamp": round(frame_num / 24.0, 3),
        # Dùng placehold.co cho thumbnail — không cần ảnh thật
        "thumbnail": f"https://placehold.co/320x180/1a1a2e/ffffff?text={vid}%0AF{db_idx}",
        "description": f"[Mock] Frame {db_idx} từ video {vid}. Mô tả cảnh giả cho mục đích test UI.",
        "score": round(score, 4),
        "feedback": None,
    }


def paginate(items: list, page: int, per_page: int) -> dict:
    total = len(items)
    total_pages = max(1, math.ceil(total / per_page))
    page = max(1, min(page, total_pages))
    start = (page - 1) * per_page
    return {
        "items": items[start : start + per_page],
        "total": total,
        "totalPages": total_pages,
        "page": page,
    }


def mock_search_results(k: int = 100) -> List[dict]:
    """Sinh k kết quả giả, score giảm dần."""
    results = []
    for i in range(k):
        score = max(0.0, 1.0 - i * (1.0 / k))
        results.append(make_mock_result(db_idx=i + 1, score=score))
    return results

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class SearchRequest(BaseModel):
    # Fields chung cho tất cả search type
    query: Optional[str] = None
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
    action: str          # 'like' | 'dislike'
    session_id: str


class ProcessQueryRequest(BaseModel):
    query_text: str


class KeyframeFilterRequest(BaseModel):
    pass  # query params thôi


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "message": "SceneSeek Mock API is running."}


# --- Search endpoints (Type 1, 2, 3) ---------------------------------------

def _handle_search(req: SearchRequest) -> dict:
    """Logic chung cho cả 3 search type."""
    pool = mock_search_results(req.k)

    if req.displayOption == "group_by_videoid":
        # Nhóm theo video_id: sắp xếp stable
        pool.sort(key=lambda r: r["video_id"])

    paged = paginate(pool, req.page, req.imagesPerPage)
    return {
        "results": paged["items"],
        "totalImages": paged["total"],
        "page": paged["page"],
        "totalPages": paged["totalPages"],
    }


@app.post("/api/search/frame")
def search_frame(req: SearchRequest):
    """Type 1 — Cảnh cụ thể (single query)."""
    return _handle_search(req)


@app.post("/api/search/event-boundary")
def search_event_boundary(req: SearchRequest):
    """Type 2 — Sự kiện cảnh đầu/cuối."""
    return _handle_search(req)


@app.post("/api/search/event-mention")
def search_event_mention(req: SearchRequest):
    """Type 3 — Sự kiện được đề cập trong transcript."""
    return _handle_search(req)


# --- Refine endpoints -------------------------------------------------------

@app.post("/api/search/frame/refine")
def refine_frame(req: SearchRequest):
    """Refine Type 1 dựa trên feedback."""
    pool = mock_search_results(req.k)
    random.shuffle(pool)  # giả vờ kết quả thay đổi sau refine
    paged = paginate(pool, req.page, req.imagesPerPage)
    return {
        "results": paged["items"],
        "totalImages": paged["total"],
        "page": paged["page"],
        "totalPages": paged["totalPages"],
    }


@app.post("/api/search/event-boundary/refine")
def refine_event_boundary(req: SearchRequest):
    return refine_frame(req)


@app.post("/api/search/event-mention/refine")
def refine_event_mention(req: SearchRequest):
    return refine_frame(req)


# --- Feedback ---------------------------------------------------------------

@app.post("/api/update_feedback")
def update_feedback(req: FeedbackRequest):
    """Lưu like/dislike vào in-memory store."""
    session = FEEDBACK_STORE.setdefault(req.session_id, {})
    session[req.db_idx] = req.action
    return {"feedbackStatus": req.action, "dbIdx": req.db_idx}


# --- Keyword suggestions ----------------------------------------------------

@app.post("/api/process_query")
def process_query(req: ProcessQueryRequest):
    """
    Trả về danh sách keyword gợi ý từ query text.
    Mock: tách từ và trả về tối đa 5 từ.
    """
    words = req.query_text.lower().split()
    # Loại stop-words đơn giản
    stop = {"một", "và", "của", "ở", "tại", "trước", "sau", "đang", "được"}
    keywords = [w for w in words if w not in stop][:5]
    return {"keywords": keywords}


# --- Data page (browse keyframes by video_id / timestamp) ------------------

@app.get("/api/data")
def get_data(
    page: int = 1,
    video_ID: str = "",
    timestamp: str = "",
    perPage: int = 50,
):
    """Browse keyframes — hỗ trợ filter theo video_id và timestamp."""
    # Tạo pool 200 frame mock
    pool = [make_mock_result(db_idx=i + 1, video_id=None) for i in range(200)]

    if video_ID:
        # Lọc theo video_id (mock: gán cố định để filter cho ra kết quả)
        vid_pool = [make_mock_result(db_idx=i + 1, video_id=video_ID) for i in range(30)]
        pool = vid_pool

    if timestamp and video_ID:
        # Giả sử timestamp lọc frame gần với thời điểm đó
        try:
            parts = timestamp.split(":")
            h, m, s = int(parts[0]), int(parts[1]), float(parts[2]) if len(parts) > 2 else 0
            target_sec = h * 3600 + m * 60 + s
            pool = sorted(pool, key=lambda r: abs(r["timestamp"] - target_sec))
        except Exception:
            pass  # timestamp parse lỗi → bỏ qua filter

    paged = paginate(pool, page, perPage)
    return {
        "keyframes": paged["items"],
        "total": paged["total"],
        "totalPages": paged["totalPages"],
    }


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)