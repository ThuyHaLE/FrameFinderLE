# tools/search_utils.py

"""
Search helpers shared for search_router.py

Includes:
    search(...)                         — encode 1 query, search FAISS, return top-k
    search_hnsw_jinaclipv2_batch(...)   — encode lots of queries at once (more efficient)
    pair_boundary_results(...)          — get pairs (start, end) for Type 2

Architecture note:
functions here are designed to accept index/device/image_info_dict as PARAMETERS
(defaulting to model_state if not passed), so that:
    - Router can call with values from Depends() — keeping the DI pattern
        that deps.py has built (easy to mock for testing).
    - Notebook / standalone script can still call normally, without
        changing anything (if nothing is passed, it will default to model_state).

Note on field names: IMAGE_INFO_DICT uses the ORIGINAL names from the JSON annotation
(video_ID, time_in_seconds, frame_ID...), NOT the normalized names in state.ALL_FRAMES (video_id, timestamp_sec, db_idx...).
All comparisons/joins in this file must use the original names.
"""

from typing import List, Optional
import model_state
from tools.faiss_retrieval import k_image_search
from tools.query_encoding import encode_texts
from utils import build_thumbnail_url
import math

"""
Lookup frame_path -> db_idx, build 1 time when module is imported.
Used to join FAISS results (which don't have db_idx) back to state.ALL_FRAMES
(which has db_idx, used for feedback/like-dislike).

IMPORTANT: only use this lookup if you've confirmed that frame_ID in
IMAGE_INFO_DICT does NOT overlap with db_idx in state.ALL_FRAMES.
If they do overlap, you can skip this join step and use info["frame_ID"] directly.
"""

try:
    import state
    _FRAME_PATH_TO_DB_IDX = {
        item["frame_path"]: item["db_idx"] for item in state.ALL_FRAMES
    }
except Exception:
    # Allow this file to run independently in a notebook without state.py
    _FRAME_PATH_TO_DB_IDX = {}


def _enrich(info: dict, dist: float, idx: int) -> dict:
    """Add faiss_idx, distance, db_idx, thumbnail to a result record."""
    info = dict(info)
    info["faiss_idx"] = int(idx)
    info["distance"] = float(dist)
    info["db_idx"] = _FRAME_PATH_TO_DB_IDX.get(info.get("frame_path"))
    info["thumbnail"] = build_thumbnail_url(info["frame_path"])
    return info


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


def search_hnsw_jinaclipv2_batch(
        queries: List[str], k: int = 5,
        truncate_dim: Optional[int] = None,
        index=None, device=None,
        info_dict: Optional[dict] = None,) -> List[List[dict]]:
    """
    Find top-k keyframes for multiple queries at once — more efficient than calling search() repeatedly
    because it encodes the queries only once.
 
    :param queries: list of query strings
    :param k: number of results to return for EACH query
    :param truncate_dim: MUST match the truncate_dim used when encoding images
    :param index: FAISS/HNSW index; defaults to model_state.HNSW_JINACLIPV2.index
    :param device: defaults to model_state.DEVICE
    :param info_dict: defaults to model_state.HNSW_JINACLIPV2.info_dict
    :return: list[list[dict]] — a list of results for each query, in the same order as the input.
        Returns [] if `queries` is empty.
    """
    if not queries:
        return []
 
    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")
 
    index = index if index is not None else model_state.HNSW_JINACLIPV2.index
    device = device if device is not None else model_state.DEVICE
    info_dict = (
        info_dict if info_dict is not None else model_state.HNSW_JINACLIPV2.info_dict
    )
 
    query_embeddings = encode_texts(
        queries, model_name='jina-clip-v2', 
        truncate_dim=truncate_dim, show_progress=False)
 
    distances, indices = k_image_search(
        query_vector=query_embeddings,
        index=index,
        device=device,
        k_nums=k,
    )
 
    all_results = []
    for q_dist, q_idx in zip(distances, indices):
        results = []
        for dist, idx in zip(q_dist, q_idx):
            if idx == -1:
                continue
            info = info_dict[str(idx)]
            results.append(_enrich(info, dist, idx))
        all_results.append(results)
    return all_results


def hnsw_jinaclipv2_search(query: str, k: int = 5, truncate_dim: Optional[int] = None,
                           index=None, device=None, info_dict: Optional[dict] = None,) -> List[dict]:
    """Find top-keyframe matches for a single query. Wrapper around search_hnsw_jinaclipv2_batch()."""
    return search_hnsw_jinaclipv2_batch(
        [query], k=k, truncate_dim=truncate_dim,
        index=index, device=device, info_dict=info_dict,
    )[0]


