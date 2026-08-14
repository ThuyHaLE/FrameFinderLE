// components/results/GalleryItem.jsx

import FeedbackButtons from "./FeedbackButtons";
import { useModal } from "../../context/ModalContext";

export default function GalleryItem({
  item,
  allItems,
  indexInList,
  showFeedback = false,
  readOnly = false,
  onSearchSimilar,
}) {
  const { openModal } = useModal();

  function handleOpen() {
    const images = allItems.map((r) => ({
      src: r.thumbnail,
      video_id: r.video_id,
      frame_idx: r.frame_idx,
      timestamp: r.timestamp,
    }));
    openModal(images, indexInList);
  }

  function handleSearchSimilar(e) {
    e.stopPropagation(); // avoid triggering handleOpen (opening modal) when clicking the icon
    onSearchSimilar?.(item.db_idx);
  }

  return (
    <div className="ss-gallery-item">
      <div className="ss-gallery-item__index">
        {item.video_id} | {item.frame_idx}
      </div>

      <div className="ss-gallery-item__image-wrap">
        <button type="button" className="ss-gallery-item__image-btn" onClick={handleOpen}>
          <img src={item.thumbnail} alt={item.frame_idx} loading="lazy" />
        </button>

        {!readOnly && (
          <button
            type="button"
            aria-label="Tìm frame tương tự"
            className="ss-gallery-item__similar-btn"
            onClick={handleSearchSimilar}
          >
            🔍
          </button>
        )}
      </div>

      {showFeedback && !readOnly && <FeedbackButtons dbIdx={item.db_idx} feedback={item.feedback} />}
    </div>
  );
}