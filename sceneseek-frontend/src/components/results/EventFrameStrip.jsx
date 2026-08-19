// sceneseek-frontend/src/components/results/EventFrameStrip.jsx

import FeedbackButtons from "./FeedbackButtons";
import { useModal } from "../../context/ModalContext";

export default function EventFrameStrip({ frames, onSearchSimilar }) {
  const { openModal } = useModal();

  function openFrame(indexInEvent) {
    const images = frames.map((f) => ({
      src: f.thumbnail,
      video_id: f.video_id,
      frame_idx: f.frame_idx,
      timestamp: f.timestamp,
    }));
    openModal(images, indexInEvent);
  }

  function handleSearchSimilar(e, dbIdx) {
    e.stopPropagation();
    onSearchSimilar?.(dbIdx);
  }

  return (
    <div className="ss-cluster-item__strip">
      {frames.map((frame, i) => (
        <div className="ss-cluster-frame" key={frame.db_idx}>
          <div className="ss-gallery-item__image-wrap">
            <button type="button" className="ss-gallery-item__image-btn" onClick={() => openFrame(i)}>
              <img src={frame.thumbnail} alt={frame.frame_idx} loading="lazy" />
            </button>

            <button
              type="button"
              aria-label="Tìm frame tương tự"
              className="ss-gallery-item__similar-btn"
              onClick={(e) => handleSearchSimilar(e, frame.db_idx)}
            >
              🔍
            </button>
          </div>
          <FeedbackButtons dbIdx={frame.db_idx} feedback={frame.feedback} />
        </div>
      ))}
    </div>
  );
}