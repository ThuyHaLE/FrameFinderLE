"""
tools/search_utils.py — Search helpers dùng chung cho search_router.py
====================================================================
Chứa:
    search(...)                 — encode 1 query, search FAISS, trả top-k
    search_batch(...)           — encode nhiều query cùng lúc (hiệu quả hơn)
    pair_boundary_results(...)  — ghép cặp (start, end) cho Type 2

Thiết kế: các hàm nhận index/device/image_info_dict như PARAMETER
(default lấy từ model_state nếu không truyền), để:
  - Router gọi bằng giá trị lấy từ Depends() — giữ đúng pattern DI
    mà deps.py đã xây (dễ mock khi test).
  - Notebook / script độc lập vẫn gọi được bình thường, không cần
    đổi gì (không truyền gì thì tự lấy từ model_state).

Lưu ý về field name: IMAGE_INFO_DICT dùng tên GỐC từ JSON annotation
(video_ID, time_in_seconds, frame_ID...), KHÔNG giống tên đã chuẩn
hoá trong state.ALL_FRAMES (video_id, timestamp_sec, db_idx...).
Mọi so sánh/join trong file này phải dùng tên gốc.
"""

from typing import List, Optional
import model_state
from tools.faiss_retrieval import k_image_search
from tools.query_encoding import encode_texts
from utils import build_thumbnail_url

# Lookup frame_path -> db_idx, build 1 lần khi module được import.
# Dùng để nối kết quả FAISS (không có db_idx) về state.ALL_FRAMES
# (có db_idx, dùng cho feedback/like-dislike).
#
# QUAN TRỌNG: chỉ dùng lookup này nếu đã xác nhận frame_ID trong
# IMAGE_INFO_DICT KHÔNG trùng với db_idx trong state.ALL_FRAMES.
# Nếu trùng, có thể bỏ bước join này và dùng trực tiếp info["frame_ID"].
try:
    import state
    _FRAME_PATH_TO_DB_IDX = {
        item["frame_path"]: item["db_idx"] for item in state.ALL_FRAMES
    }
except Exception:
    # Cho phép file này chạy độc lập trong notebook không có state.py
    _FRAME_PATH_TO_DB_IDX = {}


def _enrich(info: dict, dist: float, idx: int) -> dict:
    """Gắn thêm faiss_idx, distance, db_idx, thumbnail vào 1 record kết quả."""
    info = dict(info)
    info["faiss_idx"] = int(idx)
    info["distance"] = float(dist)
    info["db_idx"] = _FRAME_PATH_TO_DB_IDX.get(info.get("frame_path"))
    info["thumbnail"] = build_thumbnail_url(info["frame_path"])
    return info


def search_batch(
    queries: List[str],
    k: int = 5,
    truncate_dim: Optional[int] = None,
    index=None,
    device=None,
    image_info_dict: Optional[dict] = None,
) -> List[List[dict]]:
    """
    Tìm top-k cho nhiều query cùng lúc — hiệu quả hơn gọi search() lặp lại
    vì encode 1 lần.

    :param queries: list các câu query
    :param k: số kết quả trả về cho MỖI query
    :param truncate_dim: PHẢI khớp với truncate_dim đã dùng khi encode ảnh
    :param index: FAISS/HNSW index; mặc định model_state.CLIPV0_HNSW
    :param device: mặc định model_state.DEVICE
    :param image_info_dict: mặc định model_state.IMAGE_INFO_DICT
    :return: list[list[dict]] — 1 list kết quả cho mỗi query, theo đúng thứ tự input
    """
    index = index if index is not None else model_state.CLIPV0_HNSW
    device = device if device is not None else model_state.DEVICE
    image_info_dict = (
        image_info_dict if image_info_dict is not None else model_state.IMAGE_INFO_DICT
    )

    query_embeddings = encode_texts(queries, truncate_dim=truncate_dim, show_progress=False)

    distances, indices = k_image_search(
        query_vector=query_embeddings,
        index_hnsw=index,
        device=device,
        k_nums=k,
    )

    all_results = []
    for q_dist, q_idx in zip(distances, indices):
        results = []
        for dist, idx in zip(q_dist, q_idx):
            if idx == -1:
                continue
            info = image_info_dict[str(idx)]
            results.append(_enrich(info, dist, idx))
        all_results.append(results)
    return all_results


def search(
    query: str,
    k: int = 5,
    truncate_dim: Optional[int] = None,
    index=None,
    device=None,
    image_info_dict: Optional[dict] = None,
) -> List[dict]:
    """Tìm top-k keyframe khớp nhất với 1 câu query. Wrapper của search_batch()."""
    return search_batch(
        [query], k=k, truncate_dim=truncate_dim,
        index=index, device=device, image_info_dict=image_info_dict,
    )[0]