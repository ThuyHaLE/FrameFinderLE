// sceneseek-frontend/src/pages/EventPage.jsx

import { useState, useEffect, useCallback } from "react";
import { fetchEvents } from "../api/client";
import VideoGroupItem from "../components/results/VideoGroupItem";
import Pagination from "../components/results/Pagination";
import SkeletonGrid from "../components/results/SkeletonGrid";
import { groupClustersByVideo } from "../utils/clusterGrouping";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

// Fallback when NOT able to fetch /api/videos/l-options (or network error).
// Same endpoint/fallback as DataPage — the L dropdown is shared across pages.
const FALLBACK_L_OPTIONS = Array.from({ length: 24 }, (_, i) =>
  String(i + 1).padStart(2, "0")
); // ["01", "02", ..., "24"]

// Exact "L13_V001" format — event_id is local per video, so range filtering
// only makes sense when exactly one video is selected (not an "L13" prefix).
const EXACT_VIDEO_ID_RE = /^L\d+_V\d+$/;

// ---------------------------------------------------------------------------
// EventIdInput — integer input with ▲▼ shift buttons, mirrors TimestampInput's
// mechanism but for event_id instead of hh:mm:ss. Simpler than TimestampInput
// because the fallback here is a fixed constant (0 or -1), not something that
// has to be derived from currently loaded data.
// ---------------------------------------------------------------------------

