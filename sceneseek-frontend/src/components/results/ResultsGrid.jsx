import { useSearchContext } from "../../context/SearchContext";
import GalleryItem from "./GalleryItem";

export default function ResultsGrid() {
  const { results, totalImages, loading } = useSearchContext();

  if (loading) {
    return <p className="ss-results-status">Đang tải kết quả...</p>;
  }

  if (results.length === 0) {
    return <p className="ss-results-status">Chưa có kết quả. Hãy nhập mô tả và tìm kiếm.</p>;
  }

  return (
    <div className="ss-results">
      <p className="ss-results-total">Tổng số kết quả: {totalImages}</p>
      <div className="ss-gallery">
        {results.map((item, i) => (
          <GalleryItem
            key={item.db_idx}
            item={item}
            allItems={results}
            indexInList={i}
            showFeedback
          />
        ))}
      </div>
    </div>
  );
}
