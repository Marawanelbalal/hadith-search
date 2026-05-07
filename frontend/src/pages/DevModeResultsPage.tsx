import { useState } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import { GradeMultiSelect } from '../components/GradeMultiSelect';
import { BookMultiSelect } from '../components/BookMultiSelect';
import HadithCard from '../components/HadithCard';
import { ModeToggle } from '../components/ModeToggle';
import { hadithCollection } from '../data/fakeData';
import type { HadithGrade, SearchAlgorithm } from '../types';

const DevModeResultsPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get('q') || 'prayer times';
  const gradeParams = searchParams.getAll('grade') as HadithGrade[];
  const bookParams = searchParams.getAll('book');
  const algorithmParam = searchParams.get('algorithm') as SearchAlgorithm | null;

  const [selectedGrades, setSelectedGrades] = useState<HadithGrade[]>(gradeParams);
  const [selectedBooks, setSelectedBooks] = useState<string[]>(bookParams);
  const [sortBy, setSortBy] = useState<'relevance' | 'authenticity'>('relevance');
  const [selectedAlgorithm, setSelectedAlgorithm] = useState<SearchAlgorithm>(algorithmParam || 'bm25-prf');
  const [isDevMode, setIsDevMode] = useState(true);

  const algorithms: { value: SearchAlgorithm; label: string }[] = [
    { value: 'bm25', label: 'BM25' },
    { value: 'bm25-prf', label: 'BM25 + PRF' },
    { value: 'tf-idf', label: 'TF-IDF' },
    { value: 'hybrid', label: 'Hybrid' },
  ];

  // Filter hadiths based on selections
  const filteredHadiths = hadithCollection.filter((h) => {
    if (selectedGrades.length > 0 && !selectedGrades.includes(h.grade)) return false;
    if (selectedBooks.length > 0 && !selectedBooks.some(book => h.book.toLowerCase().includes(book))) return false;
    return true;
  });

  // Sort hadiths
  const sortedHadiths = [...filteredHadiths].sort((a, b) => {
    if (sortBy === 'authenticity') {
      const gradeOrder: HadithGrade[] = ['sahih', 'hasan-sahih', 'hasan', 'daif-hasan', 'daif'];
      return gradeOrder.indexOf(a.grade) - gradeOrder.indexOf(b.grade);
    }
    return 0; // relevance - keep original order
  });

  const handleSearch = (newQuery: string) => {
    // In a real app, this would update the URL and trigger a new search
    console.log('Searching for:', newQuery, 'with algorithm:', selectedAlgorithm);
  };

  const handleModeToggle = () => {
    setIsDevMode(!isDevMode);
    navigate(isDevMode ? '/results' : '/results/dev');
  };

  const handleAlgorithmChange = (algorithm: SearchAlgorithm) => {
    setSelectedAlgorithm(algorithm);
    // In a real app, this would update the URL and trigger a new search
    console.log('Algorithm changed to:', algorithm);
  };

  return (
    <main className="flex-grow w-full max-w-[1200px] mx-auto px-margin-mobile md:px-margin-desktop py-8 flex flex-col gap-8 page-enter">
      {/* Header with mode toggle and algorithm selection */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h1 className="font-display-lg text-display-lg text-on-background dark:text-dark-on-background">
          Search Results
        </h1>
        <div className="flex flex-col md:flex-row items-start md:items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="font-ui-label text-ui-label text-on-surface-variant dark:text-dark-on-surface-variant">
              Algorithm:
            </span>
            <select
              className="bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg px-3 py-2 text-on-surface dark:text-dark-on-surface focus:ring-2 focus:ring-primary dark:focus:ring-dark-primary font-ui-label"
              value={selectedAlgorithm}
              onChange={(e) => handleAlgorithmChange(e.target.value as SearchAlgorithm)}
            >
              {algorithms.map((algo) => (
                <option key={algo.value} value={algo.value}>
                  {algo.label}
                </option>
              ))}
            </select>
          </div>
          <ModeToggle isDevMode={isDevMode} onToggle={handleModeToggle} />
        </div>
      </div>

      {/* Algorithm metadata */}
      <div className="bg-surface-container dark:bg-dark-surface-container rounded-lg p-4 border border-outline-variant dark:border-dark-outline-variant">
        <div className="flex items-center gap-2 mb-2">
          <span className="material-symbols-outlined text-primary dark:text-dark-primary text-sm">
            info
          </span>
          <span className="font-ui-label text-ui-label text-primary dark:text-dark-primary font-semibold">
            Algorithm: {algorithms.find(a => a.value === selectedAlgorithm)?.label}
          </span>
        </div>
        <p className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">
          Using {selectedAlgorithm.toUpperCase()} search algorithm. Results are generated using fake data for demonstration purposes.
        </p>
      </div>

      {/* Search bar */}
      <div className="w-full max-w-2xl">
        <SearchBar onSearch={handleSearch} compact placeholder={`Refine search: "${query}"`} />
      </div>

      {/* Filters row */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <GradeMultiSelect selectedGrades={selectedGrades} onSelectionChange={setSelectedGrades} />
        </div>
        <div className="flex-1">
          <BookMultiSelect selectedBooks={selectedBooks} onSelectionChange={setSelectedBooks} />
        </div>
      </div>

      {/* Results header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-surface-variant dark:border-dark-surface-variant pb-4">
        <p className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant uppercase tracking-wider">
          Showing {sortedHadiths.length} Result{sortedHadiths.length !== 1 ? 's' : ''} for &ldquo;{query}&rdquo;
        </p>
        <div className="flex items-center gap-4">
          <Link
            to="/dev"
            className="flex items-center gap-2 px-4 py-2 bg-primary dark:bg-dark-primary text-on-primary dark:text-dark-on-primary rounded-lg hover:bg-primary-container dark:hover:bg-dark-primary-container transition-colors font-ui-label text-ui-label"
          >
            <span className="material-symbols-outlined text-[18px]">
              compare_arrows
            </span>
            Compare Algorithms
          </Link>
          <div className="flex items-center gap-2 font-ui-label text-ui-label text-on-surface-variant dark:text-dark-on-surface-variant">
            <span>Sort by:</span>
            <select
              className="bg-transparent border-none text-on-surface dark:text-dark-on-surface focus:ring-0 cursor-pointer font-ui-label"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'relevance' | 'authenticity')}
            >
              <option value="relevance">Relevance</option>
              <option value="authenticity">Authenticity</option>
            </select>
          </div>
        </div>
      </div>

      {/* Results list */}
      <div className="flex flex-col gap-8">
        {sortedHadiths.map((hadith, index) => (
          <div
            key={hadith.id}
            className="animate-fade-in-up"
            style={{ animationDelay: `${index * 0.08}s` }}
          >
            <HadithCard hadith={hadith} />
          </div>
        ))}

        {sortedHadiths.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 gap-4">
            <span className="material-symbols-outlined text-[48px] text-outline-variant dark:text-dark-outline-variant">
              search_off
            </span>
            <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant text-center">
              No hadiths found matching your filters. Try adjusting your search criteria.
            </p>
          </div>
        )}
      </div>
    </main>
  );
};

export default DevModeResultsPage;
