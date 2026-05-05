import { hadithOfTheDay, gradeConfig } from '../data/fakeData';
import IslamicMotif from './IslamicMotif';

const HadithOfTheDay = () => {
  const hadith = hadithOfTheDay;
  const config = gradeConfig[hadith.grade];

  return (
    <div className="w-full max-w-4xl mx-auto animate-fade-in-up">
      <div className="relative bg-primary-container text-on-primary-container rounded-2xl p-8 md:p-12 overflow-hidden islamic-frame">
        {/* Subtle girih pattern overlay */}
        <div className="absolute inset-0 girih-bg opacity-30 pointer-events-none" />

        {/* Shimmer accent line */}
        <div className="absolute top-0 left-0 right-0 h-1 shimmer" />

        {/* Corner decorations */}
        <div className="absolute top-4 right-4 opacity-20">
          <IslamicMotif size="sm" className="!bg-secondary-fixed-dim" />
        </div>
        <div className="absolute bottom-4 left-4 opacity-20 rotate-180">
          <IslamicMotif size="sm" className="!bg-secondary-fixed-dim" />
        </div>

        <div className="relative z-10 flex flex-col items-center gap-6">
          {/* Label */}
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined fill text-secondary-fixed-dim text-[20px]">
              auto_awesome
            </span>
            <span className="font-ui-label text-ui-label uppercase tracking-widest text-secondary-fixed-dim">
              Hadith of the Day
            </span>
            <span className="material-symbols-outlined fill text-secondary-fixed-dim text-[20px]">
              auto_awesome
            </span>
          </div>

          {/* Arabic text */}
          <p
            className="font-body-arabic text-[32px] leading-[2.4] text-center text-on-primary-container max-w-3xl"
            dir="rtl"
            style={{ textShadow: '0 1px 2px rgba(0,0,0,0.1)' }}
          >
            {hadith.arabicText}
          </p>

          {/* Divider */}
          <div className="flex items-center gap-3 w-full max-w-md">
            <div className="flex-1 h-px bg-secondary-fixed-dim/30" />
            <div className="w-2 h-2 bg-secondary-fixed-dim/50 rotate-45" />
            <div className="flex-1 h-px bg-secondary-fixed-dim/30" />
          </div>

          {/* English translation */}
          <p className="font-body-main text-body-main text-on-primary-container/80 text-center max-w-2xl leading-relaxed">
            {hadith.englishText}
          </p>

          {/* Attribution */}
          <div className="flex items-center gap-3 mt-2">
            <span
              className={`${config.bgClass} ${config.textClass} font-ui-label text-ui-caption uppercase px-3 py-1 rounded-full`}
              style={{ boxShadow: `0 2px 8px ${config.hex}40` }}
            >
              {config.label}
            </span>
            <span className="font-ui-caption text-ui-caption text-on-primary-container/60">
              {hadith.book} • {hadith.narrator}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HadithOfTheDay;
