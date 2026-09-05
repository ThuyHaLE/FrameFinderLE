// sceneseek-frontend/src/components/common/VideoIDSelector.jsx

import { useState, useEffect } from "react";

export default function VideoIDSelector({ videoId, onChange, lOptions }) {
  const match = videoId.match(/^L(\d+)_V(\d+)$/);
  const [lPart, setLPart] = useState(match ? match[1] : "");
  const [vPart, setVPart] = useState(match ? match[2] : "");

  useEffect(() => {
    if (lPart && vPart) {
      onChange(`L${lPart}_V${vPart.padStart(3, "0")}`);
    } else if (lPart) {
      onChange(`L${lPart}`);
    } else {
      onChange("");
    }
  }, [lPart, vPart]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleVChange(e) {
    const val = e.target.value.replace(/\D/g, "").slice(0, 3);
    setVPart(val);
  }

  const previewLabel = lPart && vPart
    ? `→ L${lPart}_V${vPart.padStart(3, "0")}`
    : lPart
    ? `→ L${lPart}_V* (tất cả)`
    : null;

  return (
    <div className="ss-form-group">
      <label>Video ID</label>
      <div className="ss-videoid-row">
        <select value={lPart} onChange={(e) => setLPart(e.target.value)} className="ss-videoid-select" aria-label="Chọn L">
          <option value="">-- L --</option>
          {lOptions.map((l) => <option key={l} value={l}>L{l}</option>)}
        </select>
        <span className="ss-videoid-sep">_</span>
        <div className="ss-videoid-v-wrap">
          <span className="ss-videoid-v-prefix">V</span>
          <input
            type="text"
            inputMode="numeric"
            value={vPart}
            onChange={handleVChange}
            placeholder="* (tất cả)"
            className="ss-videoid-v-input ss-videoid-v-input--wide"
            aria-label="Nhập số V (để trống = lấy tất cả V)"
            maxLength={3}
          />
        </div>
        {previewLabel && <span className="ss-videoid-preview">{previewLabel}</span>}
        {(lPart || vPart) && (
          <button type="button" className="ss-btn ss-btn--ghost" onClick={() => { setLPart(""); setVPart(""); }}>×</button>
        )}
      </div>
    </div>
  );
}