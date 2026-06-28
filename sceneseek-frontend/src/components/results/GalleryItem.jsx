import FeedbackButtons from "./FeedbackButtons";
import { useModal } from "../../context/ModalContext";

export default function GalleryItem({ item, allItems, indexInList, showFeedback = false }) {
  const { openModal } = useModal();

  function handleOpen() {
    const images = allItems.map((r) => ({
      src: r.thumbnail,
      video_id: r.video_id,
      frame_id: r.frame_id,
      timestamp: r.timestamp,
    }));
    openModal(images, indexInList);
  }

  return (
    <div className="ss-gallery-item">
      <div className="ss-gallery-item__index">
        {item.video_id} | {item.frame_id}
      </div>

      <button type="button" className="ss-gallery-item__image-btn" onClick={handleOpen}>
        <img src={item.thumbnail} alt={item.frame_id} loading="lazy" />
      </button>

      {showFeedback && <FeedbackButtons dbIdx={item.db_idx} feedback={item.feedback} />}
    </div>
  );
}
