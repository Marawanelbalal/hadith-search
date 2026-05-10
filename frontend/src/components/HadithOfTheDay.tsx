import { useState, useEffect } from 'react';
import { GRADE_COLORS } from '../constants';
import IslamicMotif from './IslamicMotif';
import LoadingSpinner from './LoadingSpinner';
import { useApi } from '../api/useApi';
import { useLanguage } from '../i18n/useLanguage';

const HOTD_ID_KEY = 'hotd_id';

const HadithOfTheDay = () => {
  const { getHadith, loading, errors } = useApi();
  const { t } = useLanguage();
  const [hadith, setHadith] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    let id = sessionStorage.getItem(HOTD_ID_KEY);
    if (!id) {
      const randomId = Math.floor(Math.random() * 33738) + 1;
      id = String(randomId);
      sessionStorage.setItem(HOTD_ID_KEY, id);
    }

    getHadith(Number(id)).then((result) => {
      if (result) setHadith(result);
    });
  }, [getHadith]);

  if (loading.hadith) {
    return (
      <div className="w-full max-w-4xl mx-auto flex flex-col items-center py-12 gap-4">
        <LoadingSpinner />
        <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant">
          {t('loading.subtitle')}
        </p>
      </div>
    );
  }

  if (errors.hadith || !hadith) {
    return null;
  }

  const grade = (hadith.Normalized_Grade || hadith.grade) as string;
  const rawGrade = (hadith.Grade || hadith.raw_grade || grade) as string;
  const gradeConfig = GRADE_COLORS[grade] ?? GRADE_COLORS['Unknown'];

  const arabicText = (hadith.Arabic_Text || hadith.arabic_text || '') as string;
  const englishText = (hadith.English_Text || hadith.english_text || '') as string;
  const book = (hadith.Book || hadith.book || '') as string;
  const chapterEn = (hadith.Chapter_Title_English || hadith.chapter_title_en || '') as string;

  return (
    <div className="w-full max-w-4xl mx-auto animate-fade-in-up">
      <div className="relative bg-primary-container dark:bg-dark-primary-container text-on-primary-container dark:text-dark-on-primary-container rounded-2xl p-8 md:p-12 overflow-hidden islamic-frame">
        <div className="absolute inset-0 girih-bg opacity-30 pointer-events-none" />
        <div className="absolute top-0 start-0 end-0 h-1 shimmer" />
        <div className="absolute top-4 end-4 opacity-20">
          <IslamicMotif size="sm" className="!bg-secondary-fixed-dim" />
        </div>
        <div className="absolute bottom-4 start-4 opacity-20 rotate-180">
          <IslamicMotif size="sm" className="!bg-secondary-fixed-dim" />
        </div>

        <div className="relative z-10 flex flex-col items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined fill text-secondary-fixed-dim dark:text-dark-secondary text-[20px]">
              auto_awesome
            </span>
            <span className="font-ui-label text-ui-label uppercase tracking-widest text-secondary-fixed-dim dark:text-dark-secondary">
              {t('hotd.label')}
            </span>
            <span className="material-symbols-outlined fill text-secondary-fixed-dim dark:text-dark-secondary text-[20px]">
              auto_awesome
            </span>
          </div>

          <p
            className="font-body-arabic text-[28px] md:text-[32px] leading-[1.8] text-center text-on-primary-container dark:text-dark-on-primary-container max-w-3xl"
            dir="rtl"
          >
            {arabicText}
          </p>

          <div className="flex items-center gap-3 w-full max-w-md">
            <div className="flex-1 h-px bg-secondary-fixed-dim/30 dark:bg-dark-secondary/30" />
            <div className="w-2 h-2 bg-secondary-fixed-dim/50 dark:bg-dark-secondary/50 rotate-45" />
            <div className="flex-1 h-px bg-secondary-fixed-dim/30 dark:bg-dark-secondary/30" />
          </div>

          <p className="font-body-main text-body-main text-on-primary-container/80 dark:text-dark-on-primary-container/80 text-center max-w-2xl leading-relaxed">
            {englishText}
          </p>

          <div className="flex items-center gap-3 mt-2">
            {rawGrade ? (
              <span
                className={`${gradeConfig.bg} ${gradeConfig.text} font-ui-label text-ui-caption uppercase px-3 py-1 rounded-full`}
              >
                {rawGrade}
              </span>
            ) : null}
            <span className="font-ui-caption text-ui-caption text-on-primary-container/60 dark:text-dark-on-primary-container/60">
              {book} • {chapterEn}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HadithOfTheDay;