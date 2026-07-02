import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../api/AuthContext';

const SignupPage = () => {
  const navigate = useNavigate();
  const { signup } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (username.length < 3) {
      setError('Username must be at least 3 characters');
      return;
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      await signup(username, password);
      navigate('/dev/annotation/guidelines');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex-grow w-full max-w-md mx-auto px-4 sm:px-6 lg:px-8 py-10 lg:py-16 flex flex-col gap-8 page-enter">
      <div className="flex flex-col gap-4">
        <h1 className="font-display-lg text-display-lg text-primary dark:text-dark-primary">
          Create Account
        </h1>
        <p className="font-body-main text-body-main text-on-surface-variant dark:text-dark-on-surface-variant">
          Sign up to start annotating hadith relevance. You'll be assigned 2 queries to grade.
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
            placeholder="Choose a username"
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
            autoComplete="new-password"
            className="px-4 py-3 bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg text-on-surface dark:text-dark-on-surface focus:outline-none focus:border-primary dark:focus:border-dark-primary transition-colors"
            placeholder="At least 6 characters"
          />
        </div>

        <div className="flex flex-col gap-2">
          <label className="font-label-lg text-on-surface dark:text-dark-on-surface">
            Confirm Password
          </label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            className="px-4 py-3 bg-surface dark:bg-dark-surface border border-outline dark:border-dark-outline rounded-lg text-on-surface dark:text-dark-on-surface focus:outline-none focus:border-primary dark:focus:border-dark-primary transition-colors"
            placeholder="Re-enter password"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-4 py-3 bg-primary dark:bg-dark-primary text-on-primary dark:text-dark-on-primary rounded-lg font-medium hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Creating account...' : 'Sign Up'}
        </button>
      </form>

      <div className="text-center text-sm text-on-surface-variant dark:text-dark-on-surface-variant">
        Already have an account?{' '}
        <Link to="/dev/annotation/signin" className="text-primary dark:text-dark-primary hover:underline">
          Sign in
        </Link>
      </div>
    </main>
  );
};

export default SignupPage;
