import type { AlgorithmResult } from '../types';
import { gradeConfig } from '../data/fakeData';

interface AlgorithmCardProps {
  algorithm: AlgorithmResult;
  variant?: 'default' | 'highlighted';
}

const AlgorithmCard = ({ algorithm, variant = 'default' }: AlgorithmCardProps) => {
  const isHighlighted = variant === 'highlighted';

  return (
    <div className="flex flex-col relative">
      <div
        className={`${
          isHighlighted ? 'bg-surface-container-lowest' : 'bg-surface-container-low'
        } border-b border-outline-variant p-4 flex justify-between items-center shadow-sm`}
      >
        <div className="flex items-center gap-3">
          <div
            className={`w-6 h-6 rounded-full ${algorithm.color} text-on-primary flex items-center justify-center font-ui-label text-ui-caption`}
          >
            {algorithm.shortLabel}
          </div>
          <h3
            className={`font-h1-hadith text-lg ${
              isHighlighted ? 'text-primary' : 'text-on-surface'
            }`}
          >
            {algorithm.algorithmName}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-ui-caption text-ui-caption text-on-surface-variant">
            {algorithm.results.length} results
          </span>
        </div>
      </div>
      <div className={`p-4 space-y-4 ${isHighlighted ? 'bg-surface-container-lowest' : ''}`}>
        {algorithm.results.map((hadith) => (
          <div
            key={hadith.id}
            className="group relative bg-surface border border-outline-variant rounded-lg p-5 hover:shadow-md transition-all duration-300"
          >
            <div className="mb-3 flex items-center gap-2">
              <span
                className={`${gradeConfig[hadith.grade].bgClass} ${gradeConfig[hadith.grade].textClass} font-ui-label text-ui-caption uppercase px-2 py-0.5 rounded-full`}
              >
                {gradeConfig[hadith.grade].label}
              </span>
              <span className="font-ui-caption text-ui-caption text-on-surface-variant">
                {hadith.book}
              </span>
            </div>
            <p className="font-body-main text-body-main text-on-surface mb-2">
              {hadith.englishText}
            </p>
            <p
              className="font-body-arabic text-[20px] text-on-surface/70 text-right leading-[2]"
              dir="rtl"
            >
              {hadith.arabicText.substring(0, 100)}...
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AlgorithmCard;
