import type { SearchResult } from '../types';

export const GRADE_ORDER: Record<string, number> = {
  'Sahih': 0,
  'Hasan': 1,
  "Da'if (Weak)": 2,
  'Maudu (Fabricated)': 3,
  'Unknown': 4,
};

export function sortByGradeAndRelevance(results: SearchResult[]): SearchResult[] {
  return [...results].sort((a, b) => {
    const gradeDiff =
      (GRADE_ORDER[a.hadith.grade] ?? 4) - (GRADE_ORDER[b.hadith.grade] ?? 4);
    if (gradeDiff !== 0) return gradeDiff;
    return b.score - a.score;
  });
}

export function sortByRelevance(results: SearchResult[]): SearchResult[] {
  return [...results].sort((a, b) => b.score - a.score);
}
