import { useEffect, useCallback } from 'react';
import type { SearchResult, Lang } from '../types';
import { GRADE_COLORS, BOOK_DISPLAY_NAMES } from '../constants';
import { useLanguage } from '../i18n/useLanguage';

interface HadithModalProps {
  result: SearchResult | null;
  rank?: number;
  lang: Lang;
  onClose: () => void;
}

const HadithModal = ({ result, rank, lang, onClose }: HadithModalProps) => {
  const { t } = useLanguage();

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (result) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [result, handleKeyDown]);

  if (!result) return null;

  const { hadith, score } = result;
  const gradeConfig = GRADE_COLORS[hadith.grade] ?? GRADE_COLORS['Unknown'];

  const getBookDisplayName = () => {
    const entry = BOOK_DISPLAY_NAMES[hadith.book];
    if (entry) return lang === 'ar' ? entry.ar : entry.en;
    return hadith.book;
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in"
      onClick={onClose}
    >
      <div
        className="bg-surface dark:bg-dark-surface rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-outline dark:border-dark-outline animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-surface dark:bg-dark-surface border-b border-outline-variant dark:border-dark-outline-variant p-4 sm:p-5 flex items-center justify-between z-10">
          <div className="flex items-center gap-3 flex-wrap">
            {rank !== undefined && (
              <span className="text-2xl sm:text-3xl font-bold text-primary/50 dark:text-dark-primary/50">
                #{rank}
              </span>
            )}
            <div className="flex items-center gap-2 flex-wrap">
              <span
                className={`${gradeConfig.bg} ${gradeConfig.text} font-ui-label text-ui-caption px-2.5 py-0.5 rounded-full uppercase tracking-wide`}
              >
                {hadith.raw_grade}
              </span>
              <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">
                {getBookDisplayName()}
              </span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center rounded-full hover:bg-surface-container dark:hover:bg-dark-surface-container transition-colors text-on-surface-variant dark:text-dark-on-surface-variant shrink-0"
          >
            <span className="material-symbols-outlined text-2xl sm:text-3xl">close</span>
          </button>
        </div>

        <div className="p-4 sm:p-6 flex flex-col gap-5">
          <div className="flex flex-col gap-1.5 text-sm font-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="material-symbols-outlined text-[16px]">tag</span>
              <span>{t('results.reference')}: {hadith.reference}</span>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="material-symbols-outlined text-[16px]">bookmark</span>
              <span>{t('results.inBookRef')}: </span>
              <span className="font-ui-label text-ui-label px-3 py-1 bg-primary/10 dark:bg-dark-primary/10 border border-primary/30 dark:border-dark-primary/30 rounded-full text-primary dark:text-dark-primary">
                {hadith.in_book_reference}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-[16px]">speed</span>
              <span>{t('results.score')}: {score.toFixed(4)}</span>
            </div>
          </div>

          <div className="bg-surface-container-lowest dark:bg-dark-surface-container-lowest rounded-xl p-4 sm:p-5 border border-outline-variant dark:border-dark-outline-variant">
            <div className="mb-3">
              <span className="material-symbols-outlined text-[16px] mr-2 text-primary/60 dark:text-dark-primary/60">menu_book</span>
              <span className="font-h1-hadith text-base sm:text-lg text-on-surface dark:text-dark-on-surface">
                {lang === 'ar' ? hadith.chapter_title_ar : hadith.chapter_title_en}
              </span>
            </div>
            {hadith.chapter_title_ar !== hadith.chapter_title_en && (
              <p className="font-h1-hadith text-sm text-on-surface-variant dark:text-dark-on-surface-variant text-right mb-3" dir="rtl">
                {lang === 'ar' ? hadith.chapter_title_en : hadith.chapter_title_ar}
              </p>
            )}
            <div className="h-px bg-outline-variant dark:bg-dark-outline-variant mb-4" />
            <p
              className="font-body-arabic text-xl sm:text-2xl text-on-surface dark:text-dark-on-surface text-right leading-[2] mb-4"
              dir="rtl"
            >
              {hadith.hadith_ar_text}
            </p>
            <div className="h-px bg-outline-variant dark:bg-dark-outline-variant mb-4" />
            <p className="font-body-main text-xl sm:text-2xl text-on-surface dark:text-dark-on-surface leading-relaxed">
              {hadith.hadith_en_text}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HadithModal;
