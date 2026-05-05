import { useLocation } from 'react-router-dom';

const Footer = () => {
  const location = useLocation();
  const isDark = location.pathname === '/loading';

  if (isDark) return null;

  return (
    <footer className="bg-surface-container-lowest text-on-surface w-full border-t border-surface-container-high py-8 px-6 flex flex-col md:flex-row justify-between items-center gap-4 mt-auto font-ui-caption text-ui-caption uppercase tracking-widest">
      <p className="text-on-surface-variant">© 2024 Hadith Search. Sacred Minimalism in Digital Scholarship.</p>
      <nav className="flex gap-6">
        <a className="text-on-surface-variant hover:text-primary transition-colors duration-300" href="#">About</a>
        <a className="text-on-surface-variant hover:text-primary transition-colors duration-300" href="#">Methodology</a>
        <a className="text-on-surface-variant hover:text-primary transition-colors duration-300" href="#">Privacy</a>
        <a className="text-on-surface-variant hover:text-primary transition-colors duration-300" href="#">API</a>
      </nav>
    </footer>
  );
};

export default Footer;
