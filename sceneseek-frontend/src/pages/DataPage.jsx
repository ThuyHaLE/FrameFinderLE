import { useState, useEffect, useCallback } from "react";
import { fetchKeyframes } from "../api/client";
import GalleryItem from "../components/results/GalleryItem";
import Pagination from "../components/results/Pagination";

const TIMESTAMP_PATTERN = /^([01]?\d|2[0-3]):[0-5]\d:[0-5]\d(\.\d{1,6})?$/;

export default function DataPage() {
  const [videoId, setVideoId] = useState("L01_V001");
  const [timestamp, setTimestamp] = useState("");
  const [timestampError, setTimestampError] = useState(null);

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [keyframes, setKeyframes] = useState([]);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async (targetPage = 1) => {
    if (timestamp && !videoId) {
      setTimestampError("Vui lòng nhập Video ID khi đã nhập Timestamp.");
      return;
    }
    setTimestampError(null);
    setLoading(true);
    try {
      const res = await fetchKeyframes({ page: targetPage, perPage: 50, videoId, timestamp });
      setKeyframes(res.keyframes);
      setTotalPages(res.totalPages);
      setPage(targetPage);
    } finally {
      setLoading(false);
    }
  }, [videoId, timestamp]);

  useEffect(() => {
    load(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSubmit(e) {
    e.preventDefault();
    if (timestamp && !TIMESTAMP_PATTERN.test(timestamp)) {
      setTimestampError("Định dạng timestamp phải là hh:mm:ss[.SSS]");
      return;
    }
    load(1);
  }

  function shiftTimestamp(deltaSeconds) {
    const [h = 0, m = 0, s = 0] = timestamp.split(":").map(Number);
    let total = h * 3600 + m * 60 + s + deltaSeconds;
    if (total < 0) total = 0;
    const hh = Math.floor(total / 3600);
    const mm = Math.floor((total % 3600) / 60);
    const ss = total % 60;
    setTimestamp(
      [hh, mm, ss].map((n) => String(n).padStart(2, "0")).join(":")
    );
  }

  return (
    <div className="ss-data-page">
      <h2>Data Overview</h2>

      <form className="ss-data-filter" onSubmit={handleSubmit}>
        <div className="ss-form-group ss-form-group--inline">
          <label htmlFor="video_ID">Video ID</label>
          <input
            id="video_ID"
            type="text"
            value={videoId}
            placeholder="L01_V001"
            onChange={(e) => setVideoId(e.target.value)}
          />
        </div>

        <div className="ss-form-group ss-form-group--inline">
          <label htmlFor="timestamp">Bắt đầu tại</label>
          <input
            id="timestamp"
            type="text"
            value={timestamp}
            placeholder="hh:mm:ss[.SSS]"
            onChange={(e) => setTimestamp(e.target.value)}
          />
          <button type="button" onClick={() => shiftTimestamp(1)}>▲</button>
          <button type="button" onClick={() => shiftTimestamp(-1)}>▼</button>
        </div>

        <button type="submit" className="ss-btn ss-btn--primary">
          Apply Filter
        </button>
      </form>

      {timestampError && <p className="ss-form-error">{timestampError}</p>}

      {loading ? (
        <p className="ss-results-status">Đang tải...</p>
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
