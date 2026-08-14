// sceneseek-frontend/src/components/search/SearchOptions.jsx

import { useEffect } from "react";
import { useSearchContext } from "../../context/SearchContext";

export default function SearchOptions() {
  const {
    activeTypeKey,
    k,
    setK,
    displayOption,
    setDisplayOption,
    imagesPerPage,
    setImagesPerPage,
    refine,
    feedbackMap,
    loading,
  } = useSearchContext();

  const hasFeedback = Object.keys(feedbackMap).length > 0;
  const isBoundaryType = activeTypeKey === "event_boundary";

  useEffect(() => {
    if (isBoundaryType && displayOption !== "sort_by_frame_index") {
      setDisplayOption("sort_by_frame_index");
    }
  }, [isBoundaryType, displayOption, setDisplayOption]);

  return (
    <div className="ss-search-options">
      <div className="ss-form-group ss-form-group--inline">
        <label htmlFor="k_input">Số lượng kết quả (K)</label>
        <input
          id="k_input"
          type="number"
          min={1}
          value={k}
          onChange={(e) => setK(Number(e.target.value) || 1)}
        />
      </div>

      <div className="ss-form-group ss-form-group--inline">
        <label htmlFor="display_option">Sắp xếp theo</label>
        <select
          id="display_option"
          value={displayOption}
          onChange={(e) => setDisplayOption(e.target.value)}
          disabled={isBoundaryType}
          title={isBoundaryType ? "Cụm cảnh luôn hiển thị theo thứ tự frame" : undefined}
        >
          <option value="sort_by_frame_index">Thứ tự frame</option>
          <option value="group_by_videoid">Nhóm theo Video ID</option>
        </select>
      </div>

      <div className="ss-form-group ss-form-group--inline">
        <label htmlFor="images_per_page">Số ảnh/trang</label>
        <select
          id="images_per_page"
          value={imagesPerPage}
          onChange={(e) => setImagesPerPage(Number(e.target.value))}
        >
          {[10, 20, 30, 40, 50, 100].map((n) => (
            <option key={n} value={n}>
              {n}
            </option>
          ))}
        </select>
      </div>

      <button
        type="button"
        className="ss-btn ss-btn--secondary"
        onClick={refine}
        disabled={!hasFeedback || loading}
        title={hasFeedback ? "Tinh chỉnh kết quả theo feedback" : "Cần like/dislike trước khi refine"}
      >
        Refine
      </button>
    </div>
  );
}