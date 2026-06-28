import { useState } from "react";
import { useSearchContext } from "../../context/SearchContext";

export default function KeywordChips() {
  const {
    useKeywords,
    setUseKeywords,
    keywords,
    addKeyword,
    removeKeyword,
    clearKeywords,
  } = useSearchContext();

  const [draft, setDraft] = useState("");

  function handleKeyDown(e) {
    if (e.key === "Enter") {
      e.preventDefault();
      addKeyword(draft.trim());
      setDraft("");
    }
  }

  return (
    <div className="ss-form-group">
      <label className="ss-checkbox-label">
        <input
          type="checkbox"
          checked={useKeywords}
          onChange={(e) => setUseKeywords(e.target.checked)}
        />
        Gợi ý keyword liên quan (keyword graph)
      </label>

      {useKeywords && (
        <>
          <div className="ss-chip-row">
            {keywords.map((kw) => (
              <button
                key={kw}
                type="button"
                className="ss-chip"
                onClick={() => removeKeyword(kw)}
                title="Bấm để xoá"
              >
                {kw} <span className="ss-chip__remove">×</span>
              </button>
            ))}
            <input
              type="text"
              className="ss-chip-input"
              placeholder="Thêm keyword..."
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKeyDown}
            />
          </div>
          {keywords.length > 0 && (
            <button type="button" className="ss-btn ss-btn--ghost" onClick={clearKeywords}>
              Xoá tất cả
            </button>
          )}
        </>
      )}
    </div>
  );
}
