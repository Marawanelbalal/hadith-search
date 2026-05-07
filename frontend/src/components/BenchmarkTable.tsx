import { benchmarkData } from '../data/fakeData';

type NumericKey = 'map' | 'precisionAt10' | 'recallAt100' | 'ndcg';

const metrics: { key: NumericKey; label: string }[] = [
  { key: 'map', label: 'MAP' },
  { key: 'precisionAt10', label: 'P@10' },
  { key: 'recallAt100', label: 'R@100' },
  { key: 'ndcg', label: 'NDCG' },
];

const BenchmarkTable = () => {
  // Find the best value for each metric
  const bestValues: Record<string, number> = {};
  metrics.forEach(({ key }) => {
    bestValues[key] = Math.max(...benchmarkData.map((entry) => entry[key]));
  });

  return (
    <div className="overflow-x-auto rounded-lg border border-outline-variant dark:border-dark-outline-variant bg-surface-container-lowest dark:bg-dark-surface-container-lowest">
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-surface-container-low dark:bg-dark-surface-container-low font-ui-label text-ui-label text-on-surface dark:text-dark-on-surface border-b border-outline-variant dark:border-dark-outline-variant">
            <th className="p-4 py-3 font-semibold">Algorithm</th>
            {metrics.map(({ key, label }) => (
              <th key={key} className="p-4 py-3 font-semibold text-right">
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="font-body-main text-body-main text-on-surface dark:text-dark-on-surface divide-y divide-outline-variant dark:divide-dark-outline-variant">
          {benchmarkData.map((entry) => (
            <tr
              key={entry.algorithmName}
              className="hover:bg-surface-container dark:hover:bg-dark-surface-container transition-colors duration-200"
            >
              <td
                className={`p-4 font-semibold ${
                  entry.algorithmName === 'Cross-Encoder'
                    ? 'text-primary dark:text-dark-primary'
                    : 'text-on-surface-variant dark:text-dark-on-surface-variant'
                }`}
              >
                {entry.algorithmName}
              </td>
              {metrics.map(({ key }) => {
                const value = entry[key];
                const isBest = value === bestValues[key];
                return (
                  <td
                    key={key}
                    className={`p-4 text-right ${
                      isBest
                        ? 'bg-primary-fixed text-on-primary-fixed font-medium'
                        : 'text-on-surface-variant dark:text-dark-on-surface-variant'
                    }`}
                  >
                    {value.toFixed(3)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default BenchmarkTable;
