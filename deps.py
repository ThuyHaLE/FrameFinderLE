# deps.py

"""
Dependency helpers for routers to get state via Depends(...).

State is actually loaded once in state.py (dataset) and 
model_state.py (model + search index) when those modules are imported (module-level cache, not re-run on each request).

Here we just expose them as Depends() so that:
  - Routers don't need to `import state` / `import model_state` directly
    (easier to mock in tests: override_dependency in test instead of
    monkeypatching the module).
  - If we later change the source of state (e.g., from module to Redis/DB, 
    or change the index to a separate service), we only need to change it here, routers don't change.

Usage in router:
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


def get_clipv0_image_info_dict():
    return model_state.CLIPV0_IMAGE_INFO_DICT