function EventIdInput({ id, label, value, onChange, fallback, placeholder, disabled = false }) {
  function shift(delta) {
    if (disabled) return;
    const trimmed = value.trim();
    const base = trimmed === "" ? fallback : parseInt(trimmed, 10);
    const startFrom = isNaN(base) ? fallback : base;
    onChange(String(startFrom + delta));
  }

  function handleChange(e) {
    if (disabled) return;
    const val = e.target.value;
    // allow empty (-> uses fallback), optional leading '-', digits only
    if (val === "" || /^-?\d*$/.test(val)) {
      onChange(val);
    }
  }

  return (
    <div className={`ss-form-group ss-form-group--inline${disabled ? " ss-form-group--disabled" : ""}`}>
      <label htmlFor={id}>{label}</label>
      <div className="ss-timestamp-row">
        <input
          id={id}
          type="text"
          inputMode="numeric"
          value={value}
          placeholder={placeholder}
          onChange={handleChange}
          autoComplete="off"
          spellCheck={false}
          disabled={disabled}
        />
        <button type="button" className="ss-ts-btn" onClick={() => shift(1)} title="+1" disabled={disabled}>▲</button>
        <button type="button" className="ss-ts-btn" onClick={() => shift(-1)} title="-1" disabled={disabled}>▼</button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// VideoIDSelector — L select + V text input → "L13_V001"
// (identical to DataPage's — kept local/duplicated rather than shared to avoid
// coupling two pages through one file; extract to a shared component if it
// needs to change in more than one place.)
// ---------------------------------------------------------------------------

function VideoIDSelector({ videoId, onChange, lOptions }) {
  const match = videoId.match(/^L(\d+)_V(\d+)$/);
  const [lPart, setLPart] = useState(match ? match[1] : "");
  const [vPart, setVPart] = useState(match ? match[2] : "");

  useEffect(() => {
    if (lPart && vPart) {
      onChange(`L${lPart}_V${vPart.padStart(3, "0")}`);
    } else if (lPart) {
      onChange(`L${lPart}`);
    } else {
      onChange("");
    }
  }, [lPart, vPart]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleVChange(e) {
    const val = e.target.value.replace(/\D/g, "").slice(0, 3);
    setVPart(val);
  }

  const previewLabel = lPart && vPart
    ? `→ L${lPart}_V${vPart.padStart(3, "0")}`
    : lPart
    ? `→ L${lPart}_V* (tất cả)`
    : null;

  return (
    <div className="ss-form-group">
      <label>Video ID</label>
      <div className="ss-videoid-row">
        <select
          value={lPart}
          onChange={(e) => setLPart(e.target.value)}
          className="ss-videoid-select"
          aria-label="Chọn L"
        >
          <option value="">-- L --</option>
          {lOptions.map((l) => (
            <option key={l} value={l}>L{l}</option>
          ))}
        </select>

        <span className="ss-videoid-sep">_</span>

        <div className="ss-videoid-v-wrap">
          <span className="ss-videoid-v-prefix">V</span>
          <input
            type="text"
            inputMode="numeric"
            value={vPart}
            onChange={handleVChange}
            placeholder="* (tất cả)"
            className="ss-videoid-v-input ss-videoid-v-input--wide"
            aria-label="Nhập số V (để trống = lấy tất cả V)"
            maxLength={3}
          />
        </div>

        {previewLabel && (
          <span className="ss-videoid-preview">{previewLabel}</span>
        )}

        {(lPart || vPart) && (
          <button
            type="button"
            className="ss-btn ss-btn--ghost"
            onClick={() => { setLPart(""); setVPart(""); }}
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
} 

// ---------------------------------------------------------------------------
// EventPage
// ---------------------------------------------------------------------------

export default function EventPage() {
  const [videoId, setVideoId] = useState("");
  const [eventIdStart, setEventIdStart] = useState("");
  const [eventIdEnd, setEventIdEnd] = useState("");
  const [filterError, setFilterError] = useState(null);

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);

  // Bump to force VideoIDSelector remount (reset internal lPart/vPart) on clear —
  // same workaround as DataPage, see its comment for why.
  const [selectorResetKey, setSelectorResetKey] = useState(0);

  const [lOptions, setLOptions] = useState(FALLBACK_L_OPTIONS);

  const isExactVideo = EXACT_VIDEO_ID_RE.test(videoId.trim());

  useEffect(() => {
    if (!isExactVideo && (eventIdStart || eventIdEnd)) {
      setEventIdStart("");
      setEventIdEnd("");
    }
  }, [isExactVideo]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    let cancelled = false;
    fetch("/api/videos/l-options")
      .then((res) => (res.ok ? res.json() : Promise.reject(res.status)))
      .then((data) => {
        if (!cancelled && Array.isArray(data?.lOptions) && data.lOptions.length > 0) {
          setLOptions(data.lOptions);
        }
      })
      .catch(() => {
        // keep FALLBACK_L_OPTIONS if fetch fails
      });
    return () => { cancelled = true; };
  }, []);

  // -------------------------------------------------------------------------
  // Validation
  // -------------------------------------------------------------------------

  function validate() {
    const hasEventIdFilter = eventIdStart.trim() !== "" || eventIdEnd.trim() !== "";
    if (eventIdStart.trim() && !/^-?\d+$/.test(eventIdStart.trim()))
      return "Event ID bắt đầu phải là số nguyên.";
    if (eventIdEnd.trim() && !/^-?\d+$/.test(eventIdEnd.trim()))
      return "Event ID kết thúc phải là số nguyên (-1 = event cuối cùng).";
    // event_id is local per video (resets to 0 for each video), so the range
    // filter only makes sense against exactly one video, not an "L13" prefix.
    if (hasEventIdFilter && !EXACT_VIDEO_ID_RE.test(videoId.trim()))
      return "Vui lòng chọn đúng 1 Video ID (VD: L21_V001) khi lọc theo Event ID.";
    if (eventIdStart.trim() && eventIdEnd.trim()) {
      const s = parseInt(eventIdStart, 10);
      const e = parseInt(eventIdEnd, 10);
      if (!isNaN(s) && !isNaN(e) && e !== -1 && e < s)
        return "Event ID kết thúc phải >= Event ID bắt đầu (hoặc -1 cho event cuối).";
    }
    return null;
  }

  // -------------------------------------------------------------------------
  // Data loading
  // -------------------------------------------------------------------------

  const load = useCallback(async (targetPage = 1, overrides = {}) => {
    const filters = {
      videoId,
      eventIdStart,
      eventIdEnd,
      ...overrides, // allow calling with new values immediately, avoid stale closure
    };
    setLoading(true);
    try {
      const res = await fetchEvents({
        page: targetPage,
        perPage: 20,
        videoId: filters.videoId.trim(),
        eventIdStart: filters.eventIdStart.trim(),
        eventIdEnd: filters.eventIdEnd.trim(),
      });
      setEvents(res.events);
      setTotalPages(res.totalPages);
      // Trust backend's returned page, same reasoning as DataPage:
      // avoids UI showing page > totalPages after a filter shrinks the result set.
      setPage(res.page ?? targetPage);
    } finally {
      setLoading(false);
    }
  }, [videoId, eventIdStart, eventIdEnd]);

  useEffect(() => { load(1); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  function handleSubmit(e) {
    e.preventDefault();
    const err = validate();
    if (err) { setFilterError(err); return; }
    setFilterError(null);
    load(1);
  }

  function handleClear() {
    setVideoId("");
    setEventIdStart("");
    setEventIdEnd("");
    setFilterError(null);
    setSelectorResetKey((k) => k + 1);
    load(1, { videoId: "", eventIdStart: "", eventIdEnd: "" });
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  const groups = groupClustersByVideo(events);

  return (
    <div className="ss-data-page">
      <h2>Event Overview</h2>

      <form className="ss-search-form" onSubmit={handleSubmit}>
        <VideoIDSelector key={selectorResetKey} videoId={videoId} onChange={setVideoId} lOptions={lOptions} />

        <div className="ss-form-row">
          <EventIdInput
            id="event_id_start"
            label="Bắt đầu tại"
            value={eventIdStart}
            onChange={setEventIdStart}
            fallback={0}
            placeholder="0 (event đầu tiên)"
            disabled={!isExactVideo}
          />
          <EventIdInput
            id="event_id_end"
            label="Kết thúc tại"
            value={eventIdEnd}
            onChange={setEventIdEnd}
            fallback={-1}
            placeholder="-1 (event cuối cùng)"
            disabled={!isExactVideo}
          />
        </div>

        <p className="ss-form-hint">
          {isExactVideo
            ? "Để trống → 0 (đầu) và -1 (cuối)."
            : "Chọn đúng 1 Video ID (VD: L21_V001) để lọc theo Event ID."}
        </p>

        {filterError && <p className="ss-form-error">{filterError}</p>}

        <div className="ss-form-actions">
          <button type="submit" className="ss-btn ss-btn--primary" disabled={loading}>
            {loading ? "Đang tải..." : "Apply Filter"}
          </button>
          <button type="button" className="ss-btn ss-btn--ghost" onClick={handleClear}>
            Xoá filter
          </button>
        </div>
      </form>

      {loading ? (
        <SkeletonGrid count={50} />
      ) : events.length === 0 ? (
        <p className="ss-results-status">Không tìm thấy sự kiện nào phù hợp.</p>
      ) : (
        <div className="ss-cluster-list">
          {groups.map((g) => (
            <VideoGroupItem
              key={g.video_id}
              videoId={g.video_id}
              events={g.events}
              // no search-similar action in browse mode, and no SearchProvider
              // wraps EventPage — FeedbackButtons needs SearchContext, so it must
              // stay off here (same convention as DataPage's GalleryItem readOnly/showFeedback={false})
              onSearchSimilar={undefined}
              showFeedback={false}
            />
          ))}
        </div>
      )}

      <Pagination page={page} totalPages={totalPages} onChange={load} />
    </div>
  );
}