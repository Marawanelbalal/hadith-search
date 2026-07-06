import { useState, useEffect, useMemo, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import SearchBar from '../components/SearchBar';
import GradeFilter from '../components/GradeFilter';
import BookFilter from '../components/BookFilter';
import HadithCard from '../components/HadithCard';
import HadithModal from '../components/HadithModal';
import ErrorBanner from '../components/ErrorBanner';
import LoadingSpinner from '../components/LoadingSpinner';
import Pagination from '../components/Pagination';
import { useApi } from '../api/useApi';
import { useLanguage } from '../i18n/useLanguage';
import { sortByGradeAndRelevance, sortByRelevance } from '../utils/sort';
import { ALGORITHMS } from '../types';
import type { Lang, SearchResult, SearchRequest } from '../types';

const PAGE_SIZE = 20;

const DevSearchPage = () => {
  const { t } = useLanguage();
  const { search, loading, errors, clearError } = useApi();
  const [searchParams, setSearchParams] = useSearchParams();
  const resultsRef = useRef<HTMLDivElement>(null);

  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [lang, setLang] = useState<Lang>((searchParams.get('lang') as Lang) || 'en');
  const [selectedAlgorithm, setSelectedAlgorithm] = useState(searchParams.get('algorithm') || 'bm25-prf');
  const [selectedGrade, setSelectedGrade] = useState<string | null>(searchParams.get('grade') || null);
  const [selectedBook, setSelectedBook] = useState<string | null>(searchParams.get('book') || null);
  const [rawResults, setRawResults] = useState<SearchResult[]>([]);
  const [responseTime, setResponseTime] = useState<number | null>(null);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [sortMode, setSortMode] = useState<'grade-relevance' | 'relevance'>('grade-relevance');

  const doSearch = (
    overrideQuery?: string,
    overrideLang?: Lang,
    overrideGrade?: string | null,
    overrideBook?: string | null,
  ) => {
    const effectiveQuery = overrideQuery ?? query;
    const effectiveLang = overrideLang ?? lang;
    const effectiveGrade = overrideGrade ?? selectedGrade;
    const effectiveBook = overrideBook ?? selectedBook;
    if (!effectiveQuery.trim()) return;
    const params = new URLSearchParams();
    params.set('q', effectiveQuery);
    params.set('lang', effectiveLang);
    params.set('algorithm', selectedAlgorithm);
    if (effectiveGrade) params.set('grade', effectiveGrade);
    if (effectiveBook) params.set('book', effectiveBook);
    setSearchParams(params, { replace: true });

    const request: SearchRequest = {
      query: effectiveQuery,
      lang: effectiveLang,
      grade_filter: effectiveGrade,
      book_filter: effectiveBook,
    };
    search(selectedAlgorithm, request).then((response) => {
      setRawResults(response.results);
      setResponseTime(response.response_time_ms ?? null);
      setCurrentPage(1);
    });
  };

  const handleSearch = (newQuery: string, newLang: Lang) => {
    setQuery(newQuery);
    setLang(newLang);
    doSearch(newQuery, newLang);
  };

  const handleAlgorithmChange = (algo: string) => {
    setSelectedAlgorithm(algo);
  };

  const handleFilterChange = (grade: string | null, book: string | null) => {
    setSelectedGrade(grade);
    setSelectedBook(book);
    if (query.trim()) {
      doSearch(undefined, undefined, grade, book);
    }
  };

  const handleSortChange = (mode: 'grade-relevance' | 'relevance') => {
    setSortMode(mode);
    setCurrentPage(1);
  };

  useEffect(() => {
    if (searchParams.get('q')) {
      doSearch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sortedResults = useMemo(() => {
    return sortMode === 'grade-relevance'
      ? sortByGradeAndRelevance(rawResults)
      : sortByRelevance(rawResults);
  }, [rawResults, sortMode]);

  const totalPages = Math.ceil(sortedResults.length / PAGE_SIZE);
  const paginatedResults = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return sortedResults.slice(start, start + PAGE_SIZE);
  }, [sortedResults, currentPage]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <main className="flex-grow w-full max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-6 page-enter">
      <div className="flex flex-col gap-6">
        <h1 className="font-display-lg text-display-lg text-primary dark:text-dark-primary">
          {t('nav.search')}
        </h1>
        <SearchBar onSearch={handleSearch} initialQuery={query} disabled={loading.search} />
      </div>

      <div className="flex flex-col sm:flex-row gap-4 flex-wrap items-start sm:items-end">
        <GradeFilter value={selectedGrade} onChange={(g) => handleFilterChange(g, selectedBook)} />
        <BookFilter value={selectedBook} onChange={(b) => handleFilterChange(selectedGrade, b)} />
        <div className="flex flex-col gap-1">
          <label className="font-ui-label text-ui-label text-on-surface-variant dark:text-dark-on-surface-variant">
            {t('algorithm.label')}
          </label>
          <select
            value={selectedAlgorithm}
            onChange={(e) => handleAlgorithmChange(e.target.value)}
            className="w-full sm:w-auto px-4 py-2.5 bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg text-on-surface dark:text-dark-on-surface font-ui-label text-ui-label focus:ring-2 focus:ring-primary dark:focus:ring-dark-primary cursor-pointer"
          >
            {ALGORITHMS.map((algo) => (
              <option key={algo.value} value={algo.value}>
                {algo.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {errors.search && (
        <ErrorBanner message={errors.search} onDismiss={() => clearError('search')} />
      )}

      {loading.search && (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <LoadingSpinner />
          <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant">
            {t('loading.subtitle')}
          </p>
        </div>
      )}

      {!loading.search && rawResults.length > 0 && (
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-surface-variant dark:border-dark-surface-variant pb-4">
          <p className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant uppercase tracking-wider">
            {t('results.showing', { count: sortedResults.length, s: sortedResults.length !== 1 ? 's' : '' })} &ldquo;{query}&rdquo;
            {responseTime !== null && (
              <span className="ml-2 text-primary/60 dark:text-dark-primary/60">({responseTime}ms)</span>
            )}
          </p>
          <div className="flex items-center gap-2">
            <span className="font-ui-label text-ui-label text-on-surface-variant dark:text-dark-on-surface-variant">{t('sort.label')}</span>
            <select
              value={sortMode}
              onChange={(e) => handleSortChange(e.target.value as 'grade-relevance' | 'relevance')}
              className="px-3 py-2 bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg text-on-surface dark:text-dark-on-surface font-ui-label text-ui-label cursor-pointer"
            >
              <option value="grade-relevance">{t('sort.gradeRelevance')}</option>
              <option value="relevance">{t('sort.relevance')}</option>
            </select>
          </div>
        </div>
      )}

      {!loading.search && (
        <div ref={resultsRef} className="flex flex-col gap-5">
          {paginatedResults.map((result, index) => (
            <HadithCard
              key={result.hadith.hadith_id}
              result={result}
              rank={(currentPage - 1) * PAGE_SIZE + index + 1}
              lang={lang}
              onClick={() => setSelectedResult(result)}
            />
          ))}

          {rawResults.length === 0 && query.trim() && !errors.search && (
            <div className="flex flex-col items-center justify-center py-16 gap-4">
              <span className="material-symbols-outlined text-[48px] text-outline-variant dark:text-dark-outline-variant">
                search_off
              </span>
              <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant text-center">
                {t('results.noResults')}
              </p>
            </div>
          )}
        </div>
      )}

      {!loading.search && totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalResults={sortedResults.length}
          pageSize={PAGE_SIZE}
          onPageChange={handlePageChange}
        />
      )}

      <HadithModal
        result={selectedResult}
        rank={selectedResult ? sortedResults.findIndex(r => r.hadith.hadith_id === selectedResult.hadith.hadith_id) + 1 : undefined}
        lang={lang}
        onClose={() => setSelectedResult(null)}
      />
    </main>
  );
};

export default DevSearchPage;
