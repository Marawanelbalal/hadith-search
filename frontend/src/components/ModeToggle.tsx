interface ModeToggleProps {
  isDevMode: boolean;
  onToggle: () => void;
}

export const ModeToggle = ({ isDevMode, onToggle }: ModeToggleProps) => {
  return (
    <div className="flex items-center gap-3">
      <span className={`font-ui-label text-ui-label transition-colors ${
        !isDevMode ? 'text-primary dark:text-dark-primary font-semibold' : 'text-on-surface-variant dark:text-dark-on-surface-variant'
      }`}>
        User
      </span>
      <button
        type="button"
        onClick={onToggle}
        className={`relative w-14 h-7 rounded-full transition-colors duration-200 ${
          isDevMode ? 'bg-primary dark:bg-dark-primary' : 'bg-outline dark:bg-dark-outline'
        }`}
        aria-label="Toggle mode"
      >
        <span
          className={`absolute top-1 w-5 h-5 bg-white rounded-full shadow-md transition-transform duration-200 ${
            isDevMode ? 'translate-x-7' : 'translate-x-1'
          }`}
        />
      </button>
      <span className={`font-ui-label text-ui-label transition-colors ${
        isDevMode ? 'text-primary dark:text-dark-primary font-semibold' : 'text-on-surface-variant dark:text-dark-on-surface-variant'
      }`}>
        Dev
      </span>
    </div>
  );
};
