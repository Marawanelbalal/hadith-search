export type Lang = 'en' | 'ar';
export type Book =
  | 'sahih-al-bukhari'
  | 'sahih-muslim'
  | 'jami-al-tirmidhi'
  | 'sunan-abu-dawud'
  | 'sunan-al-nasai'
  | 'sunan-ibn-majah';

export interface SearchRequest {
  query: string;
  lang: Lang;
  grade_filter?: string | null;
  book_filter?: string | null;
}

export interface Hadith {
  hadith_id: number;
  book: string;
  hadith_en_text: string;
  hadith_ar_text: string;
  chapter_title_ar: string;
  chapter_title_en: string;
  grade: string;
  raw_grade: string;
  reference: string;
  in_book_reference: string;
}

export interface SearchResult {
  hadith: Hadith;
  score: number;
}

export interface SearchResponse {
  number_of_results: number;
  results: SearchResult[];
  response_time_ms?: number;
}

export interface Metrics {
  AP: number;
  RR: number;
  'P@20': number;
  'R@20': number;
  'F1@20': number;
  'nDCG@20': number;
}

export interface QueryBenchmarkResult {
  'Query Text'?: string;
  Metrics: Metrics;
}

export type BenchmarkResults = Record<string, Record<string, QueryBenchmarkResult>>;

export const BOOK_SLUGS = [
  'sahih-al-bukhari',
  'sahih-muslim',
  'jami-al-tirmidhi',
  'sunan-abu-dawud',
  'sunan-al-nasai',
  'sunan-ibn-majah',
] as const;

export const GRADE_COLORS: Record<string, { bg: string; text: string; hex: string }> = {
  'Sahih':              { bg: 'bg-grade-sahih', text: 'text-white', hex: '#16a34a' },
  'Hasan':              { bg: 'bg-grade-hasan', text: 'text-white', hex: '#2563eb' },
  "Da'if (Weak)":       { bg: 'bg-grade-daif', text: 'text-white', hex: '#d97706' },
  'Maudu (Fabricated)': { bg: 'bg-grade-fabricated', text: 'text-white', hex: '#dc2626' },
  'Unknown':            { bg: 'bg-grade-unknown', text: 'text-white', hex: '#6b7280' },
};

export type Algorithm =
  | 'boolean'
  | 'tfidf'
  | 'bm25'
  | 'bm25-tf-idf'
  | 'bm25-prf'
  | 'semantic-rerank'
  | 'cosine-similarity'
  | 'semantic-rrf'
  | 'final-pipeline'
  | 'cross-encoder-rerank';

export const ALGORITHMS: { value: Algorithm; label: string; endpoint: string }[] = [
  { value: 'term-overlap', label: 'Term Overlap', endpoint: 'term-overlap' },
  { value: 'tfidf', label: 'TF-IDF', endpoint: 'tfidf' },
  { value: 'bm25', label: 'BM25', endpoint: 'bm25' },
  { value: 'bm25-tf-idf', label: 'BM25 + TF-IDF (Hybrid)', endpoint: 'bm25-tf-idf' },
  { value: 'bm25-prf', label: 'BM25 + PRF', endpoint: 'bm25-prf' },
  { value: 'semantic-rerank', label: 'Semantic Rerank', endpoint: 'semantic-rerank' },
  { value: 'cosine-similarity', label: 'Cosine Similarity', endpoint: 'cosine-similarity' },
  { value: 'semantic-rrf', label: 'Semantic RRF', endpoint: 'semantic-rrf' },
  { value: 'final-pipeline', label: 'Final Pipeline', endpoint: 'final-pipeline' },
  { value: 'cross-encoder-rerank', label: 'Cross-Encoder Rerank', endpoint: 'cross-encoder-rerank' },
];