const LoadingSpinner = () => {
  return (
    <div className="relative w-16 h-16 flex items-center justify-center animate-spin-slow">
      <svg className="w-full h-full text-secondary-fixed dark:text-dark-secondary" viewBox="0 0 100 100">
        <path
          d="M50 10 L60 40 L90 50 L60 60 L50 90 L40 60 L10 50 L40 40 Z"
          fill="none"
          stroke="currentColor"
          strokeLinejoin="round"
          strokeWidth="4"
        />
      </svg>
    </div>
  );
};

export default LoadingSpinner;
