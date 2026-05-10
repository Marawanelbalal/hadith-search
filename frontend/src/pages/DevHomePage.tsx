import { useNavigate } from 'react-router-dom';
import { useLanguage } from '../i18n/useLanguage';
import SearchBar from '../components/SearchBar';
import type { Lang } from '../types';
import { getAppMode } from '../components/Navbar';

const DevHomePage = () => {
  const navigate = useNavigate();
  const { t } = useLanguage();

  const handleSearch = (query: string, lang: Lang) => {
    const mode = getAppMode();
    const params = new URLSearchParams();
    params.set('q', query);
    params.set('lang', lang);
    if (mode === 'dev') {
      navigate(`/dev/search?${params.toString()}`);
    } else {
      navigate(`/user/search?${params.toString()}`);
    }
  };

  return (
    <main className="flex-grow flex flex-col items-center justify-center px-margin-mobile md:px-margin-desktop py-16 w-full max-w-container-max-width mx-auto relative">
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-surface-container-low dark:from-dark-surface-container-low via-background dark:via-dark-background to-background dark:to-dark-background opacity-50 -z-10" />

      <div className="text-center max-w-3xl flex flex-col items-center gap-6 mb-10 animate-fade-in-up">
        <h1 className="font-display-lg text-display-lg text-primary dark:text-dark-primary tracking-tight">
          {t('dev.homeTitle')}
        </h1>
        <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant max-w-2xl mx-auto">
          {t('dev.homeSubtitle')}
        </p>
      </div>

      <div className="w-full max-w-4xl animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
        <SearchBar onSearch={handleSearch} />
      </div>
    </main>
  );
};

export default DevHomePage;