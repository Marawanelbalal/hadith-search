import { useLanguage } from '../i18n/useLanguage';

const Footer = () => {
  const { t } = useLanguage();

  return (
    <footer className="bg-surface-container-lowest dark:bg-dark-surface-container-lowest text-on-surface dark:text-dark-on-surface w-full border-t border-outline-variant dark:border-dark-outline-variant py-8 px-6 flex flex-col md:flex-row justify-between items-center gap-4 mt-auto font-ui-caption text-ui-caption uppercase tracking-widest">
      <p className="text-on-surface-variant dark:text-dark-on-surface-variant">{t('footer.copyright')}</p>
      <nav className="flex gap-6">
        <a className="text-on-surface-variant dark:text-dark-on-surface-variant hover:text-primary dark:hover:text-dark-primary transition-colors duration-300" href="#">{t('footer.about')}</a>
        <a className="text-on-surface-variant dark:text-dark-on-surface-variant hover:text-primary dark:hover:text-dark-primary transition-colors duration-300" href="#">{t('footer.methodology')}</a>
        <a className="text-on-surface-variant dark:text-dark-on-surface-variant hover:text-primary dark:hover:text-dark-primary transition-colors duration-300" href="#">{t('footer.privacy')}</a>
        <a className="text-on-surface-variant dark:text-dark-on-surface-variant hover:text-primary dark:hover:text-dark-primary transition-colors duration-300" href="#">{t('footer.api')}</a>
      </nav>
    </footer>
  );
};

export default Footer;
