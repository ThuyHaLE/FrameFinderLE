// sceneseek-frontend/src/components/results/VideoGroupItem.jsx

import EventFrameStrip from "./EventFrameStrip";

export default function VideoGroupItem({ videoId, events, onSearchSimilar }) {
  const safeEvents = (events || []).filter((ev) => Array.isArray(ev.frames) && ev.frames.length > 0);
  if (safeEvents.length === 0) return null;
  const totalFrames = safeEvents.reduce((sum, e) => sum + (e.frame_count ?? e.frames.length), 0);

  return (
    <div className="ss-video-group">
      <div className="ss-video-group__header">
        <span className="ss-video-group__video">{videoId}</span>
        <span className="ss-video-group__count">
          {totalFrames} frame{events.length > 1 ? ` · ${events.length} sự kiện` : ""}
        </span>
      </div>

      {events.map((ev, i) => (
        <div
          className="ss-video-group__event"
          key={`${videoId}-${ev.start ?? "na"}-${ev.frames[0]?.db_idx ?? i}`}
        >
          {/* Type 3 only — event-boundary clusters don't have `text` */}
          {ev.text && (
            <p className="ss-cluster-item__text">
              {ev.start != null && ev.end != null && (
                <span className="ss-cluster-item__meta">
                  {ev.start.toFixed(1)}s – {ev.end.toFixed(1)}s
                </span>
              )}
              {" — "}
              {ev.text}
            </p>
          )}
          <EventFrameStrip frames={ev.frames} onSearchSimilar={onSearchSimilar} />
        </div>
      ))}
    </div>
  );
}