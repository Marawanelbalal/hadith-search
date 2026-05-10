import type { SearchResult } from '../types';
import { GRADE_COLORS, BOOK_DISPLAY_NAMES } from '../constants';
import { useLanguage } from '../i18n/useLanguage';

interface AlgorithmCardProps {
  label: string;
  results: SearchResult[];
  lang: string;
  variant?: 'highlighted' | 'default';
}

const AlgorithmCard = ({ label, results, lang, variant = 'default' }: AlgorithmCardProps) => {
  const { t } = useLanguage();
  const isHighlighted = variant === 'highlighted';

  const getBookDisplayName = (bookName: string) => {
    const entry = BOOK_DISPLAY_NAMES[bookName];
    if (entry) return lang === 'ar' ? entry.ar : entry.en;
    return bookName;
  };

  return (
    <div className="flex flex-col relative">
      <div
        className={`${
          isHighlighted ? 'bg-surface-container-lowest dark:bg-dark-surface-container-lowest' : 'bg-surface-container-low dark:bg-dark-surface-container-low'
        } border-b border-outline-variant dark:border-dark-outline-variant p-4 flex justify-between items-center shadow-sm`}
      >
        <div className="flex items-center gap-3">
          <div
            className={`w-6 h-6 rounded-full ${
              isHighlighted ? 'bg-primary dark:bg-dark-primary' : 'bg-secondary dark:bg-dark-secondary'
            } text-on-primary dark:text-dark-on-primary flex items-center justify-center font-ui-label text-ui-caption`}
          >
            A
          </div>
          <h3
            className={`font-h1-hadith text-lg ${
              isHighlighted ? 'text-primary dark:text-dark-primary' : 'text-on-surface dark:text-dark-on-surface'
            }`}
          >
            {label}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">
            {results.length} {t('dev.results')}
          </span>
        </div>
      </div>
      <div className={`p-4 space-y-4 ${isHighlighted ? 'bg-surface-container-lowest dark:bg-dark-surface-container-lowest' : 'bg-surface-container-low dark:bg-dark-surface-container-low'}`}>
        {results.map((result) => {
          const gradeConfig = GRADE_COLORS[result.hadith.grade] ?? GRADE_COLORS['Unknown'];
          return (
            <div
              key={result.hadith.hadith_id}
              className="group relative bg-surface dark:bg-dark-surface border border-outline-variant dark:border-dark-outline-variant rounded-lg p-5 hover:shadow-md transition-colors duration-300"
            >
              <div className="mb-3 flex items-center gap-2 flex-wrap">
                <span
                  className={`${gradeConfig.bg} ${gradeConfig.text} font-ui-label text-ui-caption uppercase px-2 py-0.5 rounded-full`}
                >
                  {result.hadith.raw_grade}
                </span>
                <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">
                  {getBookDisplayName(result.hadith.book)}
                </span>
                <span className="font-ui-caption text-ui-caption text-primary/60 dark:text-dark-primary/60 ml-auto">
                  {result.score.toFixed(4)}
                </span>
              </div>
              <p className="font-body-main text-body-main text-on-surface dark:text-dark-on-surface mb-2 line-clamp-2">
                {lang === 'ar' ? result.hadith.hadith_ar_text : result.hadith.hadith_en_text}
              </p>
              <p
                className="font-body-arabic text-[18px] text-on-surface/70 dark:text-dark-on-surface/70 text-right leading-[1.8] line-clamp-1"
                dir="rtl"
              >
                {result.hadith.chapter_title_ar}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default AlgorithmCard;