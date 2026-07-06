import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ThemeToggle } from './ThemeToggle';
import { LanguageToggle } from './LanguageToggle';
import { useLanguage } from '../i18n/useLanguage';

export const APP_MODE_KEY = 'app_mode';

export const getAppMode = (): string => localStorage.getItem(APP_MODE_KEY) || 'user';

export const setAppMode = (mode: string) => localStorage.setItem(APP_MODE_KEY, mode);

interface NavbarProps {
  mode: string;
  onModeChange: (mode: string) => void;
}

const Navbar = ({ mode, onModeChange }: NavbarProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const isDev = mode === 'dev';

  const navLinks = isDev
    ? [
        { labelKey: 'nav.search', path: '/dev/search', icon: 'search' },
        { labelKey: 'nav.benchmarks', path: '/dev/benchmark', icon: 'analytics' },
        { labelKey: 'nav.algorithmComparison', path: '/dev/compare', icon: 'compare_arrows' },
        { labelKey: 'nav.annotation', path: '/dev/annotation', icon: 'edit_note' },
        { labelKey: 'nav.kvPairs', path: '/dev/kv-pairs', icon: 'fact_check' },
      ]
    : [{ labelKey: 'nav.search', path: '/user/search', icon: 'search' }];

  const handleModeToggle = () => {
    const path = location.pathname;
    const isLanding = path === '/user/' || path === '/dev/';
    const isSearch = path === '/user/search' || path === '/dev/search';

    if (isDev) {
      if (isSearch) {
        navigate('/user/search');
      } else {
        navigate('/user/');
      }
    } else {
      navigate('/dev/search');
    }
    onModeChange(isDev ? 'user' : 'dev');
  };

  return (
    <header className="bg-surface dark:bg-dark-surface font-newsreader text-on-surface dark:text-dark-on-surface sticky top-0 border-b border-outline dark:border-dark-outline z-50">
      <div className="flex justify-between items-center w-full px-6 py-4 max-w-[1200px] mx-auto">
        <div className="flex items-center gap-4">
          <Link
            to={isDev ? '/dev/search' : '/user/'}
            className="text-2xl font-bold tracking-tight text-primary dark:text-dark-primary flex items-center gap-2 group"
          >
            <span className="material-symbols-outlined fill text-primary dark:text-dark-primary group-hover:rotate-90 transition-transform duration-500">
              star
            </span>
            <span className="font-display-lg text-[24px]">{t('home.title')}</span>
          </Link>
          {isDev && (
            <span className="px-2 py-0.5 rounded-full bg-primary-container dark:bg-dark-primary-container text-on-primary-container dark:text-dark-on-primary-container font-ui-caption text-ui-caption uppercase tracking-wider font-bold">
              {t('mode.dev')}
            </span>
          )}
        </div>
        <nav className="hidden md:flex gap-1 items-center font-ui-label text-ui-label">
          {navLinks.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`relative flex items-center gap-1.5 py-2 px-3 rounded-lg transition-colors duration-200 ${
                  isActive
                    ? 'text-primary dark:text-dark-primary bg-primary/5 dark:bg-dark-primary/5 font-semibold'
                    : 'text-on-surface-variant dark:text-dark-on-surface-variant hover:text-primary dark:hover:text-dark-primary hover:bg-surface-container dark:hover:bg-dark-surface-container'
                }`}
              >
                <span
                  className={`material-symbols-outlined text-[18px] transition-colors duration-200 ${
                    isActive ? 'fill text-primary dark:text-dark-primary' : ''
                  }`}
                >
                  {item.icon}
                </span>
                {t(item.labelKey)}
                {isActive && (
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1 h-1 bg-primary dark:bg-dark-primary rounded-full" />
                )}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-2">
          <LanguageToggle />
          <ThemeToggle />
          <button
            onClick={handleModeToggle}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full border border-outline-variant dark:border-dark-outline-variant text-on-surface-variant dark:text-dark-on-surface-variant hover:bg-surface-container dark:hover:bg-dark-surface-container transition-colors duration-200 font-ui-caption text-ui-caption"
            title={isDev ? t('mode.switchToUser') : t('mode.switchToDev')}
          >
            <span className="material-symbols-outlined text-[16px]">
              {isDev ? 'person' : 'code'}
            </span>
            {isDev ? t('mode.user') : t('mode.dev')}
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;