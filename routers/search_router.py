# routers/search_router.py

"""
Search routes (Type 1, 2, 3)

POST /api/search/frame           — Type 1: A specific frame (text-image)
POST /api/search/event-boundary  — Type 2: Start/End of an event
POST /api/search/event-mention   — Type 3: Event mentioned in transcript (text-text)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from common import NOT_IMPLEMENTED
from deps import (
    get_device, get_jinaclipv2_model, get_jinaclipv2_encoded_frames,
    get_hnsw_jinaclipv2_index, get_hnsw_jinaclipv2_info_dict,
    get_flatip_dangvantuan_index, get_flatip_dangvantuan_info_dict,
    get_video_index, get_frame_by_id, get_frame_by_path, get_frame_path_to_row
    )
from schemas import SearchRequest
from tools.search_utils import (
    search_hnsw_jinaclipv2_batch, search_flatip_dangvantuan_batch,
    normalize_frame, sort_results, to_response, cluster_by_video
    )
from tools.search_similar import search_similar
from utils import paginate

router = APIRouter(prefix="/api/search", tags=["search"])

@router.post("/frame")
def search_frame(
    req: SearchRequest,
    device=Depends(get_device),
    model=Depends(get_jinaclipv2_model),
    index=Depends(get_hnsw_jinaclipv2_index),
    info_dict: dict = Depends(get_hnsw_jinaclipv2_info_dict),
):
    full_query = req.query or ""
    if req.keywords:
        full_query = f"{full_query} {' '.join(req.keywords)}".strip()

    results = search_hnsw_jinaclipv2_batch(
        [full_query], k=req.k, index=index, 
        device=device, info_dict=info_dict
        )[0]
    results = [normalize_frame(r) for r in results]
    results = sort_results(results, req.displayOption)
    return to_response(paginate(results, req.page, req.imagesPerPage))


@router.post("/event-boundary")
def search_event_boundary(
    req: SearchRequest,
    device=Depends(get_device),
    model=Depends(get_jinaclipv2_model),
    index=Depends(get_hnsw_jinaclipv2_index),
    info_dict: dict = Depends(get_hnsw_jinaclipv2_info_dict),
    video_index: dict = Depends(get_video_index),
):
    
    """Type 2 — Event boundaries. N ordered keyframe queries (2–5), clustered by video."""
    queries = req.queries or []
    if not (2 <= len(queries) <= 5):
        raise HTTPException(status_code=422, detail="queries phải có từ 2 đến 5 phần tử")

    channel_results = search_hnsw_jinaclipv2_batch(
        [q or "" for q in queries],
        k=req.k,
        index=index,
        device=device,
        info_dict=info_dict,
    )

    clusters = cluster_by_video(channel_results, video_index)

    # displayOption is ignored here because the frontend is hard-coded to "sort_by_frame_index" for Type 2
    # — no need to handle displayOption here anymore:
    # clusters are already sorted by score (best match first),
    # and frames WITHIN each cluster are sorted by frame_idx.
    return to_response(paginate(clusters, req.page, req.imagesPerPage))

@router.get("/similar/{db_idx}")
def get_similar_frames(
    db_idx: int,
    top_k: int = Query(50, ge=1, le=200),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    frame_by_id: dict = Depends(get_frame_by_id),
    frame_by_path: dict = Depends(get_frame_by_path),
    frame_path_to_row: dict = Depends(get_frame_path_to_row),
    jinaclipv2_encoded_frames=Depends(get_jinaclipv2_encoded_frames),
    info_dict: dict = Depends(get_hnsw_jinaclipv2_info_dict),
):
    """
    Return top-k frames similar to the frame with `db_idx`, based on pre-encoded embeddings.
    Do NOT re-encode the image at request time.
    """
    query_frame = frame_by_id.get(db_idx)
    if query_frame is None:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy frame db_idx={db_idx}")

    row_idx = frame_path_to_row.get(query_frame["frame_path"])
    if row_idx is None:
        raise HTTPException(
            status_code=500,
            detail=f"Frame db_idx={db_idx} chưa có trong index embedding (lệch dữ liệu)",
        )

    query_encoding = jinaclipv2_encoded_frames[row_idx]

    # Get the top_k most similar frames (excluding itself with cosine similarity = 1) and paginate the results.
    k = min(top_k + 1, jinaclipv2_encoded_frames.shape[0])
    scores, indices = search_similar(query_encoding, top_k=k)

    items = []
    for score, idx in zip(scores, indices):
        if idx == row_idx:
            continue  # pass the query frame itself
        frame_path = info_dict[str(idx)]["frame_path"]
        frame = frame_by_path.get(frame_path)
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
def search_event_mention(
    req: SearchRequest,
    device=Depends(get_device),
    index=Depends(get_flatip_dangvantuan_index),
    info_dict: dict = Depends(get_flatip_dangvantuan_info_dict),
    frame_by_path: dict = Depends(get_frame_by_path),
):
    """
    Type 3 — Event mention. Search for events mentioned in the transcript
    using the dangvantuan text-text embedding model.
 
    NOTE on `req.keywords`: currently NOT merged into the query for this
    route (undecided whether keyword-boosting a text-text transcript search
    makes sense the same way it does for Type 1's text-image search). Revisit
    if Type 3 search quality needs tuning.
    """
    events = search_flatip_dangvantuan_batch(
        [req.query or ""], k=req.k,
        index=index, device=device, info_dict=info_dict,
    )[0]
 
    # Join frame_path (string) -> full frame dict (db_idx, thumbnail, timestamp_sec...)
    # so GalleryItem.jsx / the cluster UI gets the same shape it already expects
    # from Type 2 clusters (frame_by_path already used the same way in /similar above).
    clusters = []
    for ev in events:
        frames = []
        for frame_path in ev["frames"]:
            frame = frame_by_path.get(frame_path)
            if frame is None:
                continue  # skip instead of crash, same defensive pattern as /similar
            frames.append(frame)
        if not frames:
            continue  # event has no resolvable frames -> not usable, drop it
 
        clusters.append({
            "video_id": ev["video_id"],
            "score": ev["score"],
            "frame_count": len(frames),
            "frames": frames,
            # extra context specific to Type 3 (transcript match) — frontend
            # displays these as the event caption above the frame strip
            "text": ev["text"],
            "start": ev["start"],
            "end": ev["end"],
        })
 
    # NOTE: search_flatip_dangvantuan_batch already sorts DESC by score
    # (IP/cosine similarity, higher = better) — do NOT re-sort here like
    # cluster_by_video does for Type 2 (that one uses L2 distance, lower =
    # better). Re-sorting ascending here would silently reverse the ranking.
    return to_response(paginate(clusters, req.page, req.imagesPerPage))