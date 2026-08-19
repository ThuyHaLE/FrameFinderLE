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

const FALLBACK_L_OPTIONS = Array.from({ length: 24 }, (_, i) =>
  String(i + 1).padStart(2, "0")
);

// Same "exact video" test used by client.js's fetchEvents / event_router.py's
// "_V" in video_ID check — keep in sync if that rule ever changes.
const EXACT_VIDEO_RE = /^L\d+_V\d+$/;

// ---------------------------------------------------------------------------
// VideoIDSelector — unchanged
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
// EventIDSelector — only meaningful once videoId is an exact "L13_V001".
// Mirrors the "timestamp only unlocks after exact video" gating in DataPage,
// but for a single numeric event_id instead of a start/end range.
// ---------------------------------------------------------------------------

function EventIDSelector({ eventId, onChange, disabled }) {
  function handleChange(e) {
    const val = e.target.value.replace(/\D/g, "").slice(0, 4);
    onChange(val);
  }

  return (
    <div className="ss-form-group">
      <label>Event ID</label>
      <input
        type="text"
        inputMode="numeric"
        value={eventId}
        onChange={handleChange}
        disabled={disabled}
        placeholder={disabled ? "Chọn video cụ thể trước" : "* (tất cả sự kiện)"}
        className="ss-videoid-v-input"
        aria-label="Nhập event ID (chỉ dùng được khi đã chọn 1 video cụ thể)"
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// EventPage
// ---------------------------------------------------------------------------

export default function EventPage() {
  const [videoId, setVideoId] = useState("");
  const [eventId, setEventId] = useState("");

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [selectorResetKey, setSelectorResetKey] = useState(0);
  const [lOptions, setLOptions] = useState(FALLBACK_L_OPTIONS);

  const isExactVideo = EXACT_VIDEO_RE.test(videoId.trim());

  // Clear eventId as soon as videoId stops being an exact video — same reasoning
  // as why DataPage clears its timestamp filter when leaving an exact video.
  useEffect(() => {
    if (!isExactVideo && eventId) {
      setEventId("");
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
      .catch(() => {});
    return () => { cancelled = true; };
  }, []);

  // -------------------------------------------------------------------------
  // Data loading
  // -------------------------------------------------------------------------

  const load = useCallback(async (targetPage = 1, overrides = {}) => {
    const filters = { videoId, eventId, ...overrides };
    setLoading(true);
    setError(null);
    try {
      const res = await fetchEvents({
        page: targetPage,
        perPage: 50,
        videoId: filters.videoId.trim(),
        eventId: filters.eventId.trim(),
      });
      setEvents(res.events);
      setTotalPages(res.totalPages);
      setPage(res.page ?? targetPage);
    } catch (err) {
      console.error("fetchEvents failed:", err);
      setError("Không tải được dữ liệu sự kiện. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  }, [videoId, eventId]);

  useEffect(() => { load(1); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  function handleSubmit(e) {
    e.preventDefault();
    load(1);
  }

  function handleClear() {
    setVideoId("");
    setEventId("");
    setSelectorResetKey((k) => k + 1);
    load(1, { videoId: "", eventId: "" });
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
        <EventIDSelector eventId={eventId} onChange={setEventId} disabled={!isExactVideo} />

        <div className="ss-form-actions">
          <button type="submit" className="ss-btn ss-btn--primary" disabled={loading}>
            {loading ? "Đang tải..." : "Apply Filter"}
          </button>
          <button type="button" className="ss-btn ss-btn--ghost" onClick={handleClear}>
            Xoá filter
          </button>
        </div>
      </form>

      {error && <p className="ss-form-error">{error}</p>}

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
              onSearchSimilar={undefined}
            />
          ))}
        </div>
      )}

      <Pagination page={page} totalPages={totalPages} onChange={load} />
    </div>
  );
}