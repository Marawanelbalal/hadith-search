import { useState, useEffect } from 'react';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorBanner from '../components/ErrorBanner';
import { useApi } from '../api/useApi';
import { useLanguage } from '../i18n/useLanguage';
import type { BenchmarkResults, Metrics } from '../types';

const METRIC_KEYS: (keyof Metrics)[] = ['AP', 'RR', 'P@20', 'R@20', 'F1@20', 'nDCG@20'];

const BENCHMARK_DESCRIPTION = "This benchmark evaluates 10 retrieval algorithms across a stratified sample of 2,000 hadiths. Queries were authored manually and cover both English and Arabic. Relevance judgments (qrels) were produced using Claude Sonnet 4.6, with each query-document pair graded on a scale of 0 (not relevant), 1 (relevant), or 2 (highly relevant). The benchmark measures standard IR metrics: Average Precision (AP), Mean Reciprocal Rank (MRR), Precision at 20 (P@20), Recall at 20 (R@20), F1 at 20, and nDCG at 20.";

const ALGO_LABELS: Record<string, string> = {
  'BM25': 'BM25',
  'TF-IDF': 'TF-IDF',
  'Term Overlap': 'Term Overlap',
  'BM25 + Rocchio (PRF)': 'BM25 + Rocchio (PRF)',
  'BM25 + TF-IDF (Hybrid)': 'BM25 + TF-IDF (Hybrid)',
  'BM25 + TF-IDF + Rocchio': 'BM25 + TF-IDF + Rocchio',
  'Cosine Similarity': 'Cosine Similarity',
  'BM25 + Semantic Rerank': 'BM25 + Semantic Rerank',
  'BM25 + RRF': 'BM25 + RRF',
  'BM25 + Cross-Encoder': 'BM25 + Cross-Encoder',
  'Final Pipeline': 'Final Pipeline',
};

