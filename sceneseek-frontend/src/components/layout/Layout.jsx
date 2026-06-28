import Navbar from "./Navbar";
import ImageModal from "../modal/ImageModal";

export default function Layout({ activePage, onNavigate, children }) {
  return (
    <div className="ss-app">
      <Navbar activePage={activePage} onNavigate={onNavigate} />
      <main className="ss-main">{children}</main>
      <ImageModal />
    </div>
  );
}
