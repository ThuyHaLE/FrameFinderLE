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


def get_frame_by_id():
    return state.FRAME_BY_ID


def get_frame_by_path():
    return state.FRAME_BY_PATH


def get_all_events():
    return model_state.ALL_EVENTS


def get_event_index():
    return model_state.EVENT_INDEX


# ---------------------------------------------------------------------------
# Model & search index (model_state.py)
# ---------------------------------------------------------------------------

def get_device():
    return model_state.DEVICE


def get_jinaclipv2_model():
    return model_state.JINACLIPV2_MODEL


def get_dangvantuan_model():
    return model_state.DANGVANTUAN_MODEL


def get_jinaclipv2_encoded_frames():
    return model_state.JINACLIPV2_ENCODED_FRAMES


def get_hnsw_jinaclipv2_index():
    return model_state.HNSW_JINACLIPV2.index


def get_hnsw_jinaclipv2_info_dict():
    return model_state.HNSW_JINACLIPV2.info_dict


def get_flatip_dangvantuan_index():
    return model_state.FLATIP_DANGVANTUAN.index


def get_flatip_dangvantuan_info_dict():
    return model_state.FLATIP_DANGVANTUAN.info_dict


def get_frame_path_to_row():
    return model_state.FRAME_PATH_TO_ROW


def get_bm25_flatip_dangvantuan_index():
    return model_state.FLATIP_DANGVANTUAN.index


def get_bm25_flatip_dangvantuan_info_dict():
    return model_state.FLATIP_DANGVANTUAN.info_dict


def get_bm25():
    return model_state.BM25

def get_bm25_chunks():
    return model_state.BM25_CHUNKS