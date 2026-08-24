// sceneseek-frontend/src/context/SearchContext.jsx

import { createContext, useContext, useState, useCallback, useRef } from "react";
import {
  DEFAULT_QUERY_TYPE_KEY,
  emptyFieldValues,
  getQueryType,
} from "../config/queryTypes";
import {
  searchByType,
  refineResults,
  sendFeedback,
  getKeywordSuggestions,
  getSimilarFrames,
} from "../api/client";

const SearchContext = createContext(null);

function newSessionId() {
  return `s_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export function SearchProvider({ children }) {
  const [activeTypeKey, setActiveTypeKey] = useState(DEFAULT_QUERY_TYPE_KEY);
  const [fieldValues, setFieldValues] = useState(emptyFieldValues(DEFAULT_QUERY_TYPE_KEY));

  const [useKeywords, setUseKeywords] = useState(false);
  const [keywords, setKeywords] = useState([]);

  const [k, setK] = useState(100);
  const [displayOption, setDisplayOption] = useState("sort_by_frame_index");
  const [strict, setStrict] = useState(true);
  const [minOccurrences, setMinOccurrences] = useState(null);
  const [imagesPerPage, setImagesPerPage] = useState(50);

  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalImages, setTotalImages] = useState(0);
  const [results, setResults] = useState([]);

  const [feedbackMap, setFeedbackMap] = useState({}); // { [db_idx]: 'like' | 'dislike' }
  const [sessionId, setSessionId] = useState(newSessionId());

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const activeType = getQueryType(activeTypeKey);

  // --- Similar-tab state (read-only) ---
  const [viewMode, setViewMode] = useState("search"); // 'search' | 'similar'
  const [similarQueryFrame, setSimilarQueryFrame] = useState(null);
  const [similarResults, setSimilarResults] = useState([]);
  const [similarPage, setSimilarPage] = useState(1);
  const [similarTotalPages, setSimilarTotalPages] = useState(1);
  const [similarTotalImages, setSimilarTotalImages] = useState(0);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [similarError, setSimilarError] = useState(null);

  // db_idx of the frame that was used to open the similar-tab. This is used to refetch similar results when changing pages.
  const similarDbIdxRef = useRef(null);

  const openSimilar = useCallback(async (dbIdx) => {
    // Ignore if already in similar-tab (to avoid search in similar-tab, which is not allowed)
    // (icon 🔍 is already hidden in readOnly mode, so this is just a precaution)
    if (viewMode === "similar") return;

    similarDbIdxRef.current = dbIdx;
    setSimilarLoading(true);
    setSimilarError(null);
    setViewMode("similar"); // move to similar-tab immediately, show loading in similar view

    try {
      const res = await getSimilarFrames(dbIdx, { page: 1 });
      setSimilarQueryFrame(res.queryFrame);
      setSimilarResults(res.results);
      setSimilarTotalImages(res.totalImages);
      setSimilarTotalPages(res.totalPages);
      setSimilarPage(res.page);
    } catch (e) {
      setSimilarError("Không thể tải các frame tương tự. Vui lòng thử lại.");
    } finally {
      setSimilarLoading(false);
    }
  }, [viewMode]);

  const changeSimilarPage = useCallback(async (nextPage) => {
    const dbIdx = similarDbIdxRef.current;
    if (dbIdx == null) return;

    setSimilarLoading(true);
    setSimilarError(null);
    try {
      const res = await getSimilarFrames(dbIdx, { page: nextPage });
      setSimilarResults(res.results);
      setSimilarTotalImages(res.totalImages);
      setSimilarTotalPages(res.totalPages);
      setSimilarPage(res.page);
    } catch (e) {
      setSimilarError("Không thể chuyển trang. Vui lòng thử lại.");
    } finally {
      setSimilarLoading(false);
    }
  }, []);

  // Exit similar-tab = restore the original search snapshot intact.
  // Since openSimilar does NOT touch the search results/page/... state, 
  // we can just switch viewMode back to "search" to restore the original search snapshot.
  const closeSimilar = useCallback(() => {
    setViewMode("search");
    similarDbIdxRef.current = null;
    setSimilarQueryFrame(null);
    setSimilarResults([]);
    setSimilarError(null);
  }, []);

  const selectType = useCallback((typeKey) => {
    setActiveTypeKey(typeKey);
    setFieldValues(emptyFieldValues(typeKey));
    setKeywords([]);
    setStrict(true);          
    setMinOccurrences(null);  
  }, []);

  const updateField = useCallback((name, value) => {
    setFieldValues((prev) => ({ ...prev, [name]: value }));
  }, []);

  // [MỚI] List-field actions — used by fields of type "query_list" (e.g. Type 2's N ordered scenes)
  const updateListField = useCallback((name, index, value) => {
    setFieldValues((prev) => {
      const list = [...(prev[name] ?? [])];
      list[index] = value;
      return { ...prev, [name]: list };
    });
  }, []);

  const addListFieldItem = useCallback((name, max) => {
    setFieldValues((prev) => {
      const list = prev[name] ?? [];
      if (list.length >= max) return prev;
      return { ...prev, [name]: [...list, ""] };
    });
  }, []);

  const removeListFieldItem = useCallback((name, index, min) => {
    setFieldValues((prev) => {
      const list = prev[name] ?? [];
      if (list.length <= min) return prev;
      const nextList = list.filter((_, i) => i !== index);

      // Clamp strict/minOccurrences khi số cảnh giảm xuống < 3
      // (tránh gửi combo invalid lên backend, khiến event-boundary trả 422
      //  và client.js âm thầm fallback sang mock)
      const n = nextList.length;
      if (n < 3) {
        setStrict(true);
        setMinOccurrences(null);
      } else {
        setMinOccurrences((prevMin) =>
          prevMin != null && (prevMin < 2 || prevMin > n - 1) ? null : prevMin
        );
      }

      return { ...prev, [name]: nextList };
    });
  }, []);

  // Debounced-by-caller keyword fetch — call this from the input's onChange handler.
  const refreshKeywordSuggestions = useCallback(async (text) => {
    if (!useKeywords) return;
    const suggestions = await getKeywordSuggestions(text);
    setKeywords((prev) => Array.from(new Set([...prev, ...suggestions])));
  }, [useKeywords]);

  const removeKeyword = useCallback((kw) => {
    setKeywords((prev) => prev.filter((k2) => k2 !== kw));
  }, []);

  const addKeyword = useCallback((kw) => {
    if (!kw) return;
    setKeywords((prev) => (prev.includes(kw) ? prev : [...prev, kw]));
  }, []);

  const clearKeywords = useCallback(() => setKeywords([]), []);

  // [MỚI] isQueryEmpty giờ hiểu cả field kiểu array (query_list), không chỉ string
  const isQueryEmpty = useCallback(() => {
    const hasFieldText = Object.values(fieldValues).some((v) =>
      Array.isArray(v) ? v.some((item) => item && item.trim()) : v && v.trim()
    );
    return !hasFieldText && keywords.length === 0;
  }, [fieldValues, keywords]);

  const runSearch = useCallback(async ({ resetPage = true } = {}) => {
    if (isQueryEmpty()) {
      setError("Vui lòng nhập mô tả hoặc thêm keyword trước khi tìm kiếm.");
      return;
    }
    setError(null);
    setLoading(true);
    const nextPage = resetPage ? 1 : page;
    const newSession = resetPage ? newSessionId() : sessionId;
    if (resetPage) {
      setSessionId(newSession);
      setFeedbackMap({});
    }
    try {
      const res = await searchByType(activeTypeKey, fieldValues, {
        keywords, k, displayOption, page: nextPage, imagesPerPage,
        sessionId: newSession,
        strict, minOccurrences,
      });
      setResults(res.results);
      setTotalImages(res.totalImages);
      setTotalPages(res.totalPages);
      setPage(nextPage);
    } catch (e) {
      setError("Không thể lấy kết quả. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  }, [activeTypeKey, fieldValues, keywords, k, displayOption, imagesPerPage, page, sessionId, isQueryEmpty]);

  const changePage = useCallback(async (nextPage) => {
    setLoading(true);
    try {
      const hasFeedback = Object.keys(feedbackMap).length > 0;
      const fn = hasFeedback ? refineResults : searchByType;
      const res = await fn(activeTypeKey, fieldValues, {
        keywords,
        k,
        displayOption,
        page: nextPage,
        imagesPerPage,
        sessionId,
        strict, minOccurrences,          
      });
      setResults(res.results);
      setTotalImages(res.totalImages);
      setTotalPages(res.totalPages);
      setPage(nextPage);
    } catch (e) {
      setError("Không thể chuyển trang. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  }, [activeTypeKey, fieldValues, keywords, k, displayOption, imagesPerPage, sessionId, feedbackMap, strict, minOccurrences]);

  const setFeedback = useCallback(async (dbIdx, action) => {
    setFeedbackMap((prev) => ({ ...prev, [dbIdx]: action }));
    setResults((prev) =>
      prev.map((r) => (r.db_idx === dbIdx ? { ...r, feedback: action } : r))
    );
    try {
      await sendFeedback(dbIdx, action, sessionId);
    } catch (e) {
      // Non-fatal — feedback is best-effort; UI already reflects the click.
    }
  }, [sessionId]);

  const refine = useCallback(async () => {
    setLoading(true);
    try {
      const res = await refineResults(activeTypeKey, fieldValues, {
        keywords,
        k,
        displayOption,
        page: 1,
        imagesPerPage,
        sessionId,
        strict, minOccurrences,          // [THIẾU]
      });
      setResults(res.results);
      setTotalImages(res.totalImages);
      setTotalPages(res.totalPages);
      setPage(1);
    } catch (e) {
      setError("Không thể refine kết quả. Vui lòng thử lại.");
    } finally {
      setLoading(false);
    }
  }, [activeTypeKey, fieldValues, keywords, k, displayOption, imagesPerPage, sessionId, strict, minOccurrences]);

  const value = {
    activeTypeKey,
    activeType,
    selectType,
    fieldValues,
    updateField,
    updateListField,        
    addListFieldItem,       
    removeListFieldItem,
    strict, setStrict,
    minOccurrences, setMinOccurrences,    
    useKeywords,
    setUseKeywords,
    keywords,
    refreshKeywordSuggestions,
    addKeyword,
    removeKeyword,
    clearKeywords,
    k,
    setK,
    displayOption,
    setDisplayOption,
    imagesPerPage,
    setImagesPerPage,
    page,
    totalPages,
    totalImages,
    results,
    runSearch,
    changePage,
    refine,
    feedbackMap,
    setFeedback,
    loading,
    error,
    viewMode,
    openSimilar,
    closeSimilar,
    changeSimilarPage,
    similarQueryFrame,
    similarResults,
    similarPage,
    similarTotalPages,
    similarTotalImages,
    similarLoading,
    similarError,
  };

  return <SearchContext.Provider value={value}>{children}</SearchContext.Provider>;
}

export function useSearchContext() {
  const ctx = useContext(SearchContext);
  if (!ctx) throw new Error("useSearchContext must be used within SearchProvider");
  return ctx;
}