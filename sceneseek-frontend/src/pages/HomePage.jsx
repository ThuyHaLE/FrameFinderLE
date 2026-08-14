// sceneseek-frontend/src/pages/HomePage.jsx

import { SearchProvider } from "../context/SearchContext";
import TypeSelector from "../components/search/TypeSelector";
import SearchForm from "../components/search/SearchForm";
import SearchOptions from "../components/search/SearchOptions";
import ResultsGrid from "../components/results/ResultsGrid";

function HomeContent() {
  return (
    <div className="ss-home">
      <TypeSelector />
      <SearchForm />
      <SearchOptions />
      <ResultsGrid />
    </div>
  );
}

export default function HomePage() {
  return (
    <SearchProvider>
      <HomeContent />
    </SearchProvider>
  );
}