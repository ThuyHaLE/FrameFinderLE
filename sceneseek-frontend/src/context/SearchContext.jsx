import { createContext, useContext, useState, useCallback } from "react";
import {
  DEFAULT_QUERY_TYPE_KEY,
  emptyFieldValues,
  getQueryType,
} from "../config/queryTypes";
import { searchByType, refineResults, sendFeedback, getKeywordSuggestions } from "../api/client";

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

  const selectType = useCallback((typeKey) => {
    setActiveTypeKey(typeKey);
    setFieldValues(emptyFieldValues(typeKey));
    setKeywords([]);
  }, []);

  const updateField = useCallback((name, value) => {
    setFieldValues((prev) => ({ ...prev, [name]: value }));
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

  const isQueryEmpty = useCallback(() => {
    const hasFieldText = Object.values(fieldValues).some((v) => v && v.trim());
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
        keywords,
        k,
        displayOption,
        page: nextPage,
        imagesPerPage,
        sessionId: newSession,
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
  }, [activeTypeKey, fieldValues, keywords, k, displayOption, imagesPerPage, sessionId, feedbackMap]);

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
  }, [activeTypeKey, fieldValues, keywords, k, displayOption, imagesPerPage, sessionId]);

  const value = {
    activeTypeKey,
    activeType,
    selectType,
    fieldValues,
    updateField,
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
  };

  return <SearchContext.Provider value={value}>{children}</SearchContext.Provider>;
}

export function useSearchContext() {
  const ctx = useContext(SearchContext);
  if (!ctx) throw new Error("useSearchContext must be used within SearchProvider");
  return ctx;
}
