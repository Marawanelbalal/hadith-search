import { useState, useRef, useEffect } from 'react';

export interface MultiSelectOption {
  value: string;
  label: string;
  count?: number;
}

interface MultiSelectDropdownProps {
  label: string;
  options: MultiSelectOption[];
  selectedValues: string[];
  onSelectionChange: (values: string[]) => void;
  placeholder?: string;
}

export const MultiSelectDropdown = ({
  label,
  options,
  selectedValues,
  onSelectionChange,
  placeholder = 'Select options',
}: MultiSelectDropdownProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const toggleOption = (value: string) => {
    if (selectedValues.includes(value)) {
      onSelectionChange(selectedValues.filter((v) => v !== value));
    } else {
      onSelectionChange([...selectedValues, value]);
    }
  };

  const toggleSelectAll = () => {
    if (selectedValues.length === options.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(options.map((opt) => opt.value));
    }
  };

  const clearAll = () => {
    onSelectionChange([]);
  };

  const getDisplayText = () => {
    if (selectedValues.length === 0) return placeholder;
    if (selectedValues.length === 1) {
      const option = options.find((opt) => opt.value === selectedValues[0]);
      return option?.label || selectedValues[0];
    }
    return `${selectedValues.length} selected`;
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <label className="block font-ui-label text-ui-label mb-2 text-on-surface dark:text-dark-on-surface">
        {label}
      </label>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg text-left flex items-center justify-between hover:border-primary dark:hover:border-dark-primary transition-colors duration-200"
      >
        <span className="text-on-surface dark:text-dark-on-surface">{getDisplayText()}</span>
        <span
          className={`material-symbols-outlined text-on-surface-variant dark:text-dark-on-surface-variant transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
        >
          expand_more
        </span>
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-2 bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg shadow-lg max-h-80 overflow-y-auto">
          <div className="p-3 border-b border-outline-variant dark:border-dark-outline-variant">
            <button
              type="button"
              onClick={toggleSelectAll}
              className="w-full text-left px-3 py-2 rounded hover:bg-surface-container dark:hover:bg-dark-surface-container transition-colors text-sm font-ui-label text-primary dark:text-dark-primary"
            >
              {selectedValues.length === options.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>
          <div className="p-2">
            {options.map((option) => (
              <label
                key={option.value}
                className="flex items-center gap-3 px-3 py-2 rounded hover:bg-surface-container dark:hover:bg-dark-surface-container cursor-pointer transition-colors"
              >
                <input
                  type="checkbox"
                  checked={selectedValues.includes(option.value)}
                  onChange={() => toggleOption(option.value)}
                  className="w-4 h-4 rounded border-outline dark:border-dark-outline text-primary dark:text-dark-primary focus:ring-primary dark:focus:ring-dark-primary"
                />
                <span className="flex-1 text-on-surface dark:text-dark-on-surface">
                  {option.label}
                </span>
                {option.count !== undefined && (
                  <span className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
                    ({option.count})
                  </span>
                )}
              </label>
            ))}
          </div>
          {selectedValues.length > 0 && (
            <div className="p-3 border-t border-outline-variant dark:border-dark-outline-variant">
              <button
                type="button"
                onClick={clearAll}
                className="w-full text-left px-3 py-2 rounded hover:bg-surface-container dark:hover:bg-dark-surface-container transition-colors text-sm font-ui-label text-error"
              >
                Clear All
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
