"""
deps.py — Dependency helpers để router lấy state qua Depends(...).
====================================================================
State thật sự được load 1 lần trong state.py (dataset) và
model_state.py (model + search index) lúc các module đó được
import (module-level cache, không phải chạy lại mỗi request).
Ở đây chỉ expose lại dưới dạng Depends() để:
  - Router không cần `import state` / `import model_state` trực tiếp
    (dễ mock khi test: override_dependency trong test thay vì
    monkeypatch module).
  - Nếu sau này đổi nguồn state (VD: từ module sang Redis/DB,
    hoặc đổi index sang service riêng), chỉ cần sửa ở đây, router
    không đổi gì.

Cách dùng trong router:
    from deps import get_all_frames, get_model
    ...
    def route(
        all_frames: list = Depends(get_all_frames),
        model = Depends(get_model),
    ):
        ...
"""

import state
import model_state


# ---------------------------------------------------------------------------
# Dataset (state.py)
# ---------------------------------------------------------------------------

def get_all_frames():
    return state.ALL_FRAMES


def get_video_index():
    return state.VIDEO_INDEX


def get_l_options():
    return state.L_OPTIONS


def get_feedback_store():
    return state.FEEDBACK_STORE


# ---------------------------------------------------------------------------
# Model & search index (model_state.py)
# ---------------------------------------------------------------------------

def get_device():
    return model_state.DEVICE


def get_model():
    return model_state.MODEL


def get_encoded_frames():
    return model_state.ENCODED_FRAMES


def get_clipv0_index():
    return model_state.CLIPV0_HNSW


def get_image_info_dict():
    return model_state.IMAGE_INFO_DICT
