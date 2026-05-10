import { useTheme } from '../hooks/useTheme';
import { useLanguage } from '../i18n/useLanguage';

export const ThemeToggle = () => {
  const { isDark, toggleTheme } = useTheme();
  const { t } = useLanguage();

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-full hover:bg-surface-container dark:hover:bg-dark-surface-container transition-colors duration-200"
      aria-label={t('theme.toggle')}
      title={isDark ? t('theme.switchToLight') : t('theme.switchToDark')}
    >
      {isDark ? (
        <span className="material-symbols-outlined text-on-surface dark:text-dark-on-surface">
          light_mode
        </span>
      ) : (
        <span className="material-symbols-outlined text-on-surface dark:text-dark-on-surface">
          dark_mode
        </span>
      )}
    </button>
  );
};
