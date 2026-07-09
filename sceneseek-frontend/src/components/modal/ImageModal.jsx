import { useEffect } from "react";
import { useModal } from "../../context/ModalContext";

export default function ImageModal() {
  const { images, index, open, closeModal, next, prev } = useModal();

  useEffect(() => {
    if (!open) return;
    function handleKey(e) {
      if (e.key === "Escape")     closeModal();
      if (e.key === "ArrowRight") next();
      if (e.key === "ArrowLeft")  prev();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, closeModal, next, prev]);

  if (!open || images.length === 0) return null;

  const current = images[index];

  // Format timestamp: strip microseconds nếu có ("0:00:08.300000" → "0:00:08.3")
  function formatTimestamp(ts) {
    if (!ts) return "";
    return ts.replace(/(\.\d*?)0+$/, "$1").replace(/\.$/, "");
  }

  return (
    <div className="ss-modal-backdrop" onClick={closeModal}>
      <div className="ss-modal-content" onClick={(e) => e.stopPropagation()}>

        <button className="ss-modal-close" onClick={closeModal} aria-label="Đóng">×</button>
        <button className="ss-modal-nav ss-modal-nav--prev" onClick={prev} aria-label="Ảnh trước">‹</button>
        <button className="ss-modal-nav ss-modal-nav--next" onClick={next} aria-label="Ảnh sau">›</button>

        <img src={current.src} alt={current.frame_id} className="ss-modal-image" />

        {/* Primary: videoID | timestamp */}
        <div className="ss-modal-primary-meta">
          <span className="ss-modal-video-id">{current.video_id}</span>
          <span className="ss-modal-sep">|</span>
          <span className="ss-modal-timestamp">{formatTimestamp(current.timestamp)}</span>
        </div>

        {/* Secondary: frame_id + position counter */}
        <div className="ss-modal-secondary-meta">
          <span>{current.frame_id}</span>
          <span>{index + 1} / {images.length}</span>
        </div>

      </div>
    </div>
  );
}