import { API_BASE_URL } from './config';
import { validateSearchResponse, validateBenchmarkResults } from './validators';
import type { SearchResponse, BenchmarkResults, SearchRequest } from '../types';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export const searchHadiths = async (
  algorithm: string,
  request: SearchRequest
): Promise<SearchResponse> => {
  const response = await fetch(`${API_BASE_URL}/search/${algorithm}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new ApiError(`Search failed: ${response.status} ${response.statusText}`, response.status);
  }

  const data = await response.json();
  return validateSearchResponse(data);
};

export const getBenchmarkResults = async (signal?: AbortSignal): Promise<BenchmarkResults> => {
  const response = await fetch(`${API_BASE_URL}/benchmark/results`, { signal });

  if (!response.ok) {
    throw new ApiError(`Benchmark fetch failed: ${response.status}`, response.status);
  }

  const data = await response.json();
  return validateBenchmarkResults(data);
};

export const getBenchmarkQrels = async (signal?: AbortSignal) => {
  const response = await fetch(`${API_BASE_URL}/benchmark/qrels`, { signal });

  if (!response.ok) {
    throw new ApiError(`Qrels fetch failed: ${response.status}`, response.status);
  }

  return response.json();
};

export const getHadithById = async (id: number, signal?: AbortSignal) => {
  const response = await fetch(`${API_BASE_URL}/hadith/${id}`, { signal });

  if (!response.ok) {
    throw new ApiError(`Hadith fetch failed: ${response.status}`, response.status);
  }

  return response.json();
};

export const getAnnotationQueries = async (signal?: AbortSignal) => {
  const response = await fetch(`${API_BASE_URL}/annotation/queries`, { signal });

  if (!response.ok) {
    throw new ApiError(`Annotation queries fetch failed: ${response.status}`, response.status);
  }

  return response.json();
};

export const getAnnotationCurrent = async (queryId: string, signal?: AbortSignal) => {
  const response = await fetch(`${API_BASE_URL}/annotation/${queryId}/current`, { signal });

  if (!response.ok) {
    throw new ApiError(`Annotation current fetch failed: ${response.status}`, response.status);
  }

  return response.json();
};

export const saveAnnotationLabel = async (queryId: string, payload: { hadith_id: number; index: number; label: number }, signal?: AbortSignal) => {
  const response = await fetch(`${API_BASE_URL}/annotation/${queryId}/label`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal
  });

  if (!response.ok) {
    throw new ApiError(`Annotation label save failed: ${response.status}`, response.status);
  }

  return response.json();
};

export const navigateAnnotation = async (queryId: string, index: number, signal?: AbortSignal) => {
  const response = await fetch(`${API_BASE_URL}/annotation/${queryId}/navigate?index=${index}`, {
    method: 'POST',
    signal
  });

  if (!response.ok) {
    throw new ApiError(`Annotation navigate failed: ${response.status}`, response.status);
  }

  return response.json();
};