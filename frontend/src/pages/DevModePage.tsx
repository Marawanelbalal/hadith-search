import AlgorithmCard from '../components/AlgorithmCard';
import { algorithmResults } from '../data/fakeData';

const DevModePage = () => {
  return (
    <div className="flex flex-1 pt-0 h-full w-full max-w-full">
      <main className="flex-1 bg-background dark:bg-dark-background p-gutter min-h-screen girih-bg w-full page-enter">
        {/* Query info bar */}
        <div className="bg-surface-container-low dark:bg-dark-surface-container-low rounded-xl p-4 mb-gutter border border-outline-variant dark:border-dark-outline-variant flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-6">
            <div className="flex flex-col">
              <label className="font-ui-caption text-ui-caption text-on-surface-variant dark:text-dark-on-surface-variant mb-1">
                Base Query
              </label>
              <div className="font-ui-label text-ui-label text-on-surface dark:text-dark-on-surface">
                &ldquo;purification before prayer&rdquo;
              </div>
            </div>
          </div>
          <div className="text-on-surface-variant dark:text-dark-on-surface-variant font-ui-caption text-ui-caption flex items-center gap-2">
            <span className="material-symbols-outlined text-sm">info</span>
            Comparing top 100 results
          </div>
        </div>

        {/* Side-by-side algorithm comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-0 border border-outline-variant dark:border-dark-outline-variant rounded-xl overflow-hidden bg-surface dark:bg-dark-surface">
          {algorithmResults.map((algo, index) => (
            <div
              key={algo.id}
              className={`flex flex-col relative ${
                index === 0 ? 'border-r border-outline-variant dark:border-dark-outline-variant' : ''
              }`}
            >
              <AlgorithmCard
                algorithm={algo}
                variant={index === 0 ? 'highlighted' : 'default'}
              />
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default DevModePage;