const DevBenchmarkPage = () => {
  const { t } = useLanguage();
  const { getBenchmarks, getQrels, loading, errors, clearError } = useApi();
  const [qrelData, setQrelData] = useState<{ description: string; qrels: Record<string, { query: string; grades: Record<string, unknown> }> } | null>(null);
  const [benchmarkResults, setBenchmarkResults] = useState<BenchmarkResults | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [qrels, benchmarks] = await Promise.all([getQrels(), getBenchmarks()]);
        setQrelData(qrels as { description: string; qrels: Record<string, { query: string; grades: Record<string, unknown> }> });
        setBenchmarkResults(benchmarks);
      } catch {
        // errors handled by ApiContext
      }
    };
    fetchData();
  }, [getQrels, getBenchmarks]);

  return (
    <main className="flex-grow w-full max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 py-10 lg:py-12 flex flex-col gap-12 lg:gap-16 page-enter">
      <div className="flex flex-col gap-4">
        <h1 className="font-display-lg text-display-lg text-primary dark:text-dark-primary">
          {t('benchmarks.title')}
        </h1>
        <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant">
          {t('benchmarks.subtitle')}
        </p>
      </div>

      {errors.benchmarks && (
        <ErrorBanner message={errors.benchmarks} onDismiss={() => clearError('benchmarks')} />
      )}

      {loading.benchmarks && (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <LoadingSpinner />
          <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant">{t('loading.subtitle')}</p>
        </div>
      )}

      {!loading.benchmarks && (
        <>
          <section className="flex flex-col gap-6">
            <div className="flex items-center gap-4 border-b border-outline-variant dark:border-dark-outline-variant pb-2">
              <span className="material-symbols-outlined text-primary dark:text-dark-primary fill">info</span>
              <h2 className="font-h1-hadith text-h1-hadith text-on-surface dark:text-dark-on-surface">{t('benchmarks.about')}</h2>
            </div>
            <div className="bg-surface-container-lowest dark:bg-dark-surface-container-lowest border border-outline-variant dark:border-dark-outline-variant rounded-xl p-5 sm:p-6">
              <p className="font-body-main text-body-main text-on-surface dark:text-dark-on-surface leading-relaxed">
                {BENCHMARK_DESCRIPTION}
              </p>
            </div>
          </section>

          <section className="flex flex-col gap-6">
            <div className="flex items-center gap-4 border-b border-outline-variant dark:border-dark-outline-variant pb-2">
              <span className="material-symbols-outlined text-primary dark:text-dark-primary fill">fact_check</span>
              <h2 className="font-h1-hadith text-h1-hadith text-on-surface dark:text-dark-on-surface">Relevance Judgments (Qrels)</h2>
            </div>
            <div className="bg-surface-container-lowest dark:bg-dark-surface-container-lowest border border-outline-variant dark:border-dark-outline-variant rounded-xl p-5 sm:p-6">
{benchmarkResults?.BM25 && (
  <div className="overflow-x-auto rounded-lg border border-outline-variant dark:border-dark-outline-variant">
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="bg-surface-container-low dark:bg-dark-surface-container-low border-b border-outline-variant dark:border-dark-outline-variant">
          <th className="p-3 sm:p-4 text-start font-semibold text-on-surface dark:text-dark-on-surface min-w-[120px]">
            Query ID
          </th>
          <th className="p-3 sm:p-4 text-start font-semibold text-on-surface dark:text-dark-on-surface">
            Query text
          </th>
          <th className="p-3 sm:p-4 text-center font-semibold text-on-surface dark:text-dark-on-surface min-w-[80px]">
            Language
          </th>
        </tr>
      </thead>
      <tbody className="divide-y divide-outline-variant dark:divide-dark-outline-variant">
        {Object.entries(benchmarkResults.BM25)
          .filter(([queryId]) => queryId !== 'MEAN')
          .map(([queryId, entry], idx) => {
            const isArabic = queryId.startsWith('AR');
            return (
              <tr
                key={queryId}
                className="hover:bg-surface-container dark:hover:bg-dark-surface-container transition-colors duration-150"
              >
                <td className="p-3 sm:p-4 font-mono text-xs text-primary dark:text-dark-primary whitespace-nowrap">
                  {queryId}
                </td>
                <td
                  className="p-3 sm:p-4 text-on-surface dark:text-dark-on-surface"
                  dir={isArabic ? 'rtl' : 'ltr'}
                >
                  {entry['Query Text']}
                </td>
                <td className="p-3 sm:p-4 text-center">
                  <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium
                    ${isArabic
                      ? 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200'
                      : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                    }`}>
                    {isArabic ? 'Arabic' : 'English'}
                  </span>
                </td>
              </tr>
            );
          })}
      </tbody>
    </table>
  </div>
)}
            </div>
          </section>

          <section className="flex flex-col gap-8">
            <div className="flex items-center gap-4 border-b border-outline-variant dark:border-dark-outline-variant pb-2">
              <span className="material-symbols-outlined text-primary dark:text-dark-primary fill">analytics</span>
              <h2 className="font-h1-hadith text-h1-hadith text-on-surface dark:text-dark-on-surface">{t('benchmarks.performance')}</h2>
            </div>

            {benchmarkResults && (
              <div className="flex flex-col gap-10">
                {Object.entries(benchmarkResults).map(([algo, queries]) => {
                  const algoLabel = ALGO_LABELS[algo] ?? algo;
                  const queryEntries = Object.entries(queries).filter(([, r]) => r.Metrics);

                  return (
                    <div key={algo} className="flex flex-col gap-4">
                      <h3 className="font-h1-hadith text-lg text-primary dark:text-dark-primary">{algoLabel}</h3>
                      <div className="overflow-x-auto rounded-lg border border-outline-variant dark:border-dark-outline-variant bg-surface-container-lowest dark:bg-dark-surface-container-lowest">
                        <table className="w-full text-start border-collapse min-w-[600px]">
                          <thead>
                            <tr className="bg-surface-container-low dark:bg-dark-surface-container-low font-ui-label text-ui-label text-on-surface dark:text-dark-on-surface border-b border-outline-variant dark:border-dark-outline-variant">
                              <th className="p-3 sm:p-4 py-3 font-semibold text-start min-w-[80px]">Query ID</th>
                              <th className="p-3 sm:p-4 py-3 font-semibold text-start min-w-[200px]">Query Text</th>
                              {METRIC_KEYS.map((key) => (
                                <th key={key} className="p-3 sm:p-4 py-3 font-semibold text-end min-w-[100px]">{key}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody className="font-body-main text-body-main text-on-surface dark:text-dark-on-surface divide-y divide-outline-variant dark:divide-dark-outline-variant">
                            {queryEntries.map(([queryId, data]) => (
                              <tr key={queryId} className="hover:bg-surface-container dark:hover:bg-dark-surface-container transition-colors duration-200">
                                <td className="p-3 sm:p-4 text-primary dark:text-dark-primary font-mono">{queryId}</td>
                                <td className="p-3 sm:p-4 text-on-surface-variant dark:text-dark-on-surface-variant truncate max-w-[200px]">{data['Query Text'] ?? queryId}</td>
                                {METRIC_KEYS.map((key) => (
                                  <td key={key} className="p-3 sm:p-4 text-end text-on-surface-variant dark:text-dark-on-surface-variant">
                                    {(data.Metrics[key] ?? 0).toFixed(4)}
                                  </td>
                                ))}
                              </tr>
                            ))}

                          </tbody>
                        </table>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
};

export default DevBenchmarkPage;
