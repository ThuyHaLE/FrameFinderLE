// sceneseek-frontend/src/components/search/SearchForm.jsx

import { useSearchContext } from "../../context/SearchContext";
import KeywordChips from "./KeywordChips";

function Field({ field, value, onChange, onBlur }) {
  if (field.type === "textarea") {
    return (
      <div className="ss-form-group" key={field.name}>
        <label htmlFor={field.name}>{field.label}</label>
        <textarea
          id={field.name}
          rows={2}
          placeholder={field.placeholder}
          value={value}
          onChange={(e) => onChange(field.name, e.target.value)}
          onBlur={(e) => onBlur(e.target.value)}
        />
      </div>
    );
  }

  // Fallback for any future field type added to config without a dedicated renderer.
  return (
    <div className="ss-form-group" key={field.name}>
      <label htmlFor={field.name}>{field.label}</label>
      <input
        id={field.name}
        type="text"
        placeholder={field.placeholder}
        value={value}
        onChange={(e) => onChange(field.name, e.target.value)}
        onBlur={(e) => onBlur(e.target.value)}
      />
    </div>
  );
}

export default function SearchForm() {
  const {
    activeType,
    fieldValues,
    updateField,
    runSearch,
    refreshKeywordSuggestions,
    loading,
    error,
  } = useSearchContext();

  function handleSubmit(e) {
    e.preventDefault();
    runSearch({ resetPage: true });
  }

  return (
    <form className="ss-search-form" onSubmit={handleSubmit}>
      {activeType.fields.map((field) => (
        <Field
          key={field.name}
          field={field}
          value={fieldValues[field.name] ?? ""}
          onChange={updateField}
          onBlur={(text) => refreshKeywordSuggestions(text)}
        />
      ))}

      {activeType.supportsKeywords && <KeywordChips />}

      {error && <p className="ss-form-error">{error}</p>}

      <div className="ss-form-actions">
        <button type="submit" className="ss-btn ss-btn--primary" disabled={loading}>
          {loading ? "Đang tìm..." : "Tìm kiếm"}
        </button>
      </div>
    </form>
  );
}
