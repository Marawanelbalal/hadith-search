import type { Hadith } from '../types';
import { gradeConfig } from '../data/fakeData';

interface HadithCardProps {
  hadith: Hadith;
}

const HadithCard = ({ hadith }: HadithCardProps) => {
  const config = gradeConfig[hadith.grade];

  return (
    <article className="bg-surface-container-lowest dark:bg-dark-surface-container-lowest border border-outline-variant dark:border-dark-outline-variant rounded-lg p-6 md:p-8 flex flex-col gap-6 hover:shadow-[0_4px_20px_rgba(0,81,41,0.08)] dark:hover:shadow-[0_4px_20px_rgba(137,216,158,0.15)] hover:border-primary-container dark:hover:border-dark-primary-container transition-all duration-300 group">
      <div className="flex justify-between items-start border-b border-surface-variant dark:border-dark-surface-variant pb-4">
        <div className="flex flex-col gap-1">
          <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant uppercase tracking-widest">
            {hadith.book}
          </span>
          <h2 className="font-h1-hadith text-h1-hadith text-on-surface dark:text-dark-on-surface group-hover:text-primary dark:group-hover:text-dark-primary transition-colors duration-300">
            Book {hadith.bookNumber}, Hadith {hadith.hadithNumber}
          </h2>
        </div>
        <span
          className={`${config.bgClass} ${config.textClass} font-ui-label text-ui-label px-3 py-1 rounded-full uppercase shadow-sm`}
          style={{ boxShadow: `0 2px 8px ${config.hex}30` }}
        >
          {config.label}
        </span>
      </div>
      <div className="flex flex-col gap-6">
        <p
          className="font-body-arabic text-body-arabic text-on-surface dark:text-dark-on-surface text-right leading-[2.2]"
          dir="rtl"
        >
          {hadith.arabicText}
        </p>
        <div className="flex flex-col gap-2">
          <p className="font-body-main text-body-main text-on-surface dark:text-dark-on-surface leading-relaxed">
            {hadith.englishText}
          </p>
          <div className="flex items-center gap-2 pt-2">
            <span className="material-symbols-outlined text-[16px] text-on-surface-variant dark:text-dark-on-surface-variant">person</span>
            <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">
              {hadith.narrator}
            </span>
            <span className="text-on-surface-variant/30 dark:text-dark-on-surface-variant/30 mx-1">•</span>
            <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant">
              {hadith.topic}
            </span>
          </div>
        </div>
      </div>
    </article>
  );
};

export default HadithCard;
