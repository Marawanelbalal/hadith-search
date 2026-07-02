import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../api/config';
import { useAuth } from '../api/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

interface Hadith {
  hadith_id: number;
  arabic_hadith: string;
  english_hadith: string;
  book: string;
  normalized_grade: string;
  reference: string;
  in_book_reference: string;
}

interface AnnotationState {
  query_id: string;
  query: string;
  current_index: number;
  total: number;
  pooled_hadiths: Hadith[];
  labels: Record<string, number>;
}

const GRADE_LABELS: Record<number, string> = {
  0: 'Not Relevant',
  1: 'Relevant',
  2: 'Highly Relevant',
};

const GRADE_COLORS: Record<number, string> = {
  0: 'text-red-600 dark:text-red-400',
  1: 'text-yellow-600 dark:text-yellow-400',
  2: 'text-green-600 dark:text-green-400',
};

const DevAnnotationSessionPage = () => {
  const { queryId } = useParams<{ queryId: string }>();
  const navigate = useNavigate();
  const { token, loading: authLoading, authFetch } = useAuth();
  const [state, setState] = useState<AnnotationState | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [flashGrade, setFlashGrade] = useState<number | null>(null);
  const lastSavedRef = useRef<number>(0);

  const fetchState = useCallback(async () => {
    if (!queryId) return;
    try {
      const response = await authFetch(`${API_BASE_URL}/annotation/${queryId}/current`);
      if (response.status === 401) {
        navigate('/dev/annotation/signin');
        return;
      }
      if (!response.ok) throw new Error('Failed to fetch state');
      const data = await response.json();
      setState(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [queryId, authFetch, navigate]);

  useEffect(() => {
    if (authLoading) return;
    if (!token) {
      navigate('/dev/annotation/signin');
      return;
    }
    fetchState();
  }, [token, authLoading, navigate, fetchState]);

  const saveLabel = async (index: number, label: number) => {
    if (!queryId || !state) return;
    const hadith = state.pooled_hadiths[index];
    if (!hadith) return;

    setFlashGrade(label);
    setSaving(true);
    try {
      await authFetch(`${API_BASE_URL}/annotation/${queryId}/label`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          hadith_id: hadith.hadith_id,
          index,
          label
        })
      });
      lastSavedRef.current = Date.now();

      setFlashGrade(null);
      setState(prev => prev ? {
        ...prev,
        labels: { ...prev.labels, [String(hadith.hadith_id)]: label },
        current_index: index + 1
      } : null);
      setSaving(false);
    } catch (err) {
      console.error('Failed to save label:', err);
      setFlashGrade(null);
      setSaving(false);
    }
  };

  const navigateTo = async (index: number) => {
    if (!queryId || !state) return;
    if (index < 0 || index >= state.total) return;

    try {
      await authFetch(`${API_BASE_URL}/annotation/${queryId}/navigate?index=${index}`, {
        method: 'POST'
      });
      setState(prev => prev ? { ...prev, current_index: index } : null);
    } catch (err) {
      console.error('Failed to navigate:', err);
    }
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!state) return;

      if (e.key === 'ArrowRight') {
        navigateTo(state.current_index + 1);
      } else if (e.key === 'ArrowLeft') {
        navigateTo(state.current_index - 1);
      } else if (e.key === '0' || e.key === '1' || e.key === '2') {
        saveLabel(state.current_index, parseInt(e.key));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [state]);

  if (authLoading || loading) return <LoadingSpinner />;

  if (error) {
    return (
      <main className="flex-grow w-full max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col gap-4 page-enter">
        <div className="bg-error-container text-on-error-container p-4 rounded-lg">
          Error: {error}
        </div>
        <button
          onClick={() => navigate('/dev/annotation')}
          className="text-primary dark:text-dark-primary hover:underline"
        >
          Back to annotation list
        </button>
      </main>
    );
  }

  if (!state) return <LoadingSpinner />;

  const currentHadith = state.pooled_hadiths[state.current_index];
  const currentLabel = currentHadith ? state.labels[String(currentHadith.hadith_id)] : undefined;

  const gradeCounts = [0, 1, 2].map(g => ({
    grade: g,
    count: Object.values(state.labels).filter(l => l === g).length,
  }));

  return (
    <main className="flex-grow w-full max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6 page-enter">
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/dev/annotation')}
          className="flex items-center gap-2 px-3 py-1.5 text-on-surface-variant dark:text-dark-on-surface-variant hover:text-primary dark:hover:text-dark-primary transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>

        <div className="flex items-center gap-3">
          {saving && (
            <span className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
              Saving...
            </span>
          )}
          <div className="text-label-lg text-on-surface-variant dark:text-dark-on-surface-variant">
            {state.current_index + 1} / {state.total}
          </div>
        </div>
      </div>

      <div className="w-full bg-surface-variant dark:bg-dark-surface-variant rounded-full h-2">
        <div
          className="bg-primary dark:bg-dark-primary h-2 rounded-full transition-all duration-300"
          style={{ width: `${((state.current_index + 1) / state.total) * 100}%` }}
        />
      </div>

      {Object.keys(state.labels).length > 0 && (
        <div className="flex items-center justify-center gap-6 text-sm">
          {gradeCounts.map(({ grade, count }) => (
            <span key={grade} className={GRADE_COLORS[grade]}>
              {GRADE_LABELS[grade]}: {count}
            </span>
          ))}
        </div>
      )}

      <div className="bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg p-6">
        <div className="mb-4">
          <span className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
            Query:
          </span>
          <div className="font-title-md text-on-surface dark:text-dark-on-surface mt-1">
            {state.query}
          </div>
        </div>

        {currentHadith ? (
          <div className="flex flex-col gap-6">
            <div className="flex flex-col md:flex-row gap-6">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-on-surface-variant dark:text-dark-on-surface-variant mb-2">
                  Arabic (ID: {currentHadith.hadith_id})
                </div>
                {currentHadith.book && (
                  <div className="text-xs text-on-surface-variant dark:text-dark-on-surface-variant mb-2">
                    {currentHadith.book}
                    {currentHadith.normalized_grade ? ` • ${currentHadith.normalized_grade}` : ''}
                    {currentHadith.reference ? ` • ${currentHadith.reference}` : ''}
                  </div>
                )}
                <div
                  className="p-4 bg-surface-variant dark:bg-dark-surface-variant rounded-lg"
                  style={{ direction: 'rtl', textAlign: 'right', fontFamily: 'Amiri, "Noto Naskh Arabic", serif' }}
                >
                  <p className="text-lg leading-relaxed text-on-surface dark:text-dark-on-surface whitespace-pre-wrap">
                    {currentHadith.arabic_hadith}
                  </p>
                </div>
              </div>

              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-on-surface-variant dark:text-dark-on-surface-variant mb-2">
                  English
                </div>
                <div 
                  className="p-4 bg-surface-variant dark:bg-dark-surface-variant rounded-lg"
                  style={{ direction: 'ltr', textAlign: 'left' }}
                >
                  <p className="text-lg leading-relaxed text-on-surface dark:text-dark-on-surface whitespace-pre-wrap">
                    {currentHadith.english_hadith}
                  </p>
                </div>
              </div>
            </div>

            {currentLabel !== undefined && (
              <div className="text-center">
                <span className="text-on-surface-variant dark:text-dark-on-surface-variant">
                  Current grade:{' '}
                </span>
                <span className={`font-medium ${GRADE_COLORS[currentLabel]}`}>
                  {GRADE_LABELS[currentLabel]}
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center py-12 text-on-surface-variant dark:text-dark-on-surface-variant">
            No more hadiths to annotate for this query.
          </div>
        )}
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <button
          onClick={() => navigateTo(state.current_index - 1)}
          disabled={state.current_index === 0}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-outline dark:border-dark-outline text-on-surface dark:text-dark-on-surface hover:bg-surface-variant dark:hover:bg-dark-surface-variant disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Previous
        </button>

        <div className="flex gap-3">
          <button
            onClick={() => saveLabel(state.current_index, 0)}
            disabled={!currentHadith || saving}
            className={`flex flex-col items-center gap-1 px-6 py-3 rounded-lg border-2 transition-all ${
              flashGrade === 0
                ? 'border-red-500 bg-red-500 scale-105 shadow-lg shadow-red-500/50'
                : currentLabel === 0
                ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                : 'border-outline dark:border-dark-outline hover:border-red-400 hover:bg-red-50 dark:hover:bg-red-900/20'
            }`}
          >
            <span className={`text-lg font-bold ${flashGrade === 0 ? 'text-white' : 'text-red-600 dark:text-red-400'}`}>0</span>
            <span className={`text-xs ${flashGrade === 0 ? 'text-white' : 'text-on-surface-variant dark:text-dark-on-surface-variant'}`}>Not Relevant</span>
          </button>

          <button
            onClick={() => saveLabel(state.current_index, 1)}
            disabled={!currentHadith || saving}
            className={`flex flex-col items-center gap-1 px-6 py-3 rounded-lg border-2 transition-all ${
              flashGrade === 1
                ? 'border-yellow-500 bg-yellow-500 scale-105 shadow-lg shadow-yellow-500/50'
                : currentLabel === 1
                ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
                : 'border-outline dark:border-dark-outline hover:border-yellow-400 hover:bg-yellow-50 dark:hover:bg-yellow-900/20'
            }`}
          >
            <span className={`text-lg font-bold ${flashGrade === 1 ? 'text-white' : 'text-yellow-600 dark:text-yellow-400'}`}>1</span>
            <span className={`text-xs ${flashGrade === 1 ? 'text-white' : 'text-on-surface-variant dark:text-dark-on-surface-variant'}`}>Relevant</span>
          </button>

          <button
            onClick={() => saveLabel(state.current_index, 2)}
            disabled={!currentHadith || saving}
            className={`flex flex-col items-center gap-1 px-6 py-3 rounded-lg border-2 transition-all ${
              flashGrade === 2
                ? 'border-green-500 bg-green-500 scale-105 shadow-lg shadow-green-500/50'
                : currentLabel === 2
                ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                : 'border-outline dark:border-dark-outline hover:border-green-400 hover:bg-green-50 dark:hover:bg-green-900/20'
            }`}
          >
            <span className={`text-lg font-bold ${flashGrade === 2 ? 'text-white' : 'text-green-600 dark:text-green-400'}`}>2</span>
            <span className={`text-xs ${flashGrade === 2 ? 'text-white' : 'text-on-surface-variant dark:text-dark-on-surface-variant'}`}>Highly Relevant</span>
          </button>
        </div>

        <button
          onClick={() => navigateTo(state.current_index + 1)}
          disabled={state.current_index >= state.total - 1}
          className="flex items-center gap-2 px-4 py-2 rounded-lg border border-outline dark:border-dark-outline text-on-surface dark:text-dark-on-surface hover:bg-surface-variant dark:hover:bg-dark-surface-variant disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Next
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      <div className="text-center text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
        Keyboard shortcuts: <kbd className="px-1.5 py-0.5 bg-surface-variant dark:bg-dark-surface-variant rounded">0</kbd> <kbd className="px-1.5 py-0.5 bg-surface-variant dark:bg-dark-surface-variant rounded">1</kbd> <kbd className="px-1.5 py-0.5 bg-surface-variant dark:bg-dark-surface-variant rounded">2</kbd> to grade • <kbd className="px-1.5 py-0.5 bg-surface-variant dark:bg-dark-surface-variant rounded">&larr;</kbd> <kbd className="px-1.5 py-0.5 bg-surface-variant dark:bg-dark-surface-variant rounded">&rarr;</kbd> to navigate
      </div>
    </main>
  );
};

export default DevAnnotationSessionPage;
