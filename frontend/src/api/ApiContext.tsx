import { createContext, useState, useRef, useCallback, useMemo, type ReactNode } from 'react';
import { searchHadiths, getBenchmarkResults, getBenchmarkQrels, getHadithById } from './services';
import type { SearchResponse, BenchmarkResults, SearchRequest } from '../types';

interface ApiState {
  loading: {
    search: boolean;
    benchmarks: boolean;
    hadith: boolean;
  };
  errors: {
    search: string | null;
    benchmarks: string | null;
    hadith: string | null;
  };
}

export interface ApiContextValue extends ApiState {
  search: (algorithm: string, request: SearchRequest) => Promise<SearchResponse>;
  getBenchmarks: () => Promise<BenchmarkResults>;
  getQrels: () => Promise<{ qrels: Record<string, { query: string; grades: Record<string, unknown> }> }>;
  getHadith: (id: number) => Promise<Record<string, unknown> | null>;
  cancelSearch: () => void;
  cancelBenchmarks: () => void;
  cancelHadith: () => void;
  clearError: (operation: keyof ApiState['errors']) => void;
}

export const ApiContext = createContext<ApiContextValue | null>(null);

export const ApiProvider = ({ children }: { children: ReactNode }) => {
  const [loading, setLoading] = useState<ApiState['loading']>({
    search: false,
    benchmarks: false,
    hadith: false,
  });

  const [errors, setErrors] = useState<ApiState['errors']>({
    search: null,
    benchmarks: null,
    hadith: null,
  });

  const searchControllerRef = useRef<AbortController | null>(null);
  const benchmarksControllerRef = useRef<AbortController | null>(null);
  const qrelsControllerRef = useRef<AbortController | null>(null);
  const hadithControllerRef = useRef<AbortController | null>(null);

  const clearError = useCallback((operation: keyof ApiState['errors']) => {
    setErrors((prev) => ({ ...prev, [operation]: null }));
  }, []);

  const cancelSearch = useCallback(() => {
    searchControllerRef.current?.abort();
    searchControllerRef.current = null;
    setLoading((prev) => ({ ...prev, search: false }));
  }, []);

  const cancelBenchmarks = useCallback(() => {
    benchmarksControllerRef.current?.abort();
    benchmarksControllerRef.current = null;
    setLoading((prev) => ({ ...prev, benchmarks: false }));
  }, []);

  const cancelHadith = useCallback(() => {
    hadithControllerRef.current?.abort();
    hadithControllerRef.current = null;
    setLoading((prev) => ({ ...prev, hadith: false }));
  }, []);

  const search = useCallback(async (algorithm: string, request: SearchRequest, externalSignal?: AbortSignal): Promise<SearchResponse> => {
    if (searchControllerRef.current) {
      searchControllerRef.current.abort();
    }
    const controller = new AbortController();
    searchControllerRef.current = controller;

    const signal = externalSignal ?? controller.signal;

    setLoading((prev) => ({ ...prev, search: true }));
    setErrors((prev) => ({ ...prev, search: null }));

    try {
      const result = await searchHadiths(algorithm, request, signal);
      setLoading((prev) => ({ ...prev, search: false }));
      return result;
    } catch (err) {
      setLoading((prev) => ({ ...prev, search: false }));
      if (err instanceof DOMException && err.name === 'AbortError') {
        return { number_of_results: 0, results: [] };
      }
      const message = err instanceof Error ? err.message : 'Search failed';
      setErrors((prev) => ({ ...prev, search: message }));
      return { number_of_results: 0, results: [] };
    }
  }, []);

  const getBenchmarks = useCallback(async (): Promise<BenchmarkResults> => {
    if (benchmarksControllerRef.current) {
      benchmarksControllerRef.current.abort();
    }
    const controller = new AbortController();
    benchmarksControllerRef.current = controller;

    setLoading((prev) => ({ ...prev, benchmarks: true }));
    setErrors((prev) => ({ ...prev, benchmarks: null }));

    try {
      const result = await getBenchmarkResults(controller.signal);
      setLoading((prev) => ({ ...prev, benchmarks: false }));
      return result;
    } catch (err) {
      setLoading((prev) => ({ ...prev, benchmarks: false }));
      if (err instanceof DOMException && err.name === 'AbortError') {
        return {};
      }
      const message = err instanceof Error ? err.message : 'Benchmark fetch failed';
      setErrors((prev) => ({ ...prev, benchmarks: message }));
      return {};
    }
  }, []);

  const getQrels = useCallback(async () => {
    if (qrelsControllerRef.current) {
      qrelsControllerRef.current.abort();
    }
    const controller = new AbortController();
    qrelsControllerRef.current = controller;

    setLoading((prev) => ({ ...prev, benchmarks: true }));
    setErrors((prev) => ({ ...prev, benchmarks: null }));

    try {
      const result = await getBenchmarkQrels(controller.signal);
      setLoading((prev) => ({ ...prev, benchmarks: false }));
      return result as { qrels: Record<string, { query: string; grades: Record<string, unknown> }> };
    } catch (err) {
      setLoading((prev) => ({ ...prev, benchmarks: false }));
      if (err instanceof DOMException && err.name === 'AbortError') {
        return { qrels: {} };
      }
      const message = err instanceof Error ? err.message : 'Qrels fetch failed';
      setErrors((prev) => ({ ...prev, benchmarks: message }));
      return { qrels: {} };
    }
  }, []);

  const getHadith = useCallback(async (id: number) => {
    if (hadithControllerRef.current) {
      hadithControllerRef.current.abort();
    }
    const controller = new AbortController();
    hadithControllerRef.current = controller;

    setLoading((prev) => ({ ...prev, hadith: true }));
    setErrors((prev) => ({ ...prev, hadith: null }));

    try {
      const result = await getHadithById(id, controller.signal);
      setLoading((prev) => ({ ...prev, hadith: false }));
      return result;
    } catch (err) {
      setLoading((prev) => ({ ...prev, hadith: false }));
      if (err instanceof DOMException && err.name === 'AbortError') {
        return null;
      }
      const message = err instanceof Error ? err.message : 'Hadith fetch failed';
      setErrors((prev) => ({ ...prev, hadith: message }));
      return null;
    }
  }, []);

  const value = useMemo<ApiContextValue>(() => ({
    loading,
    errors,
    search,
    getBenchmarks,
    getQrels,
    getHadith,
    cancelSearch,
    cancelBenchmarks,
    cancelHadith,
    clearError,
  }), [loading, errors, search, getBenchmarks, getQrels, getHadith, cancelSearch, cancelBenchmarks, cancelHadith, clearError]);

  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>;
};