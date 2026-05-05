import BenchmarkTable from '../components/BenchmarkTable';

const BenchmarksPage = () => {
  return (
    <main className="flex-grow w-full max-w-container-max-width mx-auto px-margin-mobile md:px-margin-desktop py-12 flex flex-col gap-16 page-enter">
      <div className="flex flex-col gap-4 max-w-3xl">
        <h1 className="font-display-lg text-display-lg text-primary">
          Algorithm Benchmarks
        </h1>
        <p className="font-body-main text-body-main text-on-surface-variant">
          Comprehensive evaluation of retrieval algorithms against verified gold standard
          datasets (qrels). Metrics include Mean Average Precision (MAP), Precision at 10
          (P@10), Recall at 100 (R@100), and Normalized Discounted Cumulative Gain (NDCG).
        </p>
      </div>

      <section className="flex flex-col gap-6">
        <div className="flex items-center gap-4 border-b border-outline-variant pb-2">
          <span className="material-symbols-outlined text-primary fill">analytics</span>
          <h2 className="font-h1-hadith text-h1-hadith text-on-surface">
            Algorithm Performance
          </h2>
        </div>
        <BenchmarkTable />
      </section>

      <section className="flex flex-col gap-6">
        <div className="flex items-center gap-4 border-b border-outline-variant pb-2">
          <span className="material-symbols-outlined text-secondary fill">info</span>
          <h2 className="font-h1-hadith text-h1-hadith text-on-surface">
            Methodology
          </h2>
        </div>
        <div className="bg-surface-container-lowest border border-outline-variant rounded-lg p-6 md:p-8">
          <p className="font-body-main text-body-main text-on-surface-variant leading-relaxed">
            All algorithms are evaluated on a curated set of 50 queries with expert-annotated
            relevance judgments. The qrels follow a graded relevance scale (0: not relevant,
            1: partially relevant, 2: highly relevant). Statistical significance is tested
            using a two-tailed paired t-test at p{'<'}0.05.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
            <div className="flex flex-col gap-2 p-4 bg-surface-container rounded-lg">
              <span className="font-ui-label text-ui-label text-primary">50</span>
              <span className="font-ui-caption text-ui-caption text-on-surface-variant">
                Test Queries
              </span>
            </div>
            <div className="flex flex-col gap-2 p-4 bg-surface-container rounded-lg">
              <span className="font-ui-label text-ui-label text-primary">33,000+</span>
              <span className="font-ui-caption text-ui-caption text-on-surface-variant">
                Hadith Corpus
              </span>
            </div>
            <div className="flex flex-col gap-2 p-4 bg-surface-container rounded-lg">
              <span className="font-ui-label text-ui-label text-primary">5</span>
              <span className="font-ui-caption text-ui-caption text-on-surface-variant">
                Algorithms Compared
              </span>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
};

export default BenchmarksPage;
