import { useLanguage } from '../i18n/useLanguage';

export const LanguageToggle = () => {
  const { language, toggleLanguage, t } = useLanguage();

  return (
    <button
      onClick={toggleLanguage}
      className="p-2 rounded-full hover:bg-surface-container dark:hover:bg-dark-surface-container transition-colors duration-200 flex items-center gap-1"
      aria-label={t('language.switch')}
      title={t('language.switch')}
    >
      <span className="material-symbols-outlined text-on-surface dark:text-dark-on-surface text-[20px]">
        translate
      </span>
      <span className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant uppercase">
        {language === 'en' ? t('language.ar') : t('language.en')}
      </span>
    </button>
  );
};
