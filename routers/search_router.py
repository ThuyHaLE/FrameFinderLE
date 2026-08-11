"""
routers/search_router.py — Search routes (Type 1, 2, 3)
====================================================================
POST /api/search/frame           — Type 1: Cảnh cụ thể (text-image)
POST /api/search/event-boundary  — Type 2: Sự kiện đầu/cuối (text-image x2)
POST /api/search/event-mention   — Type 3: chưa implement (thiếu model +
                                    transcript index, xem TODO ở dưới)
"""

from fastapi import APIRouter, Depends
import math
from common import NOT_IMPLEMENTED
from deps import get_device, get_model, get_clipv0_index, get_image_info_dict, get_video_index
from schemas import SearchRequest
from tools.search_utils import search_batch
from utils import paginate

router = APIRouter(prefix="/api/search", tags=["search"])


def _to_response(paged: dict) -> dict:
    """Đổi tên key từ paginate() sang shape mà SearchContext.jsx mong đợi."""
    return {
        "results": paged["items"],
        "totalImages": paged["total"],
        "totalPages": paged["totalPages"],
        "page": paged["page"],
    }


def _video_ranking_score(frame_info: list, k_nums: int, higher_is_better: bool = False) -> float:
    """
    Tính ranking score cho 1 video dựa trên vị trí (position, 1-based) và
    score (distance) của các frame thuộc video đó trong list kết quả FAISS gốc.
    Port từ notebook: calculate_video_ranking_score().
    """
    if not frame_info:
        return float('-inf') if higher_is_better else float('inf')
    n = len(frame_info)
    sum_part = sum(
        ((k_nums - info['position']) / k_nums) * info['score']
        for info in frame_info
    )
    avg_score = sum_part / n
    log_factor = math.log2(n + 1) if higher_is_better else 1 / math.log2(n + 1)
    final_score = avg_score * log_factor
    return final_score if higher_is_better else -final_score


def _group_by_video(results: list, higher_is_better: bool = False) -> list:
    """
    Nhóm results (đã enrich, đã ở thứ tự FAISS: khớp nhất trước) theo video_ID,
    tính ranking_score cho từng video, xếp video tốt nhất lên trước — rồi
    TRẢI PHẲNG lại thành list frame (cùng shape với sort_by_frame_index /
    sort_by_score), để frontend không cần biết displayOption là gì.
    Mỗi frame được gắn thêm 'video_ranking_score' (điểm của video chứa nó).
    """
    k_nums = len(results)
    grouped = {}
    for position, r in enumerate(results, start=1):
        grouped.setdefault(r['video_ID'], []).append((position, r))

    video_scores = []
    for video_ID, items in grouped.items():
        frame_info = [{'position': pos, 'score': r['distance']} for pos, r in items]
        score = _video_ranking_score(frame_info, k_nums, higher_is_better)
        video_scores.append((score, items))

    video_scores.sort(key=lambda v: v[0], reverse=higher_is_better)

    flat = []
    for score, items in video_scores:
        for _position, r in items:
            r = dict(r)
            r['video_ranking_score'] = score
            flat.append(r)
    return flat

def _normalize_frame(r: dict) -> dict:
    """Map video_ID (tên gốc) -> video_id (tên GalleryItem.jsx cần)."""
    r = dict(r)
    r.setdefault('video_id', r.get('video_ID'))
    return r


def _sort_results(results: list, display_option: str) -> list:
    """
    Áp displayOption lên list kết quả (đã enrich qua search_batch(), đã ở
    thứ tự FAISS gốc — tức khớp nhất trước theo distance tăng dần).
    Tất cả nhánh đều trả list[dict] PHẲNG cùng shape (mỗi phần tử 1 frame,
    có video_ID/frame_ID/frame_idx/frame_path/timestamp/time_in_seconds/
    distance/db_idx/thumbnail) — group_by_videoid chỉ đổi THỨ TỰ, không đổi
    shape, nên frontend (GalleryItem.jsx) không cần sửa gì.

      - "sort_by_score"       : sort lại theo distance tăng dần
      - "sort_by_frame_index" : giữ nguyên thứ tự FAISS trả về (không re-sort
                                 theo frame_idx — đúng behavior notebook gốc)
      - "group_by_videoid"    : nhóm theo video, video ranking tốt nhất lên
                                 trước, rồi trải phẳng lại (xem _group_by_video)
    """
    if display_option == "sort_by_score":
        return sorted(results, key=lambda r: r["distance"])
    if display_option == "group_by_videoid":
        return _group_by_video(results, higher_is_better=False)
    # "sort_by_frame_index" và mọi giá trị khác: giữ nguyên thứ tự FAISS gốc
    return results


