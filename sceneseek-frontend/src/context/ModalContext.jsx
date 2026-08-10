import { createContext, useContext, useState, useCallback } from "react";

const ModalContext = createContext(null);

export function ModalProvider({ children }) {
  const [images, setImages] = useState([]); // [{ src, video_id, frame_id, timestamp }]
  const [index, setIndex] = useState(0);
  const [open, setOpen] = useState(false);

  const openModal = useCallback((imageList, startIndex) => {
    setImages(imageList);
    setIndex(startIndex);
    setOpen(true);
  }, []);

  const closeModal = useCallback(() => setOpen(false), []);

  const next = useCallback(() => {
    setIndex((i) => (images.length === 0 ? 0 : (i + 1) % images.length));
  }, [images.length]);

  const prev = useCallback(() => {
    setIndex((i) => (images.length === 0 ? 0 : (i - 1 + images.length) % images.length));
  }, [images.length]);

  const value = { images, index, open, openModal, closeModal, next, prev };

  return <ModalContext.Provider value={value}>{children}</ModalContext.Provider>;
}

export function useModal() {
  const ctx = useContext(ModalContext);
  if (!ctx) throw new Error("useModal must be used within ModalProvider");
  return ctx;
}
