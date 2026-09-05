// sceneseek-frontend/src/components/search/TypeSelector.jsx

import { QUERY_TYPE_LIST } from "../../config/queryTypes";
import { useSearchContext } from "../../context/SearchContext";

export default function TypeSelector() {
  const { activeTypeKey, selectType, viewMode } = useSearchContext();
  const isSimilarMode = viewMode === "similar";

  return (
    <div className="ss-type-selector" role="tablist" aria-label="Loại truy vấn">
      {QUERY_TYPE_LIST.map((type) => (
        <button
          key={type.key}
          role="tab"
          aria-selected={activeTypeKey === type.key}
          className={`ss-type-tab ${activeTypeKey === type.key ? "ss-type-tab--active" : ""}`}
          onClick={() => selectType(type.key)}
          disabled={isSimilarMode}
          title={isSimilarMode ? "Không thể đổi loại truy vấn khi đang xem frame tương tự" : undefined}
        >
          <span className="ss-type-tab__index">{type.shortLabel}</span>
          <span className="ss-type-tab__label">{type.label}</span>
        </button>
      ))}
      <p className="ss-type-description">
        {QUERY_TYPE_LIST.find((t) => t.key === activeTypeKey)?.description}
      </p>
    </div>
  );
}