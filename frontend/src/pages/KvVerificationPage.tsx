import { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '../api/config';
import LoadingSpinner from '../components/LoadingSpinner';

interface KvPair {
  id: number;
  topic: string;
  language: string;
  concept_en: string;
  concept_ar: string;
  entity_en: string;
  entity_ar: string;
  hadith_id: number;
  hadith_en: string | null;
  hadith_ar: string | null;
  status: string;
  created_at: string;
  verified_at: string | null;
}

interface Stats {
  total: number;
  by_status: Record<string, number>;
  by_topic: Record<string, number>;
}

interface KvResponse {
  pairs: KvPair[];
  total: number;
  limit: number;
  offset: number;
}

const STATUS_FILTERS = ['pending', 'verified', 'rejected'] as const;
type StatusFilter = (typeof STATUS_FILTERS)[number] | 'all';

const PAGE_SIZE = 10;

const KvVerificationPage = () => {
  const [pairs, setPairs] = useState<KvPair[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('pending');
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [verifyingId, setVerifyingId] = useState<number | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/kv-pairs/stats`);
      if (!res.ok) throw new Error('Failed to fetch stats');
      const data = await res.json();
      setStats(data);
    } catch {
      // silent
    }
  }, []);

  const fetchPairs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        limit: String(PAGE_SIZE),
        offset: String(offset),
      });
      if (statusFilter !== 'all') params.set('status', statusFilter);
      const res = await fetch(`${API_BASE_URL}/kv-pairs?${params}`);
      if (!res.ok) throw new Error('Failed to fetch KV pairs');
      const data: KvResponse = await res.json();
      setPairs(data.pairs);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [statusFilter, offset]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  useEffect(() => {
    fetchPairs();
  }, [fetchPairs]);

  const handleVerify = async (pairId: number, status: 'verified' | 'rejected') => {
    setVerifyingId(pairId);
    try {
      const res = await fetch(`${API_BASE_URL}/kv-pairs/${pairId}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (!res.ok) throw new Error('Failed to verify');
      setPairs((prev) => prev.filter((p) => p.id !== pairId));
      setTotal((prev) => Math.max(0, prev - 1));
      fetchStats();
      if (pairs.length <= 1 && offset > 0) {
        setOffset(Math.max(0, offset - PAGE_SIZE));
      } else {
        fetchPairs();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setVerifyingId(null);
    }
  };

  const handleFilterChange = (filter: StatusFilter) => {
    setStatusFilter(filter);
    setOffset(0);
  };

  const pending = stats?.by_status['pending'] ?? 0;
  const verified = stats?.by_status['verified'] ?? 0;
  const rejected = stats?.by_status['rejected'] ?? 0;
  const totalAll = stats?.total ?? 0;

  return (
    <main className="flex-grow w-full max-w-[90rem] mx-auto px-4 sm:px-6 lg:px-8 py-10 lg:py-12 flex flex-col gap-6 page-enter">
      <div className="flex flex-col gap-2">
        <h1 className="font-display-lg text-display-lg text-primary dark:text-dark-primary">
          KV Pair Verification
        </h1>
        <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant">
          Review concept-entity pairs with retrieved hadiths for cross-concept alignment training.
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-surface dark:bg-dark-surface p-4 rounded-lg border border-outline dark:border-dark-outline">
          <div className="text-2xl font-bold text-on-surface dark:text-dark-on-surface">{totalAll}</div>
          <div className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant">Total</div>
        </div>
        <div className="bg-surface dark:bg-dark-surface p-4 rounded-lg border border-outline dark:border-dark-outline">
          <div className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">{pending}</div>
          <div className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant">Pending</div>
        </div>
        <div className="bg-surface dark:bg-dark-surface p-4 rounded-lg border border-outline dark:border-dark-outline">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">{verified}</div>
          <div className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant">Verified</div>
        </div>
        <div className="bg-surface dark:bg-dark-surface p-4 rounded-lg border border-outline dark:border-dark-outline">
          <div className="text-2xl font-bold text-red-600 dark:text-red-400">{rejected}</div>
          <div className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant">Rejected</div>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {(['all', ...STATUS_FILTERS] as StatusFilter[]).map((f) => (
          <button
            key={f}
            onClick={() => handleFilterChange(f)}
            className={`px-3 py-1.5 text-sm rounded-lg capitalize transition-colors ${
              statusFilter === f
                ? 'bg-primary dark:bg-dark-primary text-on-primary dark:text-dark-on-primary font-medium'
                : 'text-on-surface-variant dark:text-dark-on-surface-variant hover:bg-surface-container dark:hover:bg-dark-surface-container'
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-error-container text-on-error-container p-4 rounded-lg">
          Error: {error}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-20">
          <LoadingSpinner />
        </div>
      ) : pairs.length === 0 ? (
        <div className="bg-surface dark:bg-dark-surface p-8 rounded-lg border border-outline dark:border-dark-outline text-center text-on-surface-variant dark:text-dark-on-surface-variant">
          No KV pairs found for this filter.
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {pairs.map((pair) => (
            <div
              key={pair.id}
              className="bg-surface dark:bg-dark-surface p-5 rounded-lg border border-outline dark:border-dark-outline flex flex-col gap-4"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 text-xs font-medium rounded bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
                    #{pair.id}
                  </span>
                  <span className="px-2 py-0.5 text-xs font-medium rounded bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300">
                    {pair.topic}
                  </span>
                </div>
                <span
                  className={`px-2 py-0.5 text-xs font-medium rounded ${
                    pair.status === 'verified'
                      ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                      : pair.status === 'rejected'
                        ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                        : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                  }`}
                >
                  {pair.status}
                </span>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex flex-col gap-3">
                  <div>
                    <div className="text-xs font-medium text-on-surface-variant dark:text-dark-on-surface-variant mb-1">
                      Concept (EN) — the key
                    </div>
                    <div className="text-sm text-on-surface dark:text-dark-on-surface bg-surface-container dark:bg-dark-surface-container p-3 rounded">
                      {pair.concept_en}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-medium text-on-surface-variant dark:text-dark-on-surface-variant mb-1">
                      Entity (EN) — search query used
                    </div>
                    <div className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant italic bg-surface-container dark:bg-dark-surface-container p-3 rounded">
                      {pair.entity_en}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-3">
                  <div>
                    <div className="text-xs font-medium text-on-surface-variant dark:text-dark-on-surface-variant mb-1">
                      Concept (AR)
                    </div>
                    <div dir="rtl" className="text-sm text-on-surface dark:text-dark-on-surface bg-surface-container dark:bg-dark-surface-container p-3 rounded">
                      {pair.concept_ar}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs font-medium text-on-surface-variant dark:text-dark-on-surface-variant mb-1">
                      Entity (AR)
                    </div>
                    <div dir="rtl" className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant italic bg-surface-container dark:bg-dark-surface-container p-3 rounded">
                      {pair.entity_ar}
                    </div>
                  </div>
                </div>
              </div>

              <div className="border-t border-outline dark:border-dark-outline pt-3">
                <div className="text-xs font-medium text-on-surface-variant dark:text-dark-on-surface-variant mb-2">
                  Retrieved Hadith (ID: {pair.hadith_id}) — the value
                </div>
                <div className="grid md:grid-cols-2 gap-3">
                  <div className="text-sm text-on-surface dark:text-dark-on-surface bg-surface-container dark:bg-dark-surface-container p-3 rounded">
                    {pair.hadith_en || 'No English text available'}
                  </div>
                  <div dir="rtl" className="text-sm text-on-surface dark:text-dark-on-surface bg-surface-container dark:bg-dark-surface-container p-3 rounded">
                    {pair.hadith_ar || 'No Arabic text available'}
                  </div>
                </div>
              </div>

              {pair.status === 'pending' && (
                <div className="flex gap-3">
                  <button
                    onClick={() => handleVerify(pair.id, 'verified')}
                    disabled={verifyingId === pair.id}
                    className="flex-1 px-4 py-2 text-sm font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800 disabled:opacity-50 transition-colors"
                  >
                    Verify
                  </button>
                  <button
                    onClick={() => handleVerify(pair.id, 'rejected')}
                    disabled={verifyingId === pair.id}
                    className="flex-1 px-4 py-2 text-sm font-medium rounded-lg bg-red-600 text-white hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800 disabled:opacity-50 transition-colors"
                  >
                    Reject
                  </button>
                </div>
              )}
            </div>
          ))}

          <div className="flex items-center justify-between">
            <button
              onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
              disabled={offset === 0}
              className="px-4 py-2 text-sm rounded-lg border border-outline dark:border-dark-outline text-on-surface-variant dark:text-dark-on-surface-variant hover:bg-surface-container dark:hover:bg-dark-surface-container disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <span className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
              {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} of {total}
            </span>
            <button
              onClick={() => setOffset(offset + PAGE_SIZE)}
              disabled={offset + PAGE_SIZE >= total}
              className="px-4 py-2 text-sm rounded-lg border border-outline dark:border-dark-outline text-on-surface-variant dark:text-dark-on-surface-variant hover:bg-surface-container dark:hover:bg-dark-surface-container disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </main>
  );
};

export default KvVerificationPage;
