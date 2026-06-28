import { SearchProvider } from "../context/SearchContext";
import TypeSelector from "../components/search/TypeSelector";
import SearchForm from "../components/search/SearchForm";
import SearchOptions from "../components/search/SearchOptions";
import ResultsGrid from "../components/results/ResultsGrid";
import Pagination from "../components/results/Pagination";
import { useSearchContext } from "../context/SearchContext";

function HomeContent() {
  const { page, totalPages, changePage } = useSearchContext();

  return (
    <div className="ss-home">
      <TypeSelector />
      <SearchForm />
      <SearchOptions />
      <ResultsGrid />
      <Pagination page={page} totalPages={totalPages} onChange={changePage} />
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
