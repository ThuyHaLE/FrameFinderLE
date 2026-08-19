// sceneseek-frontend/src/pages/DataPage.jsx

import { useState, useEffect, useCallback, useMemo } from "react";
import { fetchKeyframes } from "../api/client";
import GalleryItem from "../components/results/GalleryItem";
import Pagination from "../components/results/Pagination";
import SkeletonGrid from "../components/results/SkeletonGrid";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

// Fallback when NOT able to fetch /api/videos/l-options (or network error).
const FALLBACK_L_OPTIONS = Array.from({ length: 24 }, (_, i) =>
  String(i + 1).padStart(2, "0")
); // ["01", "02", ..., "24"]

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function parseTimestamp(ts) {
  try {
    const parts = ts.trim().split(":");
    const h = parseInt(parts[0], 10);
    const m = parseInt(parts[1], 10);
    const s = parts.length > 2 ? parseFloat(parts[2]) : 0;
    return h * 3600 + m * 60 + s;
  } catch {
    return null;
  }
}

const TIMESTAMP_RE = /^\d+:[0-5]\d(:[0-5]\d(\.\d+)?)?$/;

function validateTimestamp(ts) {
  if (!ts || !ts.trim()) return true;
  return TIMESTAMP_RE.test(ts.trim());
}

// ---------------------------------------------------------------------------
// TimestampInput
// ---------------------------------------------------------------------------

