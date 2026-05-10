import type { SearchResult, Lang } from '../types';
import { GRADE_COLORS, BOOK_DISPLAY_NAMES } from '../constants';

interface HadithCardProps {
  result: SearchResult;
  rank: number;
  lang: Lang;
  onClick: () => void;
}

const HadithCard = ({ result, rank, lang, onClick }: HadithCardProps) => {
  const { hadith, score } = result;
  const gradeConfig = GRADE_COLORS[hadith.grade] ?? GRADE_COLORS['Unknown'];

  const getBookDisplayName = () => {
    const entry = BOOK_DISPLAY_NAMES[hadith.book];
    if (entry) return lang === 'ar' ? entry.ar : entry.en;
    return hadith.book;
  };

  return (
    <article
      onClick={onClick}
      className="bg-surface-container-lowest dark:bg-dark-surface-container-lowest border border-outline-variant dark:border-dark-outline-variant rounded-xl p-4 sm:p-5 md:p-6 flex flex-col gap-3 hover:shadow-lg hover:border-primary/30 dark:hover:border-dark-primary/30 cursor-pointer transition-all duration-300 group"
    >
      <div className="flex items-start gap-3 sm:gap-4">
        <div className="flex flex-col items-center gap-1 min-w-[40px] sm:min-w-[48px]">
          <span className="text-2xl sm:text-3xl font-bold text-primary/50 dark:text-dark-primary/50 group-hover:text-primary dark:group-hover:text-dark-primary transition-colors">
            {rank}
          </span>
          <span className="text-[10px] sm:text-xs font-ui-label text-on-surface-variant/50 dark:text-dark-on-surface-variant/50">
            {score.toFixed(4)}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span
              className={`${gradeConfig.bg} ${gradeConfig.text} font-ui-label text-ui-caption px-2.5 py-0.5 rounded-full uppercase tracking-wide`}
            >
              {hadith.raw_grade}
            </span>
            <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">
              {getBookDisplayName()}
            </span>
            <span className="text-on-surface-variant/30 dark:text-dark-on-surface-variant/30">•</span>
            <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">
              {hadith.reference}
            </span>
          </div>
          <h3 className="font-h1-hadith text-sm sm:text-base text-on-surface dark:text-dark-on-surface group-hover:text-primary dark:group-hover:text-dark-primary transition-colors line-clamp-1">
            {lang === 'ar' ? hadith.chapter_title_ar : hadith.chapter_title_en}
          </h3>
          {hadith.chapter_title_ar !== hadith.chapter_title_en && lang === 'ar' && (
            <p className="font-h1-hadith text-xs text-on-surface-variant dark:text-dark-on-surface-variant text-right" dir="rtl">
              {hadith.chapter_title_en}
            </p>
          )}
        </div>
      </div>

      <div className="h-px bg-outline-variant/40 dark:bg-dark-outline-variant/40" />

      {lang === 'ar' ? (
        <p
          className="font-body-arabic text-xl sm:text-2xl text-on-surface dark:text-dark-on-surface text-right leading-[1.9]"
          dir="rtl"
        >
          {hadith.hadith_ar_text}
        </p>
      ) : (
        <p className="font-body-main text-xl sm:text-2xl text-on-surface dark:text-dark-on-surface leading-relaxed">
          {hadith.hadith_en_text}
        </p>
      )}

      <div className="flex items-center gap-2 flex-wrap">
        <span className="material-symbols-outlined text-base text-primary/60 dark:text-dark-primary/60">bookmark</span>
        <span className="font-ui-label text-ui-label px-3 py-1 bg-surface-container dark:bg-dark-surface-container border border-outline-variant dark:border-dark-outline-variant rounded-full text-on-surface-variant dark:text-dark-on-surface-variant">
          {hadith.in_book_reference}
        </span>
      </div>
    </article>
  );
};

export default HadithCard;
