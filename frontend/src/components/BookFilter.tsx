import { useLanguage } from '../i18n/useLanguage';

interface BookFilterProps {
  value: string | null;
  onChange: (value: string | null) => void;
}

const books = [
  { value: null, labelKey: 'books.all' },
  { value: 'Sahih al-Bukhari', labelKey: 'books.sahih-al-bukhari' },
  { value: 'Sahih Muslim', labelKey: 'books.sahih-muslim' },
  { value: 'Jami` at-Tirmidhi', labelKey: 'books.jami-al-tirmidhi' },
  { value: 'Sunan Abi Dawud', labelKey: 'books.sunan-abu-dawud' },
  { value: 'Sunan Ibn Majah', labelKey: 'books.sunan-ibn-majah' },
  { value: "Sunan an-Nasa'i", labelKey: 'books.sunan-al-nasai' },
];

const BookFilter = ({ value, onChange }: BookFilterProps) => {
  const { t } = useLanguage();

  return (
    <div className="relative">
      <label className="block font-ui-label text-ui-label mb-1 text-on-surface-variant dark:text-dark-on-surface-variant">
        {t('filter.book')}
      </label>
      <select
        value={value ?? 'all'}
        onChange={(e) => onChange(e.target.value === 'all' ? null : e.target.value)}
        className="w-full sm:w-auto px-4 py-2.5 bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg text-on-surface dark:text-dark-on-surface font-ui-label text-ui-label focus:ring-2 focus:ring-primary dark:focus:ring-dark-primary cursor-pointer"
      >
        {books.map(({ value: v, labelKey }) => (
          <option key={v ?? 'all'} value={v ?? 'all'}>
            {t(labelKey)}
          </option>
        ))}
      </select>
    </div>
  );
};

export default BookFilter;