@router.post("/frame")
def search_frame(
    req: SearchRequest,
    device=Depends(get_device),
    model=Depends(get_model),
    clipv0_index=Depends(get_clipv0_index),
    image_info_dict: dict = Depends(get_image_info_dict),
):
    full_query = req.query or ""
    if req.keywords:
        full_query = f"{full_query} {' '.join(req.keywords)}".strip()

    results = search_batch([full_query], k=req.k, index=clipv0_index, device=device, image_info_dict=image_info_dict)[0]
    results = [_normalize_frame(r) for r in results]
    results = _sort_results(results, req.displayOption)
    return _to_response(paginate(results, req.page, req.imagesPerPage))


def _cluster_by_video(start_results: list, end_results: list, video_index: dict, min_occurrences: int = 2) -> list:
    """
    Gộp start_results + end_results theo video_ID:
      1. video_ID chỉ xuất hiện < min_occurrences lần trong toàn bộ pool (start+end)
         → bỏ, không đủ để xác định 1 đoạn thật.
      2. video_ID còn lại → lấy frame_idx MIN/MAX làm biên start-end.
      3. Lấy TOÀN BỘ frame thật trong khoảng [min, max] từ video_index (đã chuẩn
         hoá field: video_id, frame_idx, timestamp_sec, db_idx, thumbnail).
      4. Score cụm = best_start_distance + best_end_distance (nếu có đủ cả 2 channel),
         dùng để sort cụm nào khớp truy vấn tốt nhất lên đầu.
    """
    pool = (
        [dict(r, _channel="start") for r in start_results]
        + [dict(r, _channel="end") for r in end_results]
    )

    by_video = {}
    for r in pool:
        by_video.setdefault(r["video_ID"], []).append(r)

    clusters = []
    for video_ID, items in by_video.items():
        if len(items) < min_occurrences:
            continue  # match lẻ 1 lần — không đủ xác định đoạn

        start_item = min(items, key=lambda r: r["frame_idx"])
        end_item = max(items, key=lambda r: r["frame_idx"])
        if start_item["frame_idx"] == end_item["frame_idx"]:
            continue  # min == max, không tạo được đoạn thật

        video_frames = video_index.get(video_ID, [])
        frames_in_range = sorted(
            (f for f in video_frames
             if start_item["frame_idx"] <= f["frame_idx"] <= end_item["frame_idx"]),
            key=lambda f: f["frame_idx"],
        )
        if not frames_in_range:
            continue

        start_scores = [r["distance"] for r in items if r["_channel"] == "start"]
        end_scores = [r["distance"] for r in items if r["_channel"] == "end"]
        score = (min(start_scores) if start_scores else 0) + (min(end_scores) if end_scores else 0)

        clusters.append({
            "video_id": video_ID,
            "score": score,
            "frame_count": len(frames_in_range),
            "frames": frames_in_range,   # đã có sẵn thumbnail/db_idx/frame_idx/timestamp_sec
        })

    clusters.sort(key=lambda c: c["score"])
    return clusters


@router.post("/event-boundary")
def search_event_boundary(
    req: SearchRequest,
    device=Depends(get_device),
    model=Depends(get_model),
    clipv0_index=Depends(get_clipv0_index),
    image_info_dict: dict = Depends(get_image_info_dict),
    video_index: dict = Depends(get_video_index),
):
    """Type 2 — Sự kiện đầu/cuối. Trả về CỤM frame theo video (không phải cặp rời)."""
    start_results, end_results = search_batch(
        [req.start_query or "", req.end_query or ""],
        k=req.k,
        index=clipv0_index,
        device=device,
        image_info_dict=image_info_dict,
    )

    clusters = _cluster_by_video(start_results, end_results, video_index)

    # displayOption bị khoá cứng ở frontend thành "sort_by_frame_index" cho
    # Type 2 — không cần xử lý displayOption ở đây nữa: cụm đã sort theo
    # score (best match trước), frame TRONG cụm đã sort theo frame_idx.
    return _to_response(paginate(clusters, req.page, req.imagesPerPage))


@router.post("/event-mention")
def search_event_mention(req: SearchRequest):
    """
    Type 3 — Sự kiện được đề cập trong transcript.
    CHƯA IMPLEMENT: thiếu (1) model embedding text-text tiếng Việt riêng
    (model_state hiện chỉ load 1 model text-image), và (2) transcript
    index (chưa có nơi nào build/load). Cần bổ sung 2 phần hạ tầng này
    trước khi viết logic thật ở đây.
    """
    raise NOT_IMPLEMENTED