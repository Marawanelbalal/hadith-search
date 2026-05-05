import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import LoadingSpinner from '../components/LoadingSpinner';

const LoadingPage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate('/');
    }, 2000);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="h-screen w-full bg-primary-container m-0 p-0 overflow-hidden flex items-center justify-center fixed inset-0 z-50">
      <div className="flex flex-col items-center justify-center z-10 p-8 space-y-8">
        <LoadingSpinner />
        <div className="flex flex-col items-center space-y-2">
          <h1 className="font-display-lg text-display-lg text-on-primary tracking-tight text-center">
            Hadith Search
          </h1>
          <p className="font-ui-caption text-ui-caption text-on-primary/60 uppercase tracking-widest">
            Loading sacred knowledge...
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoadingPage;
