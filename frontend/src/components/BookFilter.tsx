import { books } from '../data/fakeData';

interface BookFilterProps {
  selectedBook: string | null;
  onBookChange: (bookId: string | null) => void;
}

const BookFilter = ({ selectedBook, onBookChange }: BookFilterProps) => {
  return (
    <div className="w-full">
      <span className="font-ui-caption text-ui-caption text-on-surface-variant uppercase tracking-wider block mb-3 text-center">
        Book:
      </span>
      <div className="flex gap-3 overflow-x-auto scrollbar-hide pb-2 px-1">
        {books.map((book) => {
          const isSelected = selectedBook === book.id;

          return (
            <button
              key={book.id}
              onClick={() => onBookChange(isSelected ? null : book.id)}
              className={`flex-shrink-0 min-w-[160px] px-4 py-3 rounded-xl font-ui-label text-ui-label transition-all duration-300 border-2 text-left group ${
                isSelected
                  ? 'bg-primary-container border-primary ring-2 ring-primary/20 shadow-lg shadow-primary/10'
                  : 'bg-surface-container border-outline-variant hover:border-primary-container hover:shadow-md'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`material-symbols-outlined text-[16px] transition-colors duration-300 ${
                    isSelected ? 'text-primary fill' : 'text-on-surface-variant'
                  }`}
                >
                  menu_book
                </span>
                <span
                  className={`font-semibold truncate transition-colors duration-300 ${
                    isSelected ? 'text-on-primary-container' : 'text-on-surface'
                  }`}
                >
                  {book.name}
                </span>
              </div>
              <p
                className={`font-body-arabic text-[16px] text-right transition-colors duration-300 ${
                  isSelected ? 'text-on-primary-container' : 'text-on-surface-variant'
                }`}
                dir="rtl"
              >
                {book.arabicName}
              </p>
              <p
                className={`font-ui-caption text-ui-caption mt-1 transition-colors duration-300 ${
                  isSelected ? 'text-on-primary-container/70' : 'text-on-surface-variant/70'
                }`}
              >
                {book.hadithCount.toLocaleString()} hadiths
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default BookFilter;
