/**
 * Centralized API client.
 *
 * This is the ONLY file that should know whether data is mocked or real.
 * Every component calls these functions, never `fetch` directly. When the
 * real retrieval backend is ready, flip USE_MOCK to false (or delete the
 * mock branch) — no component needs to change.
 */

import { getQueryType } from "../config/queryTypes";

const USE_MOCK = true;
const API_BASE = ""; // e.g. "http://localhost:8000" when running frontend/backend separately

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

function makeMockResult(i, videoId = `L01_V${String((i % 5) + 1).padStart(3, "0")}`) {
  return {
    db_idx: i,
    video_id: videoId,
    frame_id: `F${String(i).padStart(4, "0")}`,
    timestamp: 12.5 * i,
    thumbnail: `https://placehold.co/320x180?text=${videoId}`,
    description: "Mô tả khung cảnh mẫu (mock) cho frame này.",
    score: 1 - i * 0.03,
    feedback: null, // 'like' | 'dislike' | null
  };
}

const MOCK_POOL = Array.from({ length: 60 }, (_, i) => makeMockResult(i + 1));

function paginate(items, page, perPage) {
  const start = (page - 1) * perPage;
  const pageItems = items.slice(start, start + perPage);
  return {
    items: pageItems,
    total: items.length,
    totalPages: Math.max(1, Math.ceil(items.length / perPage)),
  };
}

async function mockDelay(ms = 300) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
// Real fetch helper (used once USE_MOCK is false)
// ---------------------------------------------------------------------------

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${await res.text()}`);
  }
  return res.json();
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Run a search for the given query type.
 * @param {string} typeKey - one of the keys in config/queryTypes.js
 * @param {object} fieldValues - e.g. { query } or { start_query, end_query }
 * @param {object} opts - { keywords, k, displayOption, page, imagesPerPage, sessionId }
 */
export async function searchByType(typeKey, fieldValues, opts) {
  if (USE_MOCK) {
    await mockDelay();
    const { page = 1, imagesPerPage = 50 } = opts;
    const { items, total, totalPages } = paginate(MOCK_POOL, page, imagesPerPage);
    return { results: items, totalImages: total, page, totalPages };
  }

  const type = getQueryType(typeKey);
  return request(type.endpoint, {
    method: "POST",
    body: JSON.stringify({ ...fieldValues, ...opts }),
  });
}

/** Keyword graph suggestions for the free-text query (replaces old hashtag generation). */
export async function getKeywordSuggestions(queryText) {
  if (USE_MOCK) {
    await mockDelay(150);
    if (!queryText.trim()) return [];
    return queryText
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 4)
      .map((w) => w.toLowerCase());
  }

  return request("/api/process_query", {
    method: "POST",
    body: JSON.stringify({ query_text: queryText }),
  }).then((d) => d.keywords ?? []);
}

/** Record a like/dislike on a single result. */
export async function sendFeedback(dbIdx, action, sessionId) {
  if (USE_MOCK) {
    await mockDelay(100);
    return { feedbackStatus: action, dbIdx };
  }
  return request("/api/update_feedback", {
    method: "POST",
    body: JSON.stringify({ db_idx: dbIdx, action, session_id: sessionId }),
  });
}

/** Trigger refinement using accumulated feedback for the session. */
export async function refineResults(typeKey, fieldValues, opts) {
  if (USE_MOCK) {
    await mockDelay();
    const { page = 1, imagesPerPage = 50 } = opts;
    const shuffled = [...MOCK_POOL].sort(() => Math.random() - 0.5);
    const { items, total, totalPages } = paginate(shuffled, page, imagesPerPage);
    return { results: items, totalImages: total, page, totalPages };
  }

  const type = getQueryType(typeKey);
  return request(`${type.endpoint}/refine`, {
    method: "POST",
    body: JSON.stringify({ ...fieldValues, ...opts }),
  });
}

/** Browse keyframes by video_id / timestamp — backs the Data page. */
export async function fetchKeyframes({ page = 1, perPage = 50, videoId = "", timestamp = "" }) {
  if (USE_MOCK) {
    await mockDelay();
    const filtered = videoId
      ? MOCK_POOL.filter((r) => r.video_id === videoId)
      : MOCK_POOL;
    const { items, total, totalPages } = paginate(filtered, page, perPage);
    return { keyframes: items, total, totalPages };
  }
  const params = new URLSearchParams({ page, video_ID: videoId, timestamp });
  return request(`/api/data?${params.toString()}`);
}
