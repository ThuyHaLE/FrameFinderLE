import { useEffect } from "react";
import { useModal } from "../../context/ModalContext";

export default function ImageModal() {
  const { images, index, open, closeModal, next, prev } = useModal();

  useEffect(() => {
    if (!open) return;
    function handleKey(e) {
      if (e.key === "Escape") closeModal();
      if (e.key === "ArrowRight") next();
      if (e.key === "ArrowLeft") prev();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, closeModal, next, prev]);

  if (!open || images.length === 0) return null;

  const current = images[index];

  return (
    <div className="ss-modal-backdrop" onClick={closeModal}>
      <div className="ss-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="ss-modal-close" onClick={closeModal} aria-label="Đóng">
          ×
        </button>
        <button className="ss-modal-nav ss-modal-nav--prev" onClick={prev} aria-label="Ảnh trước">
          ‹
        </button>
        <button className="ss-modal-nav ss-modal-nav--next" onClick={next} aria-label="Ảnh sau">
          ›
        </button>

        <img src={current.src} alt={current.frame_id} className="ss-modal-image" />

        <div className="ss-modal-meta">
          <span>{current.video_id}</span>
          <span>{current.frame_id}</span>
          <span>{current.timestamp}</span>
        </div>
      </div>
    </div>
  );
}
