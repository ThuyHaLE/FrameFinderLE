// sceneseek-frontend/src/api/client.js

/**
 * SceneSeek API client
 * =====================================
 * Pattern: try real backend first, fallback to mock if it fails.
 *
 * - Backend route is implemented → return HTTP 200 → use real data.
 * - Backend route is NOT implemented → return 501 → catch → fallback mock.
 * - Backend is not running (network error) → catch → fallback mock.
 *
 * To update each route: implement the route in app.py, remove `throw` / 501,
 * return real data → client will automatically detect and stop using mock for that route.
 * No need to change flags or rebuild.
 */

import { getQueryType } from "../config/queryTypes";

const API_BASE = ""; // e.g. "http://localhost:8000" when running 2 different servers

// ---------------------------------------------------------------------------
// Core fetch helper
// ---------------------------------------------------------------------------

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = new Error(`API ${res.status}: ${path}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

/**
 * Try calling the real backend.
 * - 501 (not implemented) or network error → return null (caller falls back to mock).
 * - Any other error (4xx/5xx, JSON parse error...) → re-thrown, caller must catch and show a real error.
 */
async function tryReal(fn) {
  try {
    const result = await fn();
    return result ?? null;
  } catch (e) {
    if (e.status === 501) return null;
    if (e instanceof TypeError) return null;
    throw e;
  }
}

// ---------------------------------------------------------------------------
// Mock helpers
// ---------------------------------------------------------------------------

function makeMockResult(i, videoId) {
  const vid = videoId ?? `L01_V${String((i % 5) + 1).padStart(3, "0")}`;
  return {
    db_idx: i,
    video_id: vid,
    frame_id: `F${String(i).padStart(4, "0")}`,
    frame_idx: i, 
    timestamp: 12.5 * i,
    thumbnail: `https://placehold.co/320x180/1a1a2e/ffffff?text=${vid}`,
    description: `[Mock] Frame ${i} — ${vid}`,
    score: Math.max(0, 1 - i * 0.015),
    feedback: null,
  };
}

const MOCK_POOL = Array.from({ length: 120 }, (_, i) => makeMockResult(i + 1));

function paginate(items, page, perPage) {
  const total = items.length;
  const totalPages = Math.max(1, Math.ceil(total / perPage));
  const safePage = Math.max(1, Math.min(page, totalPages));
  const start = (safePage - 1) * perPage;
  return {
    items: items.slice(start, start + perPage),
    total,
    totalPages,
    page: safePage,
  };
}

async function mockDelay(ms = 280) {
  return new Promise((r) => setTimeout(r, ms));
}

function mockSearchResponse(page, imagesPerPage, shuffle = false) {
  const pool = shuffle ? [...MOCK_POOL].sort(() => Math.random() - 0.5) : MOCK_POOL;
  const { items, total, totalPages } = paginate(pool, page, imagesPerPage);
  return { results: items, totalImages: total, page, totalPages };
}

function makeMockCluster(i, videoId) {
  const vid = videoId ?? `L01_V${String((i % 5) + 1).padStart(3, "0")}`;
  const frameCount = 3 + (i % 3); // 3–5 frames mỗi cluster, để UI test được nhiều size
  return {
    video_id: vid,
    event_id: i,               // vô hại với event_boundary (không dùng field này), cần thiết cho event_mention
    score: Math.max(0, 1 - i * 0.02),
    frame_count: frameCount,
    frames: Array.from({ length: frameCount }, (_, j) =>
      makeMockResult(i * 10 + j + 1, vid)
    ),
  };
}

const MOCK_CLUSTER_POOL = Array.from({ length: 40 }, (_, i) => makeMockCluster(i + 1));

