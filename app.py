"""
app.py — SceneSeek Backend
===========================
Toàn bộ route đã được tách vào routers/*.py, mỗi route trả 501 khi
chưa implement. Client (client.js) sẽ catch 501 và tự fallback về
mock data ở frontend.

Để "activate" một route:
1. Mở router tương ứng trong routers/, implement logic thật.
2. Xoá dòng `raise NOT_IMPLEMENTED`.
3. Client sẽ tự nhận ra HTTP 200 và dùng data thật — không cần đổi gì ở frontend.

Chạy:
    pip install fastapi uvicorn pydantic
    uvicorn app:app --reload --port 8000
"""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import state  # noqa: F401  import để trigger load dataset 1 lần lúc startup
import model_state  # noqa: F401  import để trigger load model + FAISS index 1 lần lúc startup

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
# Routers
# ---------------------------------------------------------------------------
# Dataset (state.ALL_FRAMES, state.VIDEO_INDEX, state.L_OPTIONS,
# state.FEEDBACK_STORE) và model/search index (model_state.DEVICE,
# model_state.MODEL, model_state.ENCODED_FRAMES, model_state.CLIPV0_HNSW,
# model_state.IMAGE_INFO_DICT) đã được load & cache 1 lần khi import
# state / model_state ở trên chạy — mỗi router lấy qua deps.py,
# KHÔNG dùng app.state nữa.

from routers.data_router import router as data_router
from routers.search_router import router as search_router
from routers.refine_router import router as refine_router
from routers.feedback_router import router as feedback_router
from routers.query_router import router as query_router

app.include_router(data_router)
app.include_router(search_router)
app.include_router(refine_router)
app.include_router(feedback_router)
app.include_router(query_router)

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