// sceneseek-frontend/src/components/search/SearchForm.jsx

import { useSearchContext } from "../../context/SearchContext";
import { canAddQueryItem, canRemoveQueryItem } from "../../config/queryTypes";
import KeywordChips from "./KeywordChips";


function QueryListField({ field, value, onItemChange, onItemBlur, onAdd, onRemove }) {
  const list = value ?? [];

  return (
    <div className="ss-form-group ss-query-list" key={field.name}>
      {list.map((itemValue, i) => (
        <div className="ss-query-list__item" key={i}>
          <label htmlFor={`${field.name}-${i}`}>{field.itemLabel(i, list.length)}</label>
          <div className="ss-query-list__row">
            <textarea
              id={`${field.name}-${i}`}
              rows={2}
              placeholder={field.itemPlaceholder}
              value={itemValue}
              onChange={(e) => onItemChange(field.name, i, e.target.value)}
              onBlur={(e) => onItemBlur(e.target.value)}
            />
            {canRemoveQueryItem(field, list) && (
              <button
                type="button"
                className="ss-query-list__remove"
                aria-label="Xóa cảnh này"
                onClick={() => onRemove(field.name, i, field.min)}
              >
                ✕
              </button>
            )}
          </div>
        </div>
      ))}

      {canAddQueryItem(field, list) && (
        <button
          type="button"
          className="ss-query-list__add"
          onClick={() => onAdd(field.name, field.max)}
        >
          + Thêm cảnh ({list.length}/{field.max})
        </button>
      )}
    </div>
  );
}


function Field({ field, value, onChange, onBlur, listActions }) {
  if (field.type === "query_list") {
    return (
      <QueryListField
        field={field}
        value={value}
        onItemChange={listActions.updateListField}
        onItemBlur={onBlur}
        onAdd={listActions.addListFieldItem}
        onRemove={listActions.removeListFieldItem}
      />
    );
  }

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
    updateListField,
    addListFieldItem,
    removeListFieldItem,
    runSearch,
    refreshKeywordSuggestions,
    loading,
    error,
    viewMode,
  } = useSearchContext();

  const isSimilarMode = viewMode === "similar";

  function handleSubmit(e) {
    e.preventDefault();
    runSearch({ resetPage: true });
  }

  const listActions = { updateListField, addListFieldItem, removeListFieldItem };

  return (
    <form className="ss-search-form" onSubmit={handleSubmit}>
      <fieldset disabled={isSimilarMode} className="ss-form-fieldset">
        {activeType.fields.map((field) => (
          <Field
            key={field.name}
            field={field}
            value={fieldValues[field.name] ?? (field.type === "query_list" ? [] : "")}
            onChange={updateField}
            onBlur={(text) => refreshKeywordSuggestions(text)}
            listActions={listActions}
          />
        ))}

        {activeType.supportsKeywords && <KeywordChips />}

        {error && <p className="ss-form-error">{error}</p>}

        <div className="ss-form-actions">
          <button type="submit" className="ss-btn ss-btn--primary" disabled={loading}>
            {loading ? "Đang tìm..." : "Tìm kiếm"}
          </button>
        </div>
      </fieldset>
    </form>
  );
}