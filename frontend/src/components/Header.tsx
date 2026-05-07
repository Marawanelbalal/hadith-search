import { Link, useLocation } from 'react-router-dom';
import { navItems } from '../data/fakeData';
import { ThemeToggle } from './ThemeToggle';

const Header = () => {
  const location = useLocation();
  const isDark = location.pathname === '/loading';

  if (isDark) return null;

  return (
    <header className="bg-surface dark:bg-dark-surface font-newsreader text-on-surface dark:text-dark-on-surface sticky top-0 border-b border-outline dark:border-dark-outline transition-all duration-200 ease-in-out z-50">
      <div className="flex justify-between items-center w-full px-6 py-4 max-w-[1200px] mx-auto">
        <Link
          to="/"
          className="text-2xl font-bold tracking-tight text-primary dark:text-dark-primary flex items-center gap-2 group"
        >
          <span className="material-symbols-outlined fill text-primary group-hover:rotate-90 transition-transform duration-500">
            star
          </span>
          <span className="font-display-lg text-[24px]">Hadith Search</span>
        </Link>
        <nav className="hidden md:flex gap-1 items-center font-ui-label text-ui-label">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`relative flex items-center gap-1.5 py-2 px-3 rounded-lg transition-all duration-300 ${
                  isActive
                    ? 'text-primary dark:text-dark-primary bg-primary/5 dark:bg-dark-primary/5 font-semibold'
                    : 'text-on-surface-variant dark:text-dark-on-surface-variant hover:text-primary dark:hover:text-dark-primary hover:bg-surface-container dark:hover:bg-dark-surface-container'
                }`}
              >
                <span
                  className={`material-symbols-outlined text-[18px] transition-all duration-300 ${
                    isActive ? 'fill text-primary dark:text-dark-primary' : ''
                  }`}
                >
                  {item.icon}
                </span>
                {item.label}
                {isActive && (
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-1 h-1 bg-primary rounded-full animate-slide-in-left" />
                )}
              </Link>
            );
          })}
        </nav>
        <div className="flex items-center gap-4">
          <ThemeToggle />
          <Link
            to="/loading"
            className="text-on-surface-variant dark:text-dark-on-surface-variant hover:text-primary dark:hover:text-dark-primary p-2 rounded-full transition-colors flex items-center justify-center hover:bg-surface-container dark:hover:bg-dark-surface-container"
          >
            <span className="material-symbols-outlined">refresh</span>
          </Link>
        </div>
      </div>
    </header>
  );
};

export default Header;
