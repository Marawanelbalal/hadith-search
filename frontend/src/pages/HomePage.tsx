import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import IslamicMotif from '../components/IslamicMotif';
import SearchBar from '../components/SearchBar';
import GradeFilter from '../components/GradeFilter';
import BookFilter from '../components/BookFilter';
import HadithOfTheDay from '../components/HadithOfTheDay';
import { popularSearches } from '../data/fakeData';
import type { HadithGrade } from '../types';

const HomePage = () => {
  const navigate = useNavigate();
  const [selectedGrade, setSelectedGrade] = useState<HadithGrade | 'all'>('all');
  const [selectedBook, setSelectedBook] = useState<string | null>(null);

  const handleSearch = (query: string) => {
    navigate(`/results?q=${encodeURIComponent(query)}&grade=${selectedGrade}${selectedBook ? `&book=${selectedBook}` : ''}`);
  };

  return (
    <main className="flex-grow flex flex-col items-center justify-center px-margin-mobile md:px-margin-desktop py-16 w-full max-w-container-max-width mx-auto relative">
      {/* Background gradient */}
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-surface-container-low dark:from-dark-surface-container-low via-background dark:via-dark-background to-background dark:to-dark-background opacity-50 -z-10" />

      {/* Hero section */}
      <div className="text-center max-w-3xl flex flex-col items-center gap-8 mb-12 animate-fade-in-up">
        <IslamicMotif size="md" className="mb-4" />
        <h1 className="font-display-lg text-display-lg text-primary dark:text-dark-primary tracking-tight">
          Hadith Search
        </h1>
        <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant max-w-2xl mx-auto">
          Search across 33,000+ authenticated prophetic narrations. Explore the six canonical
          collections with advanced retrieval algorithms.
        </p>
      </div>

      {/* Search bar */}
      <div className="w-full max-w-4xl flex flex-col items-center gap-6 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        <SearchBar onSearch={handleSearch} />

        {/* Grade filter */}
        <div className="w-full flex flex-col gap-6 mt-2">
          <GradeFilter selectedGrade={selectedGrade} onGradeChange={setSelectedGrade} />
        </div>

        {/* Book filter */}
        <div className="w-full mt-2">
          <BookFilter selectedBook={selectedBook} onBookChange={setSelectedBook} />
        </div>

        {/* Popular searches */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-4">
          <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant uppercase tracking-wider mr-1">
            Popular:
          </span>
          {popularSearches.map((tag) => (
            <button
              key={tag}
              onClick={() => handleSearch(tag)}
              className="px-3 py-1.5 rounded-full bg-surface-container dark:bg-dark-surface-container text-on-surface-variant dark:text-dark-on-surface-variant font-ui-caption text-ui-caption hover:bg-secondary-container dark:hover:bg-dark-secondary-container hover:text-on-secondary-container dark:hover:text-dark-on-secondary-container transition-all duration-200 border border-outline-variant dark:border-dark-outline-variant hover:border-secondary dark:hover:border-dark-secondary"
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      {/* Hadith of the Day */}
      <div className="w-full mt-20">
        <HadithOfTheDay />
      </div>
    </main>
  );
};

export default HomePage;