function TimestampInput({ id, label, value, onChange, placeholder = "hh:mm:ss", fallback = "00:00:00", disabled = false }) {
  function shift(delta) {
    if (disabled) return;
    const base = parseTimestamp(value);
    const startFrom = (base === null || isNaN(base))
      ? (parseTimestamp(fallback) ?? 0)
      : base;
    const next = Math.max(0, startFrom + delta);
    const h = Math.floor(next / 3600);
    const m = Math.floor((next % 3600) / 60);
    const s = Math.floor(next % 60);
    onChange([h, m, s].map((n) => String(n).padStart(2, "0")).join(":"));
  }

  function handlePaste(e) {
    if (disabled) return;
    e.preventDefault();
    onChange((e.clipboardData.getData("text") || "").trim());
  }

  return (
    <div className={`ss-form-group ss-form-group--inline${disabled ? " ss-form-group--disabled" : ""}`}>
      <label htmlFor={id}>{label}</label>
      <div className="ss-timestamp-row">
        <input
          id={id}
          type="text"
          value={value}
          placeholder={placeholder}
          onChange={(e) => onChange(e.target.value.trimStart())}
          onPaste={handlePaste}
          autoComplete="off"
          spellCheck={false}
          disabled={disabled}
        />
        <button type="button" className="ss-ts-btn" onClick={() => shift(1)}  title="+1s" disabled={disabled}>▲</button>
        <button type="button" className="ss-ts-btn" onClick={() => shift(-1)} title="-1s" disabled={disabled}>▼</button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// VideoIDSelector — L select + V text input → "L13_V001"
// ---------------------------------------------------------------------------

function VideoIDSelector({ videoId, onChange, lOptions }) {
  // Parse existing videoId back into L / V parts (e.g. "L13_V001" → "13", "001")
  const match = videoId.match(/^L(\d+)_V(\d+)$/);
  const [lPart, setLPart] = useState(match ? match[1] : "");
  const [vPart, setVPart] = useState(match ? match[2] : "");

  // Sync up to parent whenever either part changes
  useEffect(() => {
    if (lPart && vPart) {
      onChange(`L${lPart}_V${vPart.padStart(3, "0")}`); // exact: "L13_V001"
    } else if (lPart) {
      onChange(`L${lPart}`); // prefix: "L13" → backend get all V for this L
    } else {
      onChange(""); // no filter
    }
  }, [lPart, vPart]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleVChange(e) {
    const val = e.target.value.replace(/\D/g, "").slice(0, 3);
    setVPart(val);
  }

  // Preview label
  const previewLabel = lPart && vPart
    ? `→ L${lPart}_V${vPart.padStart(3, "0")}`
    : lPart
    ? `→ L${lPart}_V* (tất cả)`
    : null;

  return (
    <div className="ss-form-group">
      <label>Video ID</label>
      <div className="ss-videoid-row">
        {/* L part */}
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

        {/* V part — để trống = lấy tất cả V của L đã chọn */}
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

        {/* Preview */}
        {previewLabel && (
          <span className="ss-videoid-preview">{previewLabel}</span>
        )}

        {/* Clear */}
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
// DataPage
// ---------------------------------------------------------------------------

export default function DataPage() {
  const [videoId,     setVideoId]     = useState("");
  const [tsStart,     setTsStart]     = useState("");
  const [tsEnd,       setTsEnd]       = useState("");
  const [filterError, setFilterError] = useState(null);

  const [page,       setPage]       = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [keyframes,  setKeyframes]  = useState([]);
  const [loading,    setLoading]    = useState(false);

  // Bump to force VideoIDSelector remount (reset its internal lPart/vPart) when clearing filter —
  // because that component only reads videoId prop on mount, doesn't auto-sync when prop changes.
  const [selectorResetKey, setSelectorResetKey] = useState(0);

  // List of "L" for dropdown — fetch dynamically from backend (based on real video_IDs in JSON), 
  // fallback to FALLBACK_L_OPTIONS if fetch fails.
  const [lOptions, setLOptions] = useState(FALLBACK_L_OPTIONS);

  const isExactVideo = /^L\d+_V\d+$/.test(videoId.trim());

  useEffect(() => {
    if (!isExactVideo && (tsStart || tsEnd)) {
      setTsStart("");
      setTsEnd("");
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
        // keep the FALLBACK_L_OPTIONS if fetch fails
      });
    return () => { cancelled = true; };
  }, []);

  // Duration fallback for end timestamp: get timestamp of last frame in current video
  const endFallback = useMemo(() => {
    if (keyframes.length === 0) return "00:00:00";
    const last = keyframes.reduce((max, r) =>
      (r.timestamp_sec ?? 0) > (max.timestamp_sec ?? 0) ? r : max
    );
    return last.timestamp ?? "00:00:00";
  }, [keyframes]);

  // -------------------------------------------------------------------------
  // Validation
  // -------------------------------------------------------------------------

  function validate() {
    if (tsStart && !validateTimestamp(tsStart))
      return "Định dạng thời điểm bắt đầu không hợp lệ (hh:mm:ss[.SSS]).";
    if (tsEnd && !validateTimestamp(tsEnd))
      return "Định dạng thời điểm kết thúc không hợp lệ (hh:mm:ss[.SSS]).";
    if (tsStart && tsEnd) {
      const s = parseTimestamp(tsStart);
      const e = parseTimestamp(tsEnd);
      if (s !== null && e !== null && e <= s)
        return "Thời điểm kết thúc phải sau thời điểm bắt đầu.";
    }
    if ((tsStart || tsEnd) && !isExactVideo)
      return "Vui lòng chọn đúng 1 Video (cả L và V) khi lọc theo timestamp.";
    return null;
  }

  // -------------------------------------------------------------------------
  // Data loading
  // -------------------------------------------------------------------------

  const load = useCallback(async (targetPage = 1, overrides = {}) => {
    const filters = {
      videoId: videoId,
      tsStart: tsStart,
      tsEnd: tsEnd,
      ...overrides, // allow to call with new values immediately, avoid stale closure from state not updated yet
    };
    setLoading(true);
    try {
      const res = await fetchKeyframes({
        page: targetPage,
        perPage: 50,
        videoId: filters.videoId.trim(),
        timestamp: filters.tsStart.trim(),
        timestamp_end: filters.tsEnd.trim(),
      });
      setKeyframes(res.keyframes);
      setTotalPages(res.totalPages);
      // Use the page returned by backend (res.page) instead of trusting the original targetPage,
      // to avoid the case where targetPage exceeds the actual totalPages (e.g., changing filter reduces totalPages),
      // which would cause the UI to display page > totalPages like "100 / 50".
      setPage(res.page ?? targetPage);
    } finally {
      setLoading(false);
    }
  }, [videoId, tsStart, tsEnd]);

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
    setTsStart("");
    setTsEnd("");
    setFilterError(null);
    setSelectorResetKey((k) => k + 1); // force VideoIDSelector remount → delete selected lPart/vPart
    load(1, { videoId: "", tsStart: "", tsEnd: "" }); // reload immediately with cleared filter
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div className="ss-data-page">
      <h2>Data Overview</h2>

      <form className="ss-search-form" onSubmit={handleSubmit}>

        <VideoIDSelector key={selectorResetKey} videoId={videoId} onChange={setVideoId} lOptions={lOptions} />

        <div className="ss-form-row">
          <TimestampInput
            id="ts_start"
            label="Bắt đầu tại"
            value={tsStart}
            onChange={setTsStart}
            placeholder="hh:mm:ss[.SSS]"
            fallback="00:00:00"
            disabled={!isExactVideo}
          />
          <TimestampInput
            id="ts_end"
            label="Kết thúc tại"
            value={tsEnd}
            onChange={setTsEnd}
            placeholder="hh:mm:ss[.SSS]"
            fallback={endFallback}
            disabled={!isExactVideo}
          />
        </div>

        <p className="ss-form-hint">
          {isExactVideo
            ? <>Paste trực tiếp timestamp từ video player.
                {tsStart && !tsEnd && " Chỉ nhập Bắt đầu → frame gần nhất từ thời điểm đó."}
                {tsStart &&  tsEnd && " Hiển thị frame trong khoảng đã chọn."}
              </>
            : "Chọn đúng 1 Video (cả L và V) để lọc theo timestamp."}
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
      ) : keyframes.length === 0 ? (
        <p className="ss-results-status">Không tìm thấy frame nào phù hợp.</p>
      ) : (
        <div className="ss-gallery">
          {keyframes.map((item, i) => (
            <GalleryItem
              key={item.db_idx}
              item={item}
              allItems={keyframes}
              indexInList={i}
              showFeedback={false}
              readOnly
            />
          ))}
        </div>
      )}

      <Pagination page={page} totalPages={totalPages} onChange={load} />
    </div>
  );
}