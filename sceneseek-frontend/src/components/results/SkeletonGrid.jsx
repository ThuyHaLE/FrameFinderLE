// sceneseek-frontend/src/components/results/SkeletonGrid.jsx

/**
 * Placeholder grid shown while gallery results are loading.
 * Renders `count` gray shimmer boxes matching .ss-gallery-item layout,
 * instead of a plain "Đang tải..." text.
 */
export default function SkeletonGrid({ count = 12 }) {
  return (
    <div className="ss-gallery" aria-busy="true" aria-label="Đang tải kết quả">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="ss-gallery-item ss-skeleton-item">
          <div className="ss-skeleton-shimmer" />
        </div>
      ))}
    </div>
  );
}