import { useNavigate } from 'react-router-dom';
import { useAuth } from '../api/AuthContext';

const AnnotationGuidelinesPage = () => {
  const navigate = useNavigate();
  const { assignments } = useAuth();

  return (
    <main className="flex-grow w-full max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 lg:py-12 flex flex-col gap-8 page-enter">
      <div className="flex flex-col gap-4">
        <h1 className="font-display-lg text-display-lg text-primary dark:text-dark-primary">
          Annotation Guidelines
        </h1>
        <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant">
          Please read these guidelines carefully before starting annotation.
        </p>
      </div>

      <div className="bg-surface dark:bg-dark-surface p-6 rounded-lg border border-outline dark:border-dark-outline flex flex-col gap-6">
        <section className="flex flex-col gap-3">
          <h2 className="font-title-md text-on-surface dark:text-dark-on-surface">Task</h2>
          <p className="text-on-surface-variant dark:text-dark-on-surface-variant leading-relaxed">
            You will be shown a search query and a pool of hadiths retrieved by various retrieval methods.
            Your task is to judge the <strong>relevance</strong> of each hadith to the query on a 3-point scale.
          </p>
        </section>

        <section className="flex flex-col gap-3">
          <h2 className="font-title-md text-on-surface dark:text-dark-on-surface">Grading Scale</h2>
          <div className="flex flex-col gap-3">
            <div className="flex items-start gap-3 p-3 bg-surface-variant dark:bg-dark-surface-variant rounded-lg">
              <span className="text-2xl font-bold text-green-600 dark:text-green-400 min-w-8">2</span>
              <div>
                <div className="font-medium text-on-surface dark:text-dark-on-surface">Highly Relevant</div>
                <div className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
                  The hadith directly answers or closely addresses the query topic.
                </div>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-surface-variant dark:bg-dark-surface-variant rounded-lg">
              <span className="text-2xl font-bold text-yellow-600 dark:text-yellow-400 min-w-8">1</span>
              <div>
                <div className="font-medium text-on-surface dark:text-dark-on-surface">Relevant</div>
                <div className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
                  The hadith is related to the query topic but does not directly answer it. May be tangentially relevant or address only part of the query.
                </div>
              </div>
            </div>
            <div className="flex items-start gap-3 p-3 bg-surface-variant dark:bg-dark-surface-variant rounded-lg">
              <span className="text-2xl font-bold text-red-600 dark:text-red-400 min-w-8">0</span>
              <div>
                <div className="font-medium text-on-surface dark:text-dark-on-surface">Not Relevant</div>
                <div className="text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
                  The hadith is unrelated to the query topic.
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="flex flex-col gap-3">
          <h2 className="font-title-md text-on-surface dark:text-dark-on-surface">Guidelines</h2>
          <ul className="flex flex-col gap-2 text-on-surface-variant dark:text-dark-on-surface-variant list-disc list-inside">
            <li>Judge relevance based on the <strong>meaning</strong> of the hadith, not keyword overlap.</li>
            <li>Consider both the Arabic and English text. If they differ, use the Arabic as the primary source.</li>
            <li>Grade based on topical relevance, not the authenticity (grade) of the hadith.</li>
            <li>Be consistent: if a hadith addresses the same sub-topic as another you graded, give it the same grade.</li>
            <li>When in doubt, use your best judgment. There are no wrong answers if you follow the scale.</li>
          </ul>
        </section>

        <section className="flex flex-col gap-3">
          <h2 className="font-title-md text-on-surface dark:text-dark-on-surface">Keyboard Shortcuts</h2>
          <div className="flex flex-wrap gap-4 text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
            <span><kbd className="px-1.5 py-0.5 bg-surface-variant dark:bg-dark-surface-variant rounded">0</kbd> Not Relevant</span>
            <span><kbd className="px-1.5 py-0.5 bg-surface-variant dark:bg-dark-surface-variant rounded">1</kbd> Relevant</span>
            <span><kbd className="px-1.5 py-0.5 bg-surface-variant dark:bg-dark-surface-variant rounded">2</kbd> Highly Relevant</span>
            <span><kbd className="px-1.5 py-0.5 bg-surface-variant dark:bg-dark-surface-variant rounded">&larr;</kbd> Previous</span>
            <span><kbd className="px-1.5 py-0.5 bg-surface-variant dark:bg-dark-surface-variant rounded">&rarr;</kbd> Next</span>
          </div>
        </section>

        {assignments.length > 0 && (
          <section className="flex flex-col gap-3">
            <h2 className="font-title-md text-on-surface dark:text-dark-on-surface">Your Assignments</h2>
            <div className="flex flex-col gap-2">
              {assignments.map((a) => (
                <div key={a.query_id} className="flex items-center gap-2 p-3 bg-surface-variant dark:bg-dark-surface-variant rounded-lg">
                  <span className={`px-2 py-0.5 text-xs font-medium rounded ${a.query_id.startsWith('EN') ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'}`}>
                    {a.query_id.startsWith('EN') ? 'EN' : 'AR'}
                  </span>
                  <span className="text-on-surface dark:text-dark-on-surface truncate">{a.query}</span>
                </div>
              ))}
            </div>
          </section>
        )}
      </div>

      <div className="flex justify-center">
        <button
          onClick={() => navigate('/dev/annotation')}
          className="px-6 py-3 bg-primary dark:bg-dark-primary text-on-primary dark:text-dark-on-primary rounded-lg font-medium hover:opacity-90 transition-opacity"
        >
          Start Annotating
        </button>
      </div>
    </main>
  );
};

export default AnnotationGuidelinesPage;
