import { useSearchContext } from "../../context/SearchContext";

export default function FeedbackButtons({ dbIdx, feedback }) {
  const { setFeedback } = useSearchContext();

  function toggle(action) {
    // Clicking the active action again resets to neutral, like the old behavior.
    setFeedback(dbIdx, feedback === action ? null : action);
  }

  return (
    <div className="ss-feedback-buttons">
      <button
        type="button"
        className={`ss-feedback-btn ${feedback === "like" ? "ss-feedback-btn--active-like" : ""}`}
        onClick={() => toggle("like")}
        aria-pressed={feedback === "like"}
      >
        👍 Like
      </button>
      <button
        type="button"
        className={`ss-feedback-btn ${feedback === "dislike" ? "ss-feedback-btn--active-dislike" : ""}`}
        onClick={() => toggle("dislike")}
        aria-pressed={feedback === "dislike"}
      >
        👎 Dislike
      </button>
    </div>
  );
}
