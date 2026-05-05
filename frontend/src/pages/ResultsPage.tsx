import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import GradeFilter from '../components/GradeFilter';
import BookFilter from '../components/BookFilter';
import HadithCard from '../components/HadithCard';
import { hadithCollection } from '../data/fakeData';
import type { HadithGrade } from '../types';

const ResultsPage = () => {
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || 'prayer times';
  const gradeParam = searchParams.get('grade') as HadithGrade | null;
  const bookParam = searchParams.get('book');

  const [selectedGrade, setSelectedGrade] = useState<HadithGrade | 'all'>(
    gradeParam || 'all'
  );
  const [selectedBook, setSelectedBook] = useState<string | null>(bookParam || null);
  const [sortBy, setSortBy] = useState<'relevance' | 'authenticity'>('relevance');

  // Filter hadiths based on selections
  const filteredHadiths = hadithCollection.filter((h) => {
    if (selectedGrade !== 'all' && h.grade !== selectedGrade) return false;
    if (selectedBook && !h.book.toLowerCase().includes(selectedBook)) return false;
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

  return (
    <main className="flex-grow w-full max-w-[1200px] mx-auto px-margin-mobile md:px-margin-desktop py-8 flex flex-col gap-8 page-enter">
      {/* Search bar */}
      <div className="w-full max-w-2xl">
        <SearchBar onSearch={handleSearch} compact placeholder={`Refine search: "${query}"`} />
      </div>

      {/* Filters row */}
      <div className="flex flex-col gap-4">
        <GradeFilter selectedGrade={selectedGrade} onGradeChange={setSelectedGrade} />
        <BookFilter selectedBook={selectedBook} onBookChange={setSelectedBook} />
      </div>

      {/* Results header */}
      <div className="flex items-center justify-between border-b border-surface-variant pb-4">
        <p className="font-ui-caption text-ui-caption text-on-surface-variant uppercase tracking-wider">
          Showing {sortedHadiths.length} Result{sortedHadiths.length !== 1 ? 's' : ''} for &ldquo;{query}&rdquo;
        </p>
        <div className="flex items-center gap-2 font-ui-label text-ui-label text-on-surface-variant">
          <span>Sort by:</span>
          <select
            className="bg-transparent border-none text-on-surface focus:ring-0 cursor-pointer font-ui-label"
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
            <span className="material-symbols-outlined text-[48px] text-outline-variant">
              search_off
            </span>
            <p className="font-body-main text-body-main text-on-surface-variant text-center">
              No hadiths found matching your filters. Try adjusting your search criteria.
            </p>
          </div>
        )}
      </div>
    </main>
  );
};

export default ResultsPage;
