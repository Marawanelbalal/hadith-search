import { gradeConfig } from '../data/fakeData';
import type { HadithGrade } from '../types';

interface GradeFilterProps {
  selectedGrade: HadithGrade | 'all';
  onGradeChange: (grade: HadithGrade | 'all') => void;
}

const gradeOrder: (HadithGrade | 'all')[] = ['all', 'sahih', 'hasan-sahih', 'hasan', 'daif-hasan', 'daif'];

const GradeFilter = ({ selectedGrade, onGradeChange }: GradeFilterProps) => {
  return (
    <div className="flex flex-wrap items-center justify-center gap-2">
      <span className="font-ui-caption text-ui-caption text-on-surface-variant uppercase tracking-wider mr-1">
        Grade:
      </span>
      {gradeOrder.map((grade) => {
        const isSelected = selectedGrade === grade;
        const isAll = grade === 'all';

        let bgClass = '';
        let borderClass = '';
        let shadowStyle: React.CSSProperties = {};

        if (isAll) {
          bgClass = isSelected
            ? 'bg-primary text-on-primary shadow-sm'
            : 'bg-surface-container-high text-on-surface';
          borderClass = isSelected ? '' : 'border border-outline-variant';
        } else {
          const config = gradeConfig[grade];
          if (isSelected) {
            bgClass = `${config.bgClass} ${config.textClass} shadow-md`;
            shadowStyle = { boxShadow: `0 4px 14px ${config.hex}40` };
          } else {
            bgClass = 'bg-surface-container-high text-on-surface';
            borderClass = 'border border-outline-variant';
          }
        }

        return (
          <button
            key={grade}
            onClick={() => onGradeChange(grade)}
            className={`px-4 py-2 rounded-full font-ui-label text-ui-label transition-all duration-300 ${bgClass} ${borderClass} ${
              isSelected ? 'scale-105' : 'hover:scale-102'
            } active:scale-95`}
            style={shadowStyle}
          >
            <span className="flex items-center gap-1.5">
              {isSelected && !isAll && (
                <span className="material-symbols-outlined fill text-[14px] animate-fade-in">
                  check
                </span>
              )}
              {isAll ? 'All' : gradeConfig[grade].label}
            </span>
          </button>
        );
      })}
    </div>
  );
};

export default GradeFilter;