function mockClusterResponse(page, imagesPerPage, shuffle = false) {
  const pool = shuffle
    ? [...MOCK_CLUSTER_POOL].sort(() => Math.random() - 0.5)
    : MOCK_CLUSTER_POOL;
  const { items, total, totalPages } = paginate(pool, page, imagesPerPage);
  return { results: items, totalImages: total, page, totalPages };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Search by query type (Type 1 / 2 / 3).
 * Tries the real endpoint for the active type; falls back to mock.
 */
export async function searchByType(typeKey, fieldValues, opts) {
  const { page = 1, imagesPerPage = 50, keywords = [], k = 100,
          displayOption = "sort_by_frame_index", sessionId,
          strict = true, minOccurrences = null } = opts;

  const type = getQueryType(typeKey);

  const real = await tryReal(() =>
    request(type.endpoint, {
      method: "POST",
      body: JSON.stringify({
        ...fieldValues,
        keywords,
        k,
        displayOption,
        page,
        imagesPerPage,
        sessionId,
        strict, 
        minOccurrences,
      }),
    })
  );
  if (real) return real;

  await mockDelay();
  return type.resultShape === "cluster"
    ? mockClusterResponse(page, imagesPerPage)
    : mockSearchResponse(page, imagesPerPage);
}

/**
 * Refine results using accumulated feedback.
 * Tries /api/search/{type}/refine; falls back to shuffled mock.
 */
export async function refineResults(typeKey, fieldValues, opts) {
  const { page = 1, imagesPerPage = 50, keywords = [], k = 100,
          displayOption, sessionId,
          strict = true, minOccurrences = null } = opts;

  const type = getQueryType(typeKey);

  const real = await tryReal(() =>
    request(`${type.endpoint}/refine`, {
      method: "POST",
      body: JSON.stringify({
        ...fieldValues,
        keywords,
        k,
        displayOption,
        page,
        imagesPerPage,
        sessionId,
        strict, 
        minOccurrences,
      }),
    })
  );
  if (real) return real;

  await mockDelay();
  return type.resultShape === "cluster"
    ? mockClusterResponse(page, imagesPerPage, /* shuffle= */ true)
    : mockSearchResponse(page, imagesPerPage, /* shuffle= */ true);
}

/**
 * Keyword graph suggestions.
 * Tries /api/process_query; falls back to naive word-split mock.
 */
export async function getKeywordSuggestions(queryText) {
  if (!queryText.trim()) return [];

  const real = await tryReal(() =>
    request("/api/process_query", {
      method: "POST",
      body: JSON.stringify({ query_text: queryText }),
    })
  );
  if (real) return real.keywords ?? [];

  await mockDelay(100);
  const stop = new Set(["một", "và", "của", "ở", "tại", "trước", "sau", "đang", "được"]);
  return queryText
    .toLowerCase()
    .split(/\s+/)
    .filter((w) => w && !stop.has(w))
    .slice(0, 5);
}

/**
 * Send like/dislike feedback.
 * Tries /api/update_feedback; silently ignores failure (best-effort).
 */
export async function sendFeedback(dbIdx, action, sessionId) {
  const real = await tryReal(() =>
    request("/api/update_feedback", {
      method: "POST",
      body: JSON.stringify({ db_idx: dbIdx, action, session_id: sessionId }),
    })
  );
  // Feedback is always best-effort — no mock fallback needed,
  // UI already reflects the click via local state in SearchContext.
  return real ?? { feedbackStatus: action, dbIdx };
}



/**
 * Browse keyframes by video_ID / timestamp (Data page).
 * Tries /api/data; falls back to mock pool filtered by videoId.
 */
export async function fetchKeyframes({ page = 1, perPage = 50, videoId = "", timestamp = "", timestamp_end = "" }) {
  const isExactVideo = /^L\d+_V\d+$/.test(videoId.trim());
  const safeTimestamp = isExactVideo ? timestamp : "";
  const safeTimestampEnd = isExactVideo ? timestamp_end : "";

  const params = new URLSearchParams({
    page,
    perPage,
    ...(videoId && { video_ID: videoId }),
    ...(safeTimestamp && { timestamp: safeTimestamp }),
    ...(safeTimestampEnd && { timestamp_end: safeTimestampEnd }),
  });

  const real = await tryReal(() => request(`/api/data?${params.toString()}`));
  if (real) return real;

  await mockDelay();
  const pool = isExactVideo
    ? Array.from({ length: 30 }, (_, i) => makeMockResult(i + 1, videoId))
    : videoId
    ? Array.from({ length: 30 }, (_, i) => makeMockResult(i + 1, videoId))
    : MOCK_POOL;
  const { items, total, totalPages } = paginate(pool, page, perPage);
  return { keyframes: items, total, totalPages };
}

/**
 * Browse events (transcript-segmented) by video_ID (Event page).
 * Tries /api/events; falls back to a mock pool grouped like a real event list.
 */
export async function fetchEvents({ page = 1, perPage = 20, videoId = "", eventIdStart = "", eventIdEnd = "" }) {
  const params = new URLSearchParams({
    page,
    perPage,
    ...(videoId && { video_ID: videoId }),
    ...(eventIdStart !== "" && { event_id_start: eventIdStart }),
    ...(eventIdEnd !== "" && { event_id_end: eventIdEnd }),
  });
 
  const real = await tryReal(() => request(`/api/events?${params.toString()}`));
  if (real) return real; // backend đã trả maxEventId
 
  await mockDelay();
  const vid = videoId || "L01_V001";
  const isExactVideo = /^L\d+_V\d+$/.test(videoId.trim());
  const mockEvents = Array.from({ length: 6 }, (_, i) => {
    const start = i * 30;
    const end = start + 25 + i;
    return {
      video_id: vid,
      event_id: i,
      start,
      end,
      text: `[Mock] Nội dung sự kiện ${i + 1} của ${vid}, diễn ra từ ${start}s đến ${end}s.`,
      frames: Array.from({ length: 3 }, (_, j) => makeMockResult(i * 3 + j + 1, vid)),
      frame_count: 3,
    };
  });
  const { items, total, totalPages } = paginate(mockEvents, page, perPage);
  return {
    events: items,
    total,
    totalPages,
    maxEventId: isExactVideo ? mockEvents.length - 1 : null, // = 5, khớp mock pool 6 events (0..5)
  };
}

/**
 * Find frames similar to a given frame (click 🔍 on a GalleryItem).
 * Tries GET /api/search/similar/{dbIdx}; falls back to a mock pool
 * with fake similarity scores, excluding the query frame itself.
 */
export async function getSimilarFrames(dbIdx, opts = {}) {
  const { page = 1, perPage = 50, topK = 100 } = opts;

  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
    top_k: String(topK),
  });

  const real = await tryReal(() => request(`/api/search/similar/${dbIdx}?${params.toString()}`));
  if (real) {
    return {
      queryFrame: real.queryFrame,
      results: real.items,
      totalImages: real.total,
      totalPages: real.totalPages,
      page: real.page,
    };
  }

  await mockDelay();
  const queryFrame = MOCK_POOL.find((f) => f.db_idx === dbIdx) ?? makeMockResult(dbIdx);
  const pool = MOCK_POOL
    .filter((f) => f.db_idx !== dbIdx)
    .map((f) => ({ ...f, similarity: Math.max(0, 1 - Math.random() * 0.4) }))
    .sort((a, b) => b.similarity - a.similarity)
    .slice(0, topK);
  const { items, total, totalPages, page: safePage } = paginate(pool, page, perPage);
  return { queryFrame, results: items, totalImages: total, totalPages, page: safePage };
}