// sceneseek-frontend/src/config/queryTypes.js

/**
 * Single source of truth for query types.
 *
 * Why this exists: in the old Jinja UI, "what fields to show" and
 * "what the query means" were implicit in the HTML template. Here,
 * every type is one config object — TypeSelector, SearchForm and the
 * API layer all read from this file instead of hardcoding type logic.
 *
 * To add a 4th query type later: add one entry below. No other file
 * needs to change.
 */

export const QUERY_TYPES = {
  frame: {
    id: 1,
    key: "frame",
    label: "Cảnh cụ thể",
    shortLabel: "Type 1",
    description: "Mô tả một khung cảnh / frame cụ thể bạn muốn tìm.",
    endpoint: "/api/search/frame",
    fields: [
      {
        name: "query",
        label: "Mô tả cảnh",
        placeholder: "VD: người phụ nữ mặc áo dài đỏ đứng trước cổng chợ Bến Thành",
        type: "textarea",
      },
    ],
    supportsKeywords: true,
  },

  event_boundary: {
    id: 2,
    key: "event_boundary",
    label: "Sự kiện (cảnh đầu – cảnh cuối)",
    shortLabel: "Type 2",
    description: "Mô tả cảnh bắt đầu và cảnh kết thúc của một sự kiện.",
    endpoint: "/api/search/event-boundary",
    fields: [
      {
        name: "start_query",
        label: "Cảnh bắt đầu",
        placeholder: "VD: hai xe máy va chạm tại giao lộ",
        type: "textarea",
      },
      {
        name: "end_query",
        label: "Cảnh kết thúc",
        placeholder: "VD: cảnh sát giao thông có mặt tại hiện trường",
        type: "textarea",
      },
    ],
    supportsKeywords: true,
  },

  event_mention: {
    id: 3,
    key: "event_mention",
    label: "Sự kiện được đề cập",
    shortLabel: "Type 3",
    description: "Mô tả một sự kiện được nói đến trong lời thoại / transcript.",
    endpoint: "/api/search/event-mention",
    fields: [
      {
        name: "query",
        label: "Mô tả sự kiện",
        placeholder: "VD: CEO thông báo về kết quả kinh doanh quý 4",
        type: "textarea",
      },
    ],
    supportsKeywords: true,
  },
};

export const QUERY_TYPE_LIST = Object.values(QUERY_TYPES);

export const DEFAULT_QUERY_TYPE_KEY = "frame";

export function getQueryType(key) {
  return QUERY_TYPES[key] ?? QUERY_TYPES[DEFAULT_QUERY_TYPE_KEY];
}

/** Empty form values shaped to a given type's fields — used to reset the form on type switch. */
export function emptyFieldValues(typeKey) {
  const type = getQueryType(typeKey);
  return type.fields.reduce((acc, f) => {
    acc[f.name] = "";
    return acc;
  }, {});
}
