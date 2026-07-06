import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../api/AuthContext';

const SigninPage = () => {
  const navigate = useNavigate();
  const { signin, token, loading: authLoading } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!authLoading && token) navigate('/dev/annotation');
  }, [authLoading, token, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    setLoading(true);
    try {
      await signin(username, password);
      navigate('/dev/annotation');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signin failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex-grow w-full max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-10 lg:py-16 flex flex-col gap-8 page-enter">
      <div className="flex flex-col gap-4">
        <h1 className="font-display-lg text-display-lg text-primary dark:text-dark-primary">
          Sign In
        </h1>
        <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant">
          Access your assigned annotation queries.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && (
          <div className="bg-error-container text-on-error-container p-4 rounded-lg text-sm">
            {error}
          </div>
        )}

        <div className="flex flex-col gap-2">
          <label className="font-label-lg text-on-surface dark:text-dark-on-surface">
            Username
          </label>
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            className="px-4 py-3 bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg text-on-surface dark:text-dark-on-surface focus:outline-none focus:border-primary dark:focus:border-dark-primary transition-colors"
            placeholder="Your username"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="font-label-lg text-on-surface dark:text-dark-on-surface">
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            className="px-4 py-3 bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg text-on-surface dark:text-dark-on-surface focus:outline-none focus:border-primary dark:focus:border-dark-primary transition-colors"
            placeholder="Your password"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-4 py-3 bg-primary dark:bg-dark-primary text-on-primary dark:text-dark-on-primary rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Signing in...' : 'Sign In'}
        </button>
      </form>

      <div className="text-center text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
        Don't have an account?{' '}
        <Link to="/dev/annotation/signup" className="text-primary dark:text-dark-primary hover:underline">
          Sign up
        </Link>
      </div>
    </main>
  );
};

export default SigninPage;
