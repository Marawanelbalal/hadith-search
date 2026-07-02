import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../api/config';
import { useAuth } from '../api/AuthContext';
import LoadingSpinner from '../components/LoadingSpinner';

interface QueryInfo {
  query_id: string;
  query: string;
  total: number;
  graded: number;
  current_index: number;
}

const DevAnnotationPage = () => {
  const navigate = useNavigate();
  const { token, annotator, loading: authLoading, signout, authFetch } = useAuth();
  const [queries, setQueries] = useState<QueryInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (authLoading) return;
    if (!token) {
      navigate('/dev/annotation/signin');
      return;
    }

    const fetchQueries = async () => {
      try {
        const response = await authFetch(`${API_BASE_URL}/annotation/queries`);
        if (response.status === 401) {
          navigate('/dev/annotation/signin');
          return;
        }
        if (!response.ok) throw new Error('Failed to fetch queries');
        const data = await response.json();
        setQueries(data.queries);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };
    fetchQueries();
  }, [token, authLoading, navigate, authFetch]);

  const handleSignout = async () => {
    await signout();
    navigate('/dev/annotation/signin');
  };

  const totalQueries = queries.length;
  const totalGraded = queries.reduce((sum, q) => sum + q.graded, 0);
  const totalHadiths = queries.reduce((sum, q) => sum + q.total, 0);
  const overallProgress = totalHadiths > 0 ? Math.round((totalGraded / totalHadiths) * 100) : 0;

  if (authLoading || loading) return <LoadingSpinner />;

  return (
    <main className="flex-grow w-full max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 py-10 lg:py-12 flex flex-col gap-8 page-enter">
      <div className="flex justify-between items-start">
        <div className="flex flex-col gap-4">
          <h1 className="font-display-lg text-display-lg text-primary dark:text-dark-primary">
            Annotation
          </h1>
          <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant">
            {annotator ? `Welcome, ${annotator.username}` : 'Grade hadiths for relevance.'} Click a query to start annotating.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/dev/annotation/guidelines')}
            className="px-3 py-1.5 text-sm text-on-surface-variant dark:text-dark-on-surface-variant hover:text-primary dark:hover:text-dark-primary transition-colors"
          >
            Guidelines
          </button>
          <button
            onClick={handleSignout}
            className="px-3 py-1.5 text-sm text-on-surface-variant dark:text-dark-on-surface-variant hover:text-primary dark:hover:text-dark-primary transition-colors"
          >
            Sign Out
          </button>
        </div>
      </div>

      <div className="bg-surface dark:bg-dark-surface p-6 rounded-lg border border-outline dark:border-dark-outline">
        <div className="flex justify-between items-center mb-4">
          <span className="font-label-lg text-on-surface dark:text-dark-on-surface">
            Your Progress
          </span>
          <span className="font-label-lg text-primary dark:text-dark-primary">
            {totalGraded} / {totalHadiths} ({overallProgress}%)
          </span>
        </div>
        <div className="w-full bg-surface-variant dark:bg-dark-surface-variant rounded-full h-3">
          <div
            className="bg-primary dark:bg-dark-primary h-3 rounded-full transition-all duration-300"
            style={{ width: `${overallProgress}%` }}
          />
        </div>
        <div className="mt-2 text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
          {totalQueries} queries assigned • {totalGraded} graded • {totalHadiths - totalGraded} remaining
        </div>
      </div>

      {error && (
        <div className="bg-error-container text-on-error-container p-4 rounded-lg">
          Error: {error}
        </div>
      )}

      <div className="grid gap-4">
        {queries.map((q) => {
          const progress = q.total > 0 ? Math.round((q.graded / q.total) * 100) : 0;
          const isComplete = q.graded >= q.total;
          const isEnglish = q.query_id.startsWith('EN');

          return (
            <button
              key={q.query_id}
              onClick={() => navigate(`/dev/annotation/${q.query_id}`)}
              className="flex flex-col gap-3 p-5 bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg hover:border-primary dark:hover:border-dark-primary hover:shadow-md transition-all text-left"
            >
              <div className="flex justify-between items-start">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                      isEnglish
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                        : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                    }`}>
                      {isEnglish ? 'EN' : 'AR'}
                    </span>
                    <span className="font-label-lg text-on-surface dark:text-dark-on-surface truncate">
                      {q.query}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-4">
                  {isComplete ? (
                    <span className="text-green-600 dark:text-green-400 text-sm font-medium">
                      Complete
                    </span>
                  ) : (
                    <span className="text-on-surface-variant dark:text-dark-on-surface-variant text-sm">
                      {q.graded}/{q.total}
                    </span>
                  )}
                </div>
              </div>

              <div className="w-full">
                <div className="w-full bg-surface-variant dark:bg-dark-surface-variant rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      isComplete
                        ? 'bg-green-500'
                        : 'bg-primary dark:bg-dark-primary'
                    }`}
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </main>
  );
};

export default DevAnnotationPage;
