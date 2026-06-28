import { useState } from "react";
import { ModalProvider } from "./context/ModalContext";
import Layout from "./components/layout/Layout";
import HomePage from "./pages/HomePage";
import DataPage from "./pages/DataPage";
import "./styles/theme.css";

const PAGES = {
  home: HomePage,
  data: DataPage,
};

export default function App() {
  const [activePage, setActivePage] = useState("home");
  const PageComponent = PAGES[activePage] ?? HomePage;

  return (
    <ModalProvider>
      <Layout activePage={activePage} onNavigate={setActivePage}>
        <PageComponent />
      </Layout>
    </ModalProvider>
  );
}
