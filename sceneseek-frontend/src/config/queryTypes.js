// sceneseek-frontend/src/config/queryTypes.js

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
    resultShape: "frame",
    supportsKeywords: true,
  },

  event_boundary: {
    id: 2,
    key: "event_boundary",
    label: "Sự kiện (nhiều cảnh mốc)",
    shortLabel: "Type 2",
    description: "Mô tả các cảnh mốc (keyframes) theo thứ tự thời gian của một sự kiện.",
    endpoint: "/api/search/event-boundary",
    fields: [
      {
        name: "queries",
        type: "query_list",
        min: 2,
        max: 5,
        default: 2,
        itemLabel: (i, total) => {
          if (i === 0) return "Cảnh bắt đầu";
          if (i === total - 1) return "Cảnh kết thúc";
          return `Cảnh mốc ${i + 1}`;
        },
        itemPlaceholder: "VD: hai xe máy va chạm tại giao lộ",
      },
    ],
    resultShape: "cluster",
    supportsKeywords: true,
    supportsApproximateMatch: true,
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
    resultShape: "cluster",
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
    if (f.type === "query_list") {
      acc[f.name] = Array.from({ length: f.default ?? f.min ?? 2 }, () => "");
    } else {
      acc[f.name] = "";
    }
    return acc;
  }, {});
}

export function canAddQueryItem(field, currentList) {
  return currentList.length < (field.max ?? Infinity);
}

export function canRemoveQueryItem(field, currentList) {
  return currentList.length > (field.min ?? 1);
}