import { useLanguage } from '../i18n/useLanguage';

interface GradeFilterProps {
  value: string | null;
  onChange: (value: string | null) => void;
}

const grades = [
  { value: null, labelKey: 'grades.all' },
  { value: 'Sahih', labelKey: 'grades.sahih' },
  { value: 'Hasan', labelKey: 'grades.hasan' },
  { value: "Da'if (Weak)", labelKey: 'grades.daif' },
];

const GradeFilter = ({ value, onChange }: GradeFilterProps) => {
  const { t } = useLanguage();

  return (
    <div className="relative">
      <label className="block font-ui-label text-ui-label mb-1 text-on-surface-variant dark:text-dark-on-surface-variant">
        {t('filter.grade')}
      </label>
      <select
        value={value ?? 'all'}
        onChange={(e) => onChange(e.target.value === 'all' ? null : e.target.value)}
        className="w-full sm:w-auto px-4 py-2.5 bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg text-on-surface dark:text-dark-on-surface font-ui-label text-ui-label focus:ring-2 focus:ring-primary dark:focus:ring-dark-primary cursor-pointer"
      >
        {grades.map(({ value: v, labelKey }) => (
          <option key={v ?? 'all'} value={v ?? 'all'}>
            {t(labelKey)}
          </option>
        ))}
      </select>
    </div>
  );
};

export default GradeFilter;