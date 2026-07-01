import { useState, useEffect, useCallback } from "react";
import { fetchKeyframes } from "../api/client";
import GalleryItem from "../components/results/GalleryItem";
import Pagination from "../components/results/Pagination";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Parse 'hh:mm:ss[.SSS]' hoặc 'h:mm:ss.ffffff' → giây (float) */
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

/**
 * Validate timestamp string.
 * Accept: hh:mm  |  hh:mm:ss  |  hh:mm:ss.SSS  |  h:mm:ss.ffffff
 */
const TIMESTAMP_RE = /^\d+:[0-5]\d(:[0-5]\d(\.\d+)?)?$/;

function validateTimestamp(ts) {
  if (!ts || !ts.trim()) return true; // empty = ok (optional field)
  return TIMESTAMP_RE.test(ts.trim());
}

// ---------------------------------------------------------------------------
// TimestampInput — input + ▲▼ buttons + paste-friendly
// ---------------------------------------------------------------------------

function TimestampInput({ id, label, value, onChange, placeholder = "hh:mm:ss" }) {
  function shift(delta) {
    const base = parseTimestamp(value);
    const next = Math.max(0, (base ?? 0) + delta);
    const h = Math.floor(next / 3600);
    const m = Math.floor((next % 3600) / 60);
    const s = Math.floor(next % 60);
    onChange([h, m, s].map((n) => String(n).padStart(2, "0")).join(":"));
  }

  function handleChange(e) {
    // strip leading/trailing whitespace that some video players add on copy
    onChange(e.target.value.trimStart());
  }

  function handlePaste(e) {
    // normalise pasted text immediately
    e.preventDefault();
    const pasted = (e.clipboardData.getData("text") || "").trim();
    onChange(pasted);
  }

  return (
    <div className="ss-form-group ss-form-group--inline">
      <label htmlFor={id}>{label}</label>
      <div className="ss-timestamp-row">
        <input
          id={id}
          type="text"
          value={value}
          placeholder={placeholder}
          onChange={handleChange}
          onPaste={handlePaste}
          autoComplete="off"
          spellCheck={false}
        />
        <button type="button" className="ss-ts-btn" onClick={() => shift(1)}  title="+1s">▲</button>
        <button type="button" className="ss-ts-btn" onClick={() => shift(-1)} title="-1s">▼</button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// DataPage
// ---------------------------------------------------------------------------

export default function DataPage() {
  const [videoId,      setVideoId]      = useState("");
  const [tsStart,      setTsStart]      = useState("");
  const [tsEnd,        setTsEnd]        = useState("");
  const [filterError,  setFilterError]  = useState(null);

  const [page,       setPage]       = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [keyframes,  setKeyframes]  = useState([]);
  const [loading,    setLoading]    = useState(false);

  // -------------------------------------------------------------------------
  // Validation
  // -------------------------------------------------------------------------

  function validate() {
    if (tsStart && !validateTimestamp(tsStart)) {
      return "Định dạng thời điểm bắt đầu không hợp lệ (hh:mm:ss[.SSS]).";
    }
    if (tsEnd && !validateTimestamp(tsEnd)) {
      return "Định dạng thời điểm kết thúc không hợp lệ (hh:mm:ss[.SSS]).";
    }
    if (tsStart && tsEnd) {
      const s = parseTimestamp(tsStart);
      const e = parseTimestamp(tsEnd);
      if (s !== null && e !== null && e <= s) {
        return "Thời điểm kết thúc phải sau thời điểm bắt đầu.";
      }
    }
    if ((tsStart || tsEnd) && !videoId.trim()) {
      return "Vui lòng nhập Video ID khi lọc theo timestamp.";
    }
    return null;
  }

  // -------------------------------------------------------------------------
  // Data loading
  // -------------------------------------------------------------------------

  const load = useCallback(async (targetPage = 1) => {
    setLoading(true);
    try {
      const res = await fetchKeyframes({
        page: targetPage,
        perPage: 50,
        videoId: videoId.trim(),
        timestamp: tsStart.trim(),
        timestamp_end: tsEnd.trim(),
      });
      setKeyframes(res.keyframes);
      setTotalPages(res.totalPages);
      setPage(targetPage);
    } finally {
      setLoading(false);
    }
  }, [videoId, tsStart, tsEnd]);

  // Load on mount (shows first 50 frames from mock/real)
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
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <div className="ss-data-page">
      <h2>Data Overview</h2>

      <form className="ss-search-form" onSubmit={handleSubmit}>

        {/* Video ID */}
        <div className="ss-form-group">
          <label htmlFor="video_ID">Video ID</label>
          <input
            id="video_ID"
            type="text"
            value={videoId}
            placeholder="VD: L13_V001"
            onChange={(e) => setVideoId(e.target.value)}
          />
        </div>

        {/* Timestamp range */}
        <div className="ss-form-row">
          <TimestampInput
            id="ts_start"
            label="Bắt đầu tại"
            value={tsStart}
            onChange={setTsStart}
            placeholder="hh:mm:ss[.SSS]"
          />
          <TimestampInput
            id="ts_end"
            label="Kết thúc tại"
            value={tsEnd}
            onChange={setTsEnd}
            placeholder="hh:mm:ss[.SSS]"
          />
        </div>

        <p className="ss-form-hint">
          Paste trực tiếp timestamp từ video player. Chỉ lọc theo timestamp khi đã nhập Video ID.
          {tsStart && !tsEnd && " Nếu chỉ nhập Bắt đầu, kết quả được sắp xếp từ frame gần nhất."}
          {tsStart &&  tsEnd && " Hiển thị các frame nằm trong khoảng đã chọn."}
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
        <p className="ss-results-status">Đang tải...</p>
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
            />
          ))}
        </div>
      )}

      <Pagination page={page} totalPages={totalPages} onChange={load} />
    </div>
  );
}