// sceneseek-frontend/src/components/results/Pagination.jsx

import { useState, useEffect } from "react";

export default function Pagination({ page, totalPages, onChange }) {
  const [draft, setDraft] = useState(String(page));

  // Sync draft when page changes from outside (e.g., new filter resets to page 1)
  useEffect(() => {
    setDraft(String(page));
  }, [page]);

  if (totalPages <= 1) return null;

  function jump() {
    const n = parseInt(draft, 10);
    if (!isNaN(n) && n >= 1 && n <= totalPages && n !== page) {
      onChange(n);
    } else {
      // If input is invalid → reset to current page
      setDraft(String(page));
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter") jump();
  }

  return (
    <div className="ss-pagination">
      <button disabled={page <= 1} onClick={() => onChange(page - 1)}>
        ‹ Trước
      </button>

      {/* Jump input */}
      <div className="ss-pagination-jump">
        <input
          type="text"
          inputMode="numeric"
          value={draft}
          onChange={(e) => setDraft(e.target.value.replace(/\D/g, ""))}
          onBlur={jump}
          onKeyDown={handleKeyDown}
          aria-label="Nhảy đến trang"
        />
        <span className="ss-pagination-total">/ {totalPages}</span>
      </div>

      <button disabled={page >= totalPages} onClick={() => onChange(page + 1)}>
        Sau ›
      </button>
    </div>
  );
}