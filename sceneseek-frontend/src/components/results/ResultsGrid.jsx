// sceneseek-frontend/src/components/results/ResultsGrid.jsx

import { useSearchContext } from "../../context/SearchContext";
import GalleryItem from "./GalleryItem";
import ClusterGalleryItem from "./ClusterGalleryItem";
import Pagination from "./Pagination";

export default function ResultsGrid() {
  const {
    viewMode,
    results,
    totalImages,
    loading,
    page,
    totalPages,
    changePage,
    openSimilar,
    closeSimilar,
    similarQueryFrame,
    similarResults,
    similarTotalImages,
    similarLoading,
    similarError,
    similarPage,
    similarTotalPages,
    changeSimilarPage,
  } = useSearchContext();

  if (viewMode === "similar") {
    return (
      <div className="ss-results ss-results--similar">
        <div className="ss-similar-header">
          <button type="button" className="ss-similar-back" onClick={closeSimilar}>
            ← Quay lại kết quả tìm kiếm
          </button>
          {similarQueryFrame && (
            <p className="ss-results-total">
              Frame tương tự với {similarQueryFrame.video_id} | {similarQueryFrame.frame_idx}
              {" — "}Tổng số: {similarTotalImages}
            </p>
          )}
        </div>

        {similarLoading && <p className="ss-results-status">Đang tải...</p>}
        {similarError && <p className="ss-results-status ss-results-status--error">{similarError}</p>}

        {!similarLoading && !similarError && (
          <>
            <div className="ss-gallery">
              {similarResults.map((item, i) => (
                <GalleryItem
                  key={item.db_idx}
                  item={item}
                  allItems={similarResults}
                  indexInList={i}
                  showFeedback={false}
                  readOnly
                />
              ))}
            </div>
            <Pagination page={similarPage} totalPages={similarTotalPages} onChange={changeSimilarPage} />
          </>
        )}
      </div>
    );
  }

  if (loading) return <p className="ss-results-status">Đang tải kết quả...</p>;
  if (results.length === 0) {
    return <p className="ss-results-status">Chưa có kết quả. Hãy nhập mô tả và tìm kiếm.</p>;
  }

  const isClusterResults = Boolean(results[0]?.frames && results[0]?.video_id);

  if (isClusterResults) {
    return (
      <div className="ss-results">
        <p className="ss-results-total">Tổng số cụm cảnh: {totalImages}</p>
        <div className="ss-cluster-list">
          {results.map((cluster) => (
            <ClusterGalleryItem key={cluster.video_id} cluster={cluster} onSearchSimilar={openSimilar} />
          ))}
        </div>
        <Pagination page={page} totalPages={totalPages} onChange={changePage} />
      </div>
    );
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
            onSearchSimilar={openSimilar}
          />
        ))}
      </div>
      <Pagination page={page} totalPages={totalPages} onChange={changePage} />
    </div>
  );
}