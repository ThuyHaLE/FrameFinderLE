// sceneseek-frontend/src/App.jsx

import { useState } from "react";
import { ModalProvider } from "./context/ModalContext";
import Layout from "./components/layout/Layout";
import HomePage from "./pages/HomePage";
import DataPage from "./pages/DataPage";
import EventPage from "./pages/EventPage";
import "./styles/theme.css";

const PAGES = {
  home: HomePage,
  data: DataPage,
  event: EventPage,
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
