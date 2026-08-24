// sceneseek-frontend/src/components/results/ResultsGrid.jsx

import { useSearchContext } from "../../context/SearchContext";
import GalleryItem from "./GalleryItem";
import VideoGroupItem from "./VideoGroupItem";
import Pagination from "./Pagination";
import SkeletonGrid from "./SkeletonGrid";
import { groupClustersByVideo } from "../../utils/clusterGrouping";

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
    imagesPerPage,
    activeType,
    fieldValues,
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

        {similarLoading && <SkeletonGrid count={imagesPerPage} />}
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

  if (loading) return <SkeletonGrid count={imagesPerPage} />;
  if (results.length === 0) {
    return <p className="ss-results-status">Chưa có kết quả. Hãy nhập mô tả và tìm kiếm.</p>;
  }

  const isClusterResults = Boolean(results[0]?.frames && results[0]?.video_id);

  if (isClusterResults) {
    // Group the flat cluster/event list (from event-boundary or event-mention)
    // by video_id so a video with multiple events (common for event-mention,
    // since it dedupes by (video_id, event_id) rather than 1 cluster per video)
    // renders as one header with all its events underneath, instead of
    // duplicate video headers / duplicate React keys.
    const groups = groupClustersByVideo(results);
    const queryField = activeType.fields.find((f) => f.type === "query_list");
    const totalChannels = queryField ? (fieldValues[queryField.name]?.length ?? 0) : 0;

    function getMatchedChannelsLabel(cluster) {
      if (!queryField || !Array.isArray(cluster.matched_channels)) return null;
      const labels = cluster.matched_channels.map((idx) =>
        queryField.itemLabel(idx, totalChannels)
      );
      return `Khớp với: ${labels.join(", ")}`;
    }

    function getMissingChannelsLabel(cluster) {
      if (!queryField || !Array.isArray(cluster.missing_channels) || cluster.missing_channels.length === 0) {
        return null;
      }
      const labels = cluster.missing_channels.map((m) =>
        queryField.itemLabel(m.channel, totalChannels)
      );
      return `(thiếu: ${labels.join(", ")})`;
    }
        
    return (
      <div className="ss-results">
        <p className="ss-results-total">Tổng số cụm cảnh: {totalImages}</p>
        <div className="ss-cluster-list">
          {groups.map((g) => (
            <VideoGroupItem
              key={g.video_id}
              videoId={g.video_id}
              events={g.events}
              onSearchSimilar={openSimilar}
              getMatchedChannelsLabel={getMatchedChannelsLabel} 
              getMissingChannelsLabel={getMissingChannelsLabel}
            />
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