import { useState } from 'react';
import SearchBar from '../components/SearchBar';
import GradeFilter from '../components/GradeFilter';
import BookFilter from '../components/BookFilter';
import HadithCard from '../components/HadithCard';
import HadithModal from '../components/HadithModal';
import ErrorBanner from '../components/ErrorBanner';
import LoadingSpinner from '../components/LoadingSpinner';
import { useApi } from '../api/useApi';
import { useLanguage } from '../i18n/useLanguage';
import { ALGORITHMS } from '../types';
import type { Lang, SearchResult, SearchRequest } from '../types';

const DevComparePage = () => {
  const { t } = useLanguage();
  const { search, errors, clearError } = useApi();

  const [query, setQuery] = useState('');
  const [lang, setLang] = useState<Lang>('en');
  const [algorithmA, setAlgorithmA] = useState('bm25-prf');
  const [algorithmB, setAlgorithmB] = useState('bm25');
  const [selectedGrade, setSelectedGrade] = useState<string | null>(null);
  const [selectedBook, setSelectedBook] = useState<string | null>(null);
  const [resultsA, setResultsA] = useState<SearchResult[]>([]);
  const [resultsB, setResultsB] = useState<SearchResult[]>([]);
  const [isLoadingA, setIsLoadingA] = useState(false);
  const [isLoadingB, setIsLoadingB] = useState(false);
  const [hasCompared, setHasCompared] = useState(false);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);

  const buildRequest = (): SearchRequest => ({ query, lang, grade_filter: selectedGrade, book_filter: selectedBook });

  const runComparison = async () => {
    if (!query.trim()) return;
    if (algorithmA === algorithmB) return;

    setResultsA([]);
    setResultsB([]);
    setHasCompared(true);
    setIsLoadingA(true);
    setIsLoadingB(true);

    const req = buildRequest();

    search(algorithmA, req).then((res) => {
      setResultsA(res.results);
      setIsLoadingA(false);
    });

    search(algorithmB, req).then((res) => {
      setResultsB(res.results);
      setIsLoadingB(false);
    });
  };

  const handleSearch = (newQuery: string, newLang: Lang) => {
    setQuery(newQuery);
    setLang(newLang);
  };

  const handleFilterChange = (grade: string | null, book: string | null) => {
    setSelectedGrade(grade);
    setSelectedBook(book);
  };

  const algoALabel = ALGORITHMS.find((a) => a.value === algorithmA)?.label || algorithmA;
  const algoBLabel = ALGORITHMS.find((a) => a.value === algorithmB)?.label || algorithmB;

  return (
    <main className="flex-grow w-full max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 py-10 lg:py-12 flex flex-col gap-8 page-enter">
      <div className="flex flex-col gap-4">
        <h1 className="font-display-lg text-display-lg text-primary dark:text-dark-primary">
          {t('nav.algorithmComparison')}
        </h1>
      </div>

      {hasCompared && !isLoadingA && !isLoadingB && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="flex flex-col">
            <div className="bg-surface-container-low dark:bg-dark-surface-container-low border border-outline-variant dark:border-dark-outline-variant rounded-t-xl p-4 flex justify-between items-center">
              <h3 className="font-h1-hadith text-lg text-primary dark:text-dark-primary">{algoALabel}</h3>
              <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">{resultsA.length} results</span>
            </div>
            <div className="p-4 flex flex-col gap-4 border border-t-0 border-outline-variant dark:border-dark-outline-variant rounded-b-xl bg-surface dark:bg-dark-surface">
              {isLoadingA ? (
                <div className="flex items-center justify-center py-12"><LoadingSpinner /></div>
              ) : resultsA.length === 0 ? (
                <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant text-center py-8">{t('compare.noResults')}</p>
              ) : (
                resultsA.map((result, index) => (
                  <HadithCard key={result.hadith.hadith_id} result={result} rank={index + 1} lang={lang} onClick={() => setSelectedResult(result)} />
                ))
              )}
            </div>
          </div>

          <div className="flex flex-col">
            <div className="bg-surface-container-low dark:bg-dark-surface-container-low border border-outline-variant dark:border-dark-outline-variant rounded-t-xl p-4 flex justify-between items-center">
              <h3 className="font-h1-hadith text-lg text-secondary dark:text-dark-secondary">{algoBLabel}</h3>
              <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">{resultsB.length} results</span>
            </div>
            <div className="p-4 flex flex-col gap-4 border border-t-0 border-outline-variant dark:border-dark-outline-variant rounded-b-xl bg-surface dark:bg-dark-surface">
              {isLoadingB ? (
                <div className="flex items-center justify-center py-12"><LoadingSpinner /></div>
              ) : resultsB.length === 0 ? (
                <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant text-center py-8">{t('compare.noResults')}</p>
              ) : (
                resultsB.map((result, index) => (
                  <HadithCard key={result.hadith.hadith_id} result={result} rank={index + 1} lang={lang} onClick={() => setSelectedResult(result)} />
                ))
              )}
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col gap-6 p-5 sm:p-6 bg-surface-container-lowest dark:bg-dark-surface-container-lowest border border-outline-variant dark:border-dark-outline-variant rounded-xl">
        <div className="w-full max-w-2xl">
          <SearchBar onSearch={handleSearch} />
        </div>

        <div className="flex flex-col sm:flex-row gap-4 flex-wrap items-start sm:items-end">
          <GradeFilter value={selectedGrade} onChange={(g) => handleFilterChange(g, selectedBook)} />
          <BookFilter value={selectedBook} onChange={(b) => handleFilterChange(selectedGrade, b)} />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="flex flex-col gap-2">
            <label className="font-ui-label text-ui-label text-primary dark:text-dark-primary font-semibold">{t('dev.algorithmA')}</label>
            <select
              value={algorithmA}
              onChange={(e) => setAlgorithmA(e.target.value)}
              className="h-12 px-4 rounded-lg border border-outline dark:border-dark-outline bg-surface dark:bg-dark-surface text-on-surface dark:text-dark-on-surface font-ui-label text-ui-label focus:ring-2 focus:ring-primary dark:focus:ring-dark-primary cursor-pointer"
            >
              {ALGORITHMS.map((algo) => (
                <option key={algo.value} value={algo.value} disabled={algo.value === algorithmB}>{algo.label}</option>
              ))}
            </select>
          </div>
          <div className="flex flex-col gap-2">
            <label className="font-ui-label text-ui-label text-secondary dark:text-dark-secondary font-semibold">{t('dev.algorithmB')}</label>
            <select
              value={algorithmB}
              onChange={(e) => setAlgorithmB(e.target.value)}
              className="h-12 px-4 rounded-lg border border-outline dark:border-dark-outline bg-surface dark:bg-dark-surface text-on-surface dark:text-dark-on-surface font-ui-label text-ui-label focus:ring-2 focus:ring-secondary dark:focus:ring-dark-secondary cursor-pointer"
            >
              {ALGORITHMS.map((algo) => (
                <option key={algo.value} value={algo.value} disabled={algo.value === algorithmA}>{algo.label}</option>
              ))}
            </select>
          </div>
        </div>

        {errors.search && (
          <ErrorBanner message={errors.search} onDismiss={() => clearError('search')} />
        )}

        {algorithmA === algorithmB && (
          <div className="bg-warning-container dark:bg-dark-warning-container text-on-warning-container dark:text-dark-on-warning-container rounded-lg p-4 text-center font-ui-label text-ui-label">
            {t('compare.selectTwo')}
          </div>
        )}

        <button
          onClick={runComparison}
          disabled={!query.trim() || algorithmA === algorithmB || isLoadingA || isLoadingB}
          className="h-12 px-6 rounded-lg bg-primary dark:bg-dark-primary text-white font-ui-label text-ui-label hover:bg-primary/90 dark:hover:bg-dark-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors self-start"
        >
          {t('compare.compare')}
        </button>
      </div>

      <HadithModal result={selectedResult} rank={selectedResult ? resultsA.findIndex(r => r.hadith.hadith_id === selectedResult.hadith.hadith_id) + 1 : undefined} lang={lang} onClose={() => setSelectedResult(null)} />
    </main>
  );
};

export default DevComparePage;
