import { useState, useCallback, useEffect, type ReactNode } from 'react';
import { LanguageContext, type Language, type LanguageContextValue } from './LanguageContext';
import en from './translations/en';
import ar from './translations/ar';

type Translations = Record<string, string>;

const translations: Record<Language, Translations> = { en, ar };

const STORAGE_KEY = 'language';

const getInitialLanguage = (): Language => {
  const saved = localStorage.getItem(STORAGE_KEY) as Language | null;
  if (saved === 'en' || saved === 'ar') return saved;
  return 'en';
};

const applyLanguageToDOM = (lang: Language) => {
  const html = document.documentElement;
  if (lang === 'ar') {
    html.setAttribute('dir', 'rtl');
    html.setAttribute('lang', 'ar');
    html.classList.add('rtl');
  } else {
    html.setAttribute('dir', 'ltr');
    html.setAttribute('lang', 'en');
    html.classList.remove('rtl');
  }
};

interface LanguageProviderProps {
  children: ReactNode;
}

export const LanguageProvider = ({ children }: LanguageProviderProps) => {
  const [language, setLanguageState] = useState<Language>(getInitialLanguage);

  const isRTL = language === 'ar';

  // Sync DOM on mount and when language changes
  useEffect(() => {
    applyLanguageToDOM(language);
    localStorage.setItem(STORAGE_KEY, language);
  }, [language]);

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
  }, []);

  const toggleLanguage = useCallback(() => {
    setLanguageState((prev) => (prev === 'en' ? 'ar' : 'en'));
  }, []);

  const t = useCallback(
    (key: string, params?: Record<string, string | number>): string => {
      let value = translations[language][key] || translations.en[key] || key;

      if (params) {
        Object.entries(params).forEach(([paramKey, paramValue]) => {
          value = value.replace(
            new RegExp(`\\{${paramKey}\\}`, 'g'),
            String(paramValue)
          );
        });
      }

      return value;
    },
    [language]
  );

  const value: LanguageContextValue = {
    language,
    setLanguage,
    toggleLanguage,
    t,
    isRTL,
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};
