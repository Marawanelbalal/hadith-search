import { MultiSelectDropdown } from './MultiSelectDropdown';
import type { MultiSelectOption } from './MultiSelectDropdown';
import { books } from '../data/fakeData';

interface BookMultiSelectProps {
  selectedBooks: string[];
  onSelectionChange: (books: string[]) => void;
}

const bookOptions: MultiSelectOption[] = books.map((book) => ({
  value: book.id,
  label: book.name,
  count: book.hadithCount,
}));

export const BookMultiSelect = ({ selectedBooks, onSelectionChange }: BookMultiSelectProps) => {
  return (
    <MultiSelectDropdown
      label="Filter by Book"
      options={bookOptions}
      selectedValues={selectedBooks}
      onSelectionChange={onSelectionChange}
      placeholder="Select books"
    />
  );
};
