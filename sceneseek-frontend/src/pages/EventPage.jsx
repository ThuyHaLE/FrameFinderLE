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

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);

  // Bump to force VideoIDSelector remount (reset internal lPart/vPart) on clear —
  // same workaround as DataPage, see its comment for why.
  const [selectorResetKey, setSelectorResetKey] = useState(0);

  const [lOptions, setLOptions] = useState(FALLBACK_L_OPTIONS);

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
  // Data loading
  // -------------------------------------------------------------------------

  const load = useCallback(async (targetPage = 1, overrides = {}) => {
    const filters = { videoId, ...overrides };
    setLoading(true);
    try {
      const res = await fetchEvents({
        page: targetPage,
        perPage: 50,
        videoId: filters.videoId.trim(),
      });
      setEvents(res.events);
      setTotalPages(res.totalPages);
      // Trust backend's returned page, same reasoning as DataPage:
      // avoids UI showing page > totalPages after a filter shrinks the result set.
      setPage(res.page ?? targetPage);
    } finally {
      setLoading(false);
    }
  }, [videoId]);

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
    setSelectorResetKey((k) => k + 1);
    load(1, { videoId: "" });
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
              // no search-similar action in browse mode — same readOnly intent
              // as DataPage's GalleryItem readOnly usage
              onSearchSimilar={undefined}
            />
          ))}
        </div>
      )}

      <Pagination page={page} totalPages={totalPages} onChange={load} />
    </div>
  );
}