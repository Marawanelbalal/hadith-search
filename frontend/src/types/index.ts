export type HadithGrade = 'sahih' | 'hasan-sahih' | 'hasan' | 'daif-hasan' | 'daif';

export interface Hadith {
  id: string;
  book: string;
  bookNumber: number;
  hadithNumber: number;
  grade: HadithGrade;
  arabicText: string;
  englishText: string;
  narrator: string;
  topic: string;
}

export interface Book {
  id: string;
  name: string;
  arabicName: string;
  hadithCount: number;
  description: string;
}

export interface AlgorithmResult {
  id: string;
  algorithmName: string;
  shortLabel: string;
  color: string;
  results: Hadith[];
}

export interface BenchmarkEntry {
  algorithmName: string;
  map: number;
  precisionAt10: number;
  recallAt100: number;
  ndcg: number;
}

export interface NavItem {
  label: string;
  path: string;
  icon: string;
}

export type SearchAlgorithm = 'bm25' | 'bm25-prf' | 'tf-idf' | 'hybrid';
