import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import { GradeMultiSelect } from '../components/GradeMultiSelect';
import { BookMultiSelect } from '../components/BookMultiSelect';
import HadithCard from '../components/HadithCard';
import { ModeToggle } from '../components/ModeToggle';
import { hadithCollection } from '../data/fakeData';
import type { HadithGrade } from '../types';

// USER_MODE_ENDPOINT: Change this constant to swap the search algorithm used in User Mode
// Options: 'bm25', 'bm25-prf', 'tf-idf', 'hybrid'
const USER_MODE_ENDPOINT = 'bm25-prf';

const UserModeResultsPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const query = searchParams.get('q') || 'prayer times';
  const gradeParams = searchParams.getAll('grade') as HadithGrade[];
  const bookParams = searchParams.getAll('book');

  const [selectedGrades, setSelectedGrades] = useState<HadithGrade[]>(gradeParams);
  const [selectedBooks, setSelectedBooks] = useState<string[]>(bookParams);
  const [sortBy, setSortBy] = useState<'relevance' | 'authenticity'>('relevance');
  const [isDevMode, setIsDevMode] = useState(false);

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
    console.log('Searching for:', newQuery);
  };

  const handleModeToggle = () => {
    setIsDevMode(!isDevMode);
    navigate(isDevMode ? '/results' : '/results/dev');
  };

  return (
    <main className="flex-grow w-full max-w-[1200px] mx-auto px-margin-mobile md:px-margin-desktop py-8 flex flex-col gap-8 page-enter">
      {/* Header with mode toggle */}
      <div className="flex items-center justify-between">
        <h1 className="font-display-lg text-display-lg text-on-background dark:text-dark-on-background">
          Search Results
        </h1>
        <div className="flex items-center gap-4">
          <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">
            Algorithm: {USER_MODE_ENDPOINT.toUpperCase()}
          </span>
          <ModeToggle isDevMode={isDevMode} onToggle={handleModeToggle} />
        </div>
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
      <div className="flex items-center justify-between border-b border-surface-variant dark:border-dark-surface-variant pb-4">
        <p className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant uppercase tracking-wider">
          Showing {sortedHadiths.length} Result{sortedHadiths.length !== 1 ? 's' : ''} for &ldquo;{query}&rdquo;
        </p>
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

export default UserModeResultsPage;
