import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import IslamicMotif from '../components/IslamicMotif';
import SearchBar from '../components/SearchBar';
import GradeFilter from '../components/GradeFilter';
import BookFilter from '../components/BookFilter';
import HadithOfTheDay from '../components/HadithOfTheDay';
import { POPULAR_QUERIES_EN, POPULAR_QUERIES_AR } from '../constants';
import { useLanguage } from '../i18n/useLanguage';
import { getAppMode } from '../components/Navbar';
import type { Lang } from '../types';

const HOTD_ID_KEY = 'hotd_id';

const UserHomePage = () => {
  const navigate = useNavigate();
  const { t, language } = useLanguage();
  const [selectedGrade, setSelectedGrade] = useState<string | null>(null);
  const [selectedBook, setSelectedBook] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionStorage.getItem(HOTD_ID_KEY)) {
      const randomId = Math.floor(Math.random() * 33738) + 1;
      sessionStorage.setItem(HOTD_ID_KEY, String(randomId));
    }
  }, []);

  const handleSearch = (query: string, lang: Lang) => {
    const mode = getAppMode();
    const params = new URLSearchParams();
    params.set('q', query);
    params.set('lang', lang);
    if (selectedGrade) params.set('grade', selectedGrade);
    if (selectedBook) params.set('book', selectedBook);
    if (mode === 'dev') {
      navigate(`/dev/search?${params.toString()}`);
    } else {
      navigate(`/user/search?${params.toString()}`);
    }
  };

  const popularQueries = language === 'ar' ? POPULAR_QUERIES_AR : POPULAR_QUERIES_EN;

  return (
    <main className="flex-grow flex flex-col items-center justify-center px-margin-mobile md:px-margin-desktop py-16 w-full max-w-container-max-width mx-auto relative">
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-surface-container-low dark:from-dark-surface-container-low via-background dark:via-dark-background to-background dark:to-dark-background opacity-50 -z-10" />

      <div className="text-center max-w-3xl flex flex-col items-center gap-8 mb-12 animate-fade-in-up">
        <IslamicMotif size="md" className="mb-4" />
        <h1 className="font-display-lg text-display-lg text-primary dark:text-dark-primary tracking-tight">
          {t('home.title')}
        </h1>
        <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant max-w-2xl mx-auto">
          {t('user.subtitle')}
        </p>
      </div>

      <div className="w-full max-w-4xl flex flex-col items-center gap-6 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        <SearchBar onSearch={handleSearch} />

        <div className="w-full flex flex-col sm:flex-row gap-4 mt-2">
          <div className="flex-1">
            <GradeFilter value={selectedGrade} onChange={setSelectedGrade} />
          </div>
          <div className="flex-1">
            <BookFilter value={selectedBook} onChange={setSelectedBook} />
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-2 mt-4">
          <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant uppercase tracking-wider me-1">
            {t('home.popular')}
          </span>
          {popularQueries.map((tag) => (
            <button
              key={tag}
              onClick={() => handleSearch(tag, language === 'ar' ? 'ar' : 'en')}
              className="px-3 py-1.5 rounded-full bg-surface-container dark:bg-dark-surface-container text-on-surface-variant dark:text-dark-on-surface-variant font-ui-caption text-ui-caption hover:bg-secondary-container dark:hover:bg-dark-secondary-container hover:text-on-secondary-container dark:hover:text-dark-on-secondary-container transition-colors duration-200 border border-outline-variant dark:border-dark-outline-variant hover:border-secondary dark:hover:border-dark-secondary"
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      <div className="w-full mt-20">
        <HadithOfTheDay />
      </div>
    </main>
  );
};

export default UserHomePage;