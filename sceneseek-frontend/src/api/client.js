/**
 * api/client.js — SceneSeek API client
 * =====================================
 * Pattern: try real backend first, fallback to mock if it fails.
 *
 * - Backend route đã implement → trả HTTP 200 → dùng data thật.
 * - Backend route chưa implement → trả 501 → catch → fallback mock.
 * - Backend không chạy (network error) → catch → fallback mock.
 *
 * Để update từng route: implement route trong app.py, xoá `throw` / 501,
 * trả data thật → client tự nhận ra và dừng dùng mock cho route đó.
 * Không cần đổi flag hay build lại.
 */

import { getQueryType } from "../config/queryTypes";

const API_BASE = ""; // e.g. "http://localhost:8000" khi chạy 2 server riêng

// ---------------------------------------------------------------------------
// Core fetch helper
// ---------------------------------------------------------------------------

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    // 501 = chưa implement, 4xx/5xx khác = lỗi thật
    throw new Error(`API ${res.status}: ${path}`);
  }
  return res.json();
}

/**
 * Thử gọi real backend. Nếu thất bại vì bất kỳ lý do gì
 * (network, 501, 4xx, 5xx) → trả null để caller fallback về mock.
 */
async function tryReal(fn) {
  try {
    const result = await fn();
    return result ?? null;
  } catch {
    return null;
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

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Search by query type (Type 1 / 2 / 3).
 * Tries the real endpoint for the active type; falls back to mock.
 */
export async function searchByType(typeKey, fieldValues, opts) {
  const { page = 1, imagesPerPage = 50, keywords = [], k = 100,
          displayOption = "sort_by_frame_index", sessionId } = opts;

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
      }),
    })
  );
  if (real) return real;

  await mockDelay();
  return mockSearchResponse(page, imagesPerPage);
}

/**
 * Refine results using accumulated feedback.
 * Tries /api/search/{type}/refine; falls back to shuffled mock.
 */
export async function refineResults(typeKey, fieldValues, opts) {
  const { page = 1, imagesPerPage = 50, keywords = [], k = 100,
          displayOption, sessionId } = opts;

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
      }),
    })
  );
  if (real) return real;

  await mockDelay();
  return mockSearchResponse(page, imagesPerPage, /* shuffle= */ true);
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
export async function fetchKeyframes({ page = 1, perPage = 50, videoId = "", timestamp = "" }) {
  const params = new URLSearchParams({
    page,
    perPage,
    ...(videoId && { video_ID: videoId }),
    ...(timestamp && { timestamp }),
  });

  const real = await tryReal(() => request(`/api/data?${params.toString()}`));
  if (real) return real;

  await mockDelay();
  const pool = videoId
    ? Array.from({ length: 30 }, (_, i) => makeMockResult(i + 1, videoId))
    : MOCK_POOL;
  const { items, total, totalPages } = paginate(pool, page, perPage);
  return { keyframes: items, total, totalPages };
}