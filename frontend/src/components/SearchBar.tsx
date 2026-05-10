import { useState } from 'react';
import { useLanguage } from '../i18n/useLanguage';
import type { Lang } from '../types';

interface SearchBarProps {
  onSearch: (query: string, lang: Lang) => void;
  placeholder?: string;
  compact?: boolean;
  initialQuery?: string;
  disabled?: boolean;
}

const detectArabic = (text: string): boolean => {
  for (let i = 0; i < text.length; i++) {
    const code = text.charCodeAt(i);
    if (code >= 0x0600 && code <= 0x06FF) return true;
  }
  return false;
};

const SearchBar = ({ onSearch, placeholder, compact = false, initialQuery = '', disabled = false }: SearchBarProps) => {
  const { t, language } = useLanguage();
  const [query, setQuery] = useState(initialQuery);
  const [autoDetectedLang, setAutoDetectedLang] = useState<Lang>(detectArabic(initialQuery) ? 'ar' : 'en');
  const [manualLang, setManualLang] = useState<Lang | null>(null);
  const effectiveLang: Lang = manualLang ?? autoDetectedLang;

  const handleChange = (value: string) => {
    setQuery(value);
    if (value.trim() === '') {
      setManualLang(null);
      setAutoDetectedLang('en');
    } else {
      const detected = detectArabic(value) ? 'ar' : 'en';
      setAutoDetectedLang(detected);
    }
  };

  const handleLangToggle = () => {
    setManualLang((prev) => (prev === null ? (language === 'ar' ? 'en' : 'ar') : prev === 'en' ? 'ar' : 'en'));
  };

  const handleSubmit = () => {
    if (query.trim()) {
      onSearch(query.trim(), effectiveLang);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  return (
    <div className="w-full">
      <div className="flex items-center gap-2 mb-2">
        <button
          type="button"
          onClick={handleLangToggle}
          className={`flex items-center gap-1 px-2 py-1 rounded border text-[12px] font-ui-label transition-colors ${
            manualLang !== null
              ? 'bg-primary/10 border-primary/30 text-primary dark:text-dark-primary'
              : 'bg-surface dark:bg-dark-surface border-outline dark:border-dark-outline text-on-surface-variant dark:text-dark-on-surface-variant hover:border-primary dark:hover:border-dark-primary'
          }`}
          title={manualLang !== null ? 'Manual language selected. Clear input to reset.' : 'Auto-detect active'}
        >
          <span className={manualLang !== null ? 'opacity-100' : 'opacity-50'}>EN</span>
          <span className="text-[10px] text-outline dark:text-dark-outline">/</span>
          <span className={manualLang !== null ? 'opacity-100' : 'opacity-50'}>AR</span>
        </button>
        {manualLang !== null && (
          <span className="text-[11px] text-on-surface-variant dark:text-dark-on-surface-variant font-ui-caption">
            {manualLang === 'en' ? 'English' : 'عربي'}
          </span>
        )}
      </div>
      <div className="flex items-center gap-3">
        <div className="relative w-full group">
          <div className="absolute inset-y-0 start-6 flex items-center pointer-events-none">
            <span className="material-symbols-outlined text-secondary dark:text-dark-secondary fill group-focus-within:text-primary dark:group-focus-within:text-dark-primary transition-colors duration-300">
              search
            </span>
          </div>
          <input
            className={`w-full ${compact ? 'h-12 ps-14' : 'h-16 ps-16'} rounded-full border-2 border-outline-variant dark:border-dark-outline-variant bg-surface-container-lowest dark:bg-dark-surface-container-lowest text-on-surface dark:text-dark-on-surface font-ui-label text-ui-label focus:border-secondary dark:focus:border-dark-secondary focus:ring-4 focus:ring-secondary-container/30 dark:focus:ring-dark-secondary-container/30 transition-all shadow-sm placeholder:text-outline dark:placeholder:text-dark-outline`}
            placeholder={placeholder || t('search.placeholder')}
            type="text"
            value={query}
            onChange={(e) => handleChange(e.target.value)}
            onKeyDown={handleKeyDown}
            dir={effectiveLang === 'ar' ? 'rtl' : 'ltr'}
            style={{ textAlign: effectiveLang === 'ar' ? 'right' : 'left' }}
          />
        </div>
        <button
          type="button"
          onClick={handleSubmit}
          disabled={disabled || !query.trim()}
          className={`shrink-0 ${compact ? 'h-12 px-4' : 'h-16 px-6'} bg-primary dark:bg-dark-primary text-on-primary dark:text-dark-on-primary rounded-full font-ui-label text-ui-label hover:bg-primary-container dark:hover:bg-dark-primary-container transition-all duration-200 flex items-center gap-2 hover:shadow-md active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          <span className="material-symbols-outlined text-[18px]">search</span>
          {!compact && t('search.button')}
        </button>
      </div>
    </div>
  );
};

export default SearchBar;
