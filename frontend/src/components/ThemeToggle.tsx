import { useTheme } from '../hooks/useTheme';

export const ThemeToggle = () => {
  const { isDark, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-full hover:bg-surface-container dark:hover:bg-dark-surface-container transition-colors duration-200"
      aria-label="Toggle theme"
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
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