def to_response(paged: dict) -> dict:
    """Change key names from paginate() to the shape expected by SearchContext.jsx."""
    return {
        "results": paged["items"],
        "totalImages": paged["total"],
        "totalPages": paged["totalPages"],
        "page": paged["page"],
    }


def normalize_frame(r: dict) -> dict:
    """Map video_ID (original name) -> video_id (name needed by GalleryItem.jsx)."""
    r = dict(r)
    r.setdefault('video_id', r.get('video_ID'))
    return r


def sort_results(results: list, display_option: str) -> list:
    """
    Apply displayOption to the list of results (already enriched via search_hnsw_jinaclipv2_batch(), 
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


def _best_ordered_chain(items: list) -> Optional[list]:
    """
    items: all candidate matches (from any channel) belonging to ONE video.
    Finds the chain of items, ordered by frame_idx ascending, whose channel
    indices are STRICTLY increasing (so each channel appears at most once,
    and later channels correspond to later timestamps) — optimizing:
        1) most distinct channels covered (primary)
        2) lowest total distance (tie-break)
    O(m^2) time, O(m) extra memory (parent-pointer DP, chain built once at the end).
    Returns None if items is empty.
    """
    if not items:
        return None

    items_sorted = sorted(items, key=lambda r: r["frame_idx"])
    n = len(items_sorted)

    dp_channels = [1] * n
    dp_dist = [items_sorted[i]["distance"] for i in range(n)]
    parent = [-1] * n

    for i in range(n):
        ci = items_sorted[i]["_channel"]
        for j in range(i):
            cj = items_sorted[j]["_channel"]
            if cj >= ci:
                continue  # channel must strictly increase with time;
                          # transitivity guarantees no duplicate channel in chain
            cand_channels = dp_channels[j] + 1
            cand_dist = dp_dist[j] + items_sorted[i]["distance"]
            if (cand_channels, -cand_dist) > (dp_channels[i], -dp_dist[i]):
                dp_channels[i] = cand_channels
                dp_dist[i] = cand_dist
                parent[i] = j

    best_i = max(range(n), key=lambda i: (dp_channels[i], -dp_dist[i]))

    chain = []
    i = best_i
    while i != -1:
        chain.append(items_sorted[i])
        i = parent[i]
    chain.reverse()
    return chain


def cluster_by_video(
    channel_results: List[list],
    video_index: dict,
    min_occurrences: Optional[int] = None,
    strict: bool = True,
    ) -> list:
    """
    Cluster search results by video, finding an ordered sequence of matched
    frames — one per query "scene" (channel) — that appears in the correct
    chronological order within the video (channel 0 = earliest scene,
    channel N-1 = latest scene).

    channel_results: list of result-lists, in the SAME order the user entered
        the scenes (e.g. [results_for_cảnh_1, results_for_cảnh_2, results_for_cảnh_3]).
        Each results-list is the output of one query from
        search_hnsw_jinaclipv2_batch.
    video_index: video_ID -> list of all real frames of that video
        (each frame dict has at least "frame_idx").
    min_occurrences: minimum number of DISTINCT channels that must be matched,
        in correct order, for a video to be considered a valid cluster.
        - Ignored if strict=True (forced to len(channel_results), i.e. every
          scene must match, in order).
        - If strict=False and not given, defaults to max(2, N-1) — i.e.
          allow at most 1 missing scene (to tolerate imperfect encoding/search).
    strict: True = require ALL scenes to match in order ("tìm chính xác").
            False = allow some scenes to be missing ("tìm tương đối"),
            governed by min_occurrences.

    Returns a list of clusters sorted by:
        1) number of matched channels, descending (more complete match first)
        2) score (sum of distances in the winning chain), ascending (closer match first)
    Each cluster:
        {
            "video_id": ...,
            "score": ...,
            "frame_count": ...,
            "frames": [...],                # all real frames within [start, end]
            "matched_channels": [...],      # sorted list of channel indices matched
            "missing_channels": [           # detail on unmatched channels
                {
                    "channel": <int>,
                    "reason": "no_match_in_video" | "excluded_by_ordering",
                    # only present for "excluded_by_ordering":
                    "best_candidate_frame_idx": <int>,
                    "best_candidate_distance": <float>,
                },
                ...
            ],
        }
    """
    if not channel_results:
        return []

    n_channels = len(channel_results)

    if strict:
        effective_min_occurrences = n_channels
    else:
        effective_min_occurrences = (
            min_occurrences if min_occurrences is not None
            else max(2, n_channels - 1)
        )
        effective_min_occurrences = min(effective_min_occurrences, n_channels)

    # 1. Pool all channels together, tag each item with its channel index,
    #    and group by video in the same pass.
    by_video: dict = {}
    for channel_idx, results in enumerate(channel_results):
        for r in results:
            item = dict(r, _channel=channel_idx)
            by_video.setdefault(item["video_ID"], []).append(item)

    clusters = []
    for video_ID, items in by_video.items():
        chain = _best_ordered_chain(items)
        if chain is None:
            continue

        chain_channels = {r["_channel"] for r in chain}
        if len(chain_channels) < effective_min_occurrences:
            continue

        start_idx = chain[0]["frame_idx"]
        end_idx = chain[-1]["frame_idx"]
        if start_idx == end_idx:
            continue  # min == max, not enough to create a real segment

        video_frames = video_index.get(video_ID, [])
        frames_in_range = sorted(
            (f for f in video_frames if start_idx <= f["frame_idx"] <= end_idx),
            key=lambda f: f["frame_idx"],
        )
        if not frames_in_range:
            continue

        # 2. Build missing-channel detail for debugging / UI display.
        items_by_channel: dict = {}
        for r in items:
            items_by_channel.setdefault(r["_channel"], []).append(r)

        missing_detail = []
        for ch in range(n_channels):
            if ch in chain_channels:
                continue
            candidates = items_by_channel.get(ch, [])
            if not candidates:
                missing_detail.append({
                    "channel": ch,
                    "reason": "no_match_in_video",
                })
            else:
                best_excluded = min(candidates, key=lambda r: r["distance"])
                missing_detail.append({
                    "channel": ch,
                    "reason": "excluded_by_ordering",
                    "best_candidate_frame_idx": best_excluded["frame_idx"],
                    "best_candidate_distance": best_excluded["distance"],
                })

        score = sum(r["distance"] for r in chain)
        clusters.append({
            "video_id": video_ID,
            "score": score,
            "frame_count": len(frames_in_range),
            "frames": frames_in_range,
            "matched_channels": sorted(chain_channels),
            "missing_channels": missing_detail,
        })

    clusters.sort(key=lambda c: (-len(c["matched_channels"]), c["score"]))
    return clusters


def search_flatip_dangvantuan_batch(
        queries: List[str], k: int = 5,
        fetch_multiplier: int = 5,
        index=None, device=None,
        info_dict: Optional[dict] = None,) -> List[List[dict]]:
    """
    Find top-k deduplicated events for multiple queries at once — more
    efficient than calling search() repeatedly because it encodes the
    queries only once.

    :param queries: list of query strings
    :param k: number of deduplicated results to return for EACH query
    :param fetch_multiplier: how many raw candidates to fetch per query
        before dedup (n_fetch = k * fetch_multiplier), since deduping by
        (video_id, event_id) can collapse multiple raw hits into one entry
    :param index: FAISS index; defaults to model_state.FLATIP_DANGVANTUAN.index
    :param device: defaults to model_state.DEVICE
    :param info_dict: defaults to model_state.FLATIP_DANGVANTUAN.info_dict
    :return: list[list[dict]] — deduplicated, score-sorted results for each
        query, in the same order as the input queries. Returns [] if `queries` is empty.
    """
    if not queries:
        return []

    if k < 1:
        raise ValueError(f"k must be >= 1, got {k}")

    if fetch_multiplier < 1:
        raise ValueError(f"fetch_multiplier must be >= 1, got {fetch_multiplier}")

    index = index if index is not None else model_state.FLATIP_DANGVANTUAN.index
    device = device if device is not None else model_state.DEVICE
    info_dict = (
        info_dict if info_dict is not None else model_state.FLATIP_DANGVANTUAN.info_dict
    )

    query_embeddings = encode_texts(queries, model_name='dangvantuan', show_progress=False)

    n_fetch = k * fetch_multiplier

    distances, indices = k_image_search(
        query_vector=query_embeddings,
        index=index,
        device=device,
        k_nums=n_fetch,
    )

    all_results = []
    for q_dist, q_idx in zip(distances, indices):
        # dedupe by (video_id, event_id), keep highest score
        seen = {}
        for distance, idx in zip(q_dist, q_idx):
            if idx == -1:
                continue
            info = info_dict[idx]
            key = (info["video_id"], info["event_id"])
            if key not in seen or distance > seen[key]["score"]:
                seen[key] = {
                    "video_id": info["video_id"],
                    "group": info["group"],
                    "event_id": info["event_id"],
                    "start": info["start"],
                    "end": info["end"],
                    "text": info["text"],
                    "frames": [kf["frame_path"] for kf in info["keyframes"]],
                    "score": float(distance),
                }

        query_results = sorted(seen.values(), key=lambda x: -x["score"])[:k]
        all_results.append(query_results)

    return all_results