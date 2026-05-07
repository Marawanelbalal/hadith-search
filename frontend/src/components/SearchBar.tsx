import { useState } from 'react';

interface SearchBarProps {
  onSearch: (query: string) => void;
  placeholder?: string;
  compact?: boolean;
}

const SearchBar = ({ onSearch, placeholder = "Search narrators, topics, or exact phrases...", compact = false }: SearchBarProps) => {
  const [query, setQuery] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleClick = () => {
    if (query.trim()) {
      onSearch(query.trim());
    }
  };

  return (
    <div className="relative w-full group">
      <div className="absolute inset-y-0 left-6 flex items-center pointer-events-none">
        <span className="material-symbols-outlined text-secondary fill group-focus-within:text-primary transition-colors duration-300">
          search
        </span>
      </div>
      <input
        className={`w-full ${compact ? 'h-12 pl-14 pr-4' : 'h-16 pl-16 pr-6'} rounded-full border-2 border-outline-variant dark:border-dark-outline-variant bg-surface-container-lowest dark:bg-dark-surface-container-lowest text-on-surface dark:text-dark-on-surface font-ui-label text-ui-label focus:border-secondary dark:focus:border-dark-secondary focus:ring-4 focus:ring-secondary-container/30 dark:focus:ring-dark-secondary-container/30 transition-all shadow-sm placeholder:text-outline dark:placeholder:text-dark-outline placeholder:font-normal`}
        placeholder={placeholder}
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <button
        onClick={handleClick}
        className={`absolute ${compact ? 'inset-y-1.5 right-1.5 px-4' : 'inset-y-2 right-2 px-6'} bg-primary dark:bg-dark-primary text-on-primary dark:text-dark-on-primary rounded-full font-ui-label text-ui-label hover:bg-primary-container dark:hover:bg-dark-primary-container transition-all duration-200 flex items-center gap-2 hover:shadow-md active:scale-95`}
      >
        <span className="material-symbols-outlined text-[18px]">search</span>
        Search
      </button>
    </div>
  );
};

export default SearchBar;
