import { useContext } from 'react';
import { LanguageContext, type LanguageContextValue } from './LanguageContext';

export const useLanguage = (): LanguageContextValue => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
