import type { SearchResponse, BenchmarkResults } from '../types';

export class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

const isObject = (v: unknown): v is Record<string, unknown> => typeof v === 'object' && v !== null && !Array.isArray(v);
const isString = (v: unknown): v is string => typeof v === 'string';
const isNumber = (v: unknown): v is number => typeof v === 'number';

export const validateSearchResult = (data: unknown, index: number) => {
  if (!isObject(data)) throw new ValidationError(`Invalid search result at index ${index}`);
  if (!isObject(data.hadith)) throw new ValidationError(`Invalid search result at index ${index}: missing hadith`);
  const h = data.hadith as Record<string, unknown>;
  if (!isNumber(h.hadith_id) && !isString(h.hadith_id)) throw new ValidationError(`Invalid hadith: missing hadith_id at index ${index}`);
  if (!isString(h.book)) throw new ValidationError(`Invalid hadith: missing book at index ${index}`);
  if (!isString(h.hadith_en_text)) throw new ValidationError(`Invalid hadith: missing hadith_en_text at index ${index}`);
  if (!isString(h.hadith_ar_text)) throw new ValidationError(`Invalid hadith: missing hadith_ar_text at index ${index}`);
  if (!isString(h.chapter_title_ar)) throw new ValidationError(`Invalid hadith: missing chapter_title_ar at index ${index}`);
  if (!isString(h.chapter_title_en)) throw new ValidationError(`Invalid hadith: missing chapter_title_en at index ${index}`);
  if (!isString(h.grade)) throw new ValidationError(`Invalid hadith: missing grade at index ${index}`);
  if (!isString(h.reference)) throw new ValidationError(`Invalid hadith: missing reference at index ${index}`);
  if (!isString(h.in_book_reference)) throw new ValidationError(`Invalid hadith: missing in_book_reference at index ${index}`);
  if (!isNumber(data.score) && typeof data.score !== 'number') throw new ValidationError(`Invalid search result: missing score at index ${index}`);
};

export const validateSearchResponse = (data: unknown): SearchResponse => {
  if (!isObject(data)) throw new ValidationError('Invalid search response: expected object');
  if (!isNumber(data.number_of_results)) throw new ValidationError('Invalid search response: missing number_of_results');
  if (!Array.isArray(data.results)) throw new ValidationError('Invalid search response: missing results array');
  data.results.forEach(validateSearchResult);
  return data as unknown as SearchResponse;
};

export const validateMetrics = (obj: unknown, path: string): void => {
  if (!isObject(obj)) throw new ValidationError(`Invalid metrics at ${path}`);
  const keys = ['AP', 'RR', 'P@20', 'R@20', 'F1@20', 'nDCG@20'];
  for (const k of keys) {
    if (!isNumber((obj as Record<string, unknown>)[k])) {
      throw new ValidationError(`Missing metric ${k} at ${path}`);
    }
  }
};

export const validateBenchmarkResults = (data: unknown): BenchmarkResults => {
  if (!isObject(data)) throw new ValidationError('Invalid benchmark results: expected object');
  for (const [algo, queries] of Object.entries(data)) {
    if (!isObject(queries)) throw new ValidationError(`Invalid benchmark: algorithm ${algo} should be an object`);
    for (const [queryId, result] of Object.entries(queries)) {
      if (!isObject(result)) throw new ValidationError(`Invalid benchmark result for ${algo}/${queryId}`);
      if (result['Query Text'] !== undefined && !isString(result['Query Text'])) {
        throw new ValidationError(`Invalid Query Text for ${algo}/${queryId}`);
      }
      if (!isObject(result.Metrics)) throw new ValidationError(`Missing Metrics for ${algo}/${queryId}`);
      validateMetrics(result.Metrics, `${algo}/${queryId}/Metrics`);
    }
  }
  return data as unknown as BenchmarkResults;
};