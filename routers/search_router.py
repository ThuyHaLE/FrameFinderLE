# routers/search_router.py

"""
Search routes (Type 1, 2, 3)

POST /api/search/frame           — Type 1: A specific frame (text-image)
POST /api/search/event-boundary  — Type 2: Start/End of an event
POST /api/search/event-mention   — Type 3: Not implemented yet (missing model +
                                    transcript index, see TODO below)
"""

import state
import model_state
from fastapi import APIRouter, Depends, HTTPException, Query
import math
from common import NOT_IMPLEMENTED
from deps import get_device, get_model, get_clipv0_index, get_clipv0_image_info_dict, get_video_index
from schemas import SearchRequest
from tools.search_utils import search_batch
from tools.search_similar import search_similar
from utils import paginate

router = APIRouter(prefix="/api/search", tags=["search"])


def _to_response(paged: dict) -> dict:
    """Change key names from paginate() to the shape expected by SearchContext.jsx."""
    return {
        "results": paged["items"],
        "totalImages": paged["total"],
        "totalPages": paged["totalPages"],
        "page": paged["page"],
    }


def _video_ranking_score(frame_info: list, k_nums: int, higher_is_better: bool = False) -> float:
    """Calculate a ranking score for a video based on the positions and scores of its frames in the original FAISS results list.
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
    Results (already enriched, in FAISS order: best match first) are grouped by video_ID,
    a ranking_score is calculated for each video, and videos are sorted with the best first.
    Then the results are flattened back into a list of frames (same shape as sort_by_frame_index / sort_by_score), 
    so the frontend doesn't need to know what displayOption is.
    Each frame is tagged with 'video_ranking_score' (the score of the video it belongs to).
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
    """Map video_ID (original name) -> video_id (name needed by GalleryItem.jsx)."""
    r = dict(r)
    r.setdefault('video_id', r.get('video_ID'))
    return r


def _sort_results(results: list, display_option: str) -> list:
    """
    Apply displayOption to the list of results (already enriched via search_batch(), 
    in original FAISS order — best match first by increasing distance).
    All branches return a flat list[dict] with the same shape 
    (each element is a frame with video_ID/frame_ID/frame_idx/frame_path/timestamp/time_in_seconds/distance/db_idx/thumbnail)
    — group_by_videoid only changes the ORDER, not the shape, so the frontend (GalleryItem.jsx) doesn't need to change anything.
        - "sort_by_score"       : sort by distance ascending
        - "sort_by_frame_index" : keep the original FAISS order (do not re-sort by frame_idx — this is the correct behavior of the original notebook)
        - "group_by_videoid"    : group by video, best video ranking first, then flatten (see _group_by_video)
    """
    if display_option == "sort_by_score":
        return sorted(results, key=lambda r: r["distance"])
    if display_option == "group_by_videoid":
        return _group_by_video(results, higher_is_better=False)
    # "sort_by_frame_index" and all other values: keep the original FAISS order
    return results


@router.post("/frame")
def search_frame(
    req: SearchRequest,
    device=Depends(get_device),
    model=Depends(get_model),
    clipv0_index=Depends(get_clipv0_index),
    image_info_dict: dict = Depends(get_clipv0_image_info_dict),
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
    Group start_results + end_results by video_ID:
      1. video_ID only appears < min_occurrences times in the entire pool (start+end)
         → discard, not enough to identify a real segment.
      2. Remaining video_IDs → use MIN/MAX frame_idx as start-end boundaries.
      3. Retrieve ALL real frames within the [min, max] range from video_index (already normalized
         fields: video_id, frame_idx, timestamp_sec, db_idx, thumbnail).
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
            continue  # match single 1 time — not enough to identify a segment

        start_item = min(items, key=lambda r: r["frame_idx"])
        end_item = max(items, key=lambda r: r["frame_idx"])
        if start_item["frame_idx"] == end_item["frame_idx"]:
            continue  # min == max, not enough to create a real segment

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
            "frames": frames_in_range,   # already have thumbnail/db_idx/frame_idx/timestamp_sec
        })

    clusters.sort(key=lambda c: c["score"])
    return clusters


@router.post("/event-boundary")
def search_event_boundary(
    req: SearchRequest,
    device=Depends(get_device),
    model=Depends(get_model),
    clipv0_index=Depends(get_clipv0_index),
    image_info_dict: dict = Depends(get_clipv0_image_info_dict),
    video_index: dict = Depends(get_video_index),
):
    """Type 2 — Event boundaries. Return frame clusters by video (not individual pairs)."""
    start_results, end_results = search_batch(
        [req.start_query or "", req.end_query or ""],
        k=req.k,
        index=clipv0_index,
        device=device,
        image_info_dict=image_info_dict,
    )

    clusters = _cluster_by_video(start_results, end_results, video_index)

    # displayOption is ignored here because the frontend is hard-coded to "sort_by_frame_index" for Type 2 
    # — no need to handle displayOption here anymore: 
    # clusters are already sorted by score (best match first), 
    # and frames WITHIN each cluster are sorted by frame_idx.
    return _to_response(paginate(clusters, req.page, req.imagesPerPage))

@router.get("/similar/{db_idx}")
def get_similar_frames(
    db_idx: int,
    top_k: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """
    Return top-k frames similar to the frame with `db_idx`, based on pre-encoded embeddings.
    Do NOT re-encode the image at request time.
    """
    query_frame = state.FRAME_BY_ID.get(db_idx)
    if query_frame is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy frame db_idx={db_idx}")

    row_idx = model_state.FRAME_PATH_TO_ROW.get(query_frame["frame_path"])
    if row_idx is None:
        raise HTTPException(
            status_code=500,
            detail=f"Frame db_idx={db_idx} chưa có trong index embedding (lệch dữ liệu)",
        )

    query_encoding = model_state.ENCODED_FRAMES[row_idx]

    # Get the top_k most similar frames (excluding itself with cosine similarity = 1) and paginate the results.
    k = min(top_k + 1, model_state.ENCODED_FRAMES.shape[0])
    scores, indices = search_similar(query_encoding, top_k=k)

    items = []
    for score, idx in zip(scores, indices):
        if idx == row_idx:
            continue  # pass the query frame itself
        frame_path = model_state.CLIPV0_IMAGE_INFO_DICT[str(idx)]["frame_path"]
        frame = state.FRAME_BY_PATH.get(frame_path)
        if frame is None:
            continue  # prevent data skew, skip instead of crashing the entire request
        items.append({**frame, "similarity": round(float(score), 4)})
        if len(items) >= top_k:
            break

    paged = paginate(items, page, per_page)

    return {
        "queryFrame": query_frame,
        "items": paged["items"],
        "total": paged["total"],
        "totalPages": paged["totalPages"],
        "page": paged["page"],
    }

@router.post("/event-mention")
def search_event_mention(req: SearchRequest):
    """
    Type 3 — Event mention. Search for events mentioned in the transcript.
    NOT IMPLEMENTED: Missing (1) dedicated Vietnamese text-text embedding model
    (current model_state only loads 1 text-image model), and (2) transcript
    index (no place to build/load yet). Need to add these infrastructure components
    before implementing the actual logic here.
    """
    raise NOT_IMPLEMENTED