// sceneseek-frontend/src/components/common/EventIdInput.jsx

export default function EventIdInput({ id, label, value, onChange, disabled = false }) {
  function shift(delta) {
    if (disabled) return;
    const base = parseInt(value, 10);
    const next = Math.max(0, (isNaN(base) ? 0 : base) + delta);
    onChange(String(next));
  }

  function handleChange(e) {
    onChange(e.target.value.replace(/\D/g, "")); // chỉ số nguyên không âm
  }

  return (
    <div className={`ss-form-group ss-form-group--inline${disabled ? " ss-form-group--disabled" : ""}`}>
      <label htmlFor={id}>{label}</label>
      <div className="ss-timestamp-row">
        <input
          id={id}
          type="text"
          inputMode="numeric"
          value={value}
          placeholder="event_id"
          onChange={handleChange}
          autoComplete="off"
          disabled={disabled}
        />
        <button type="button" className="ss-ts-btn" onClick={() => shift(1)} title="+1" disabled={disabled}>▲</button>
        <button type="button" className="ss-ts-btn" onClick={() => shift(-1)} title="-1" disabled={disabled}>▼</button>
      </div>
    </div>
  );
}