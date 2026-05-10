import { useLanguage } from '../i18n/useLanguage';

interface ErrorBannerProps {
  message: string | null;
  onDismiss?: () => void;
}

const ErrorBanner = ({ message, onDismiss }: ErrorBannerProps) => {
  const { t } = useLanguage();

  if (!message) return null;

  return (
    <div className="flex items-center justify-between bg-error-container dark:bg-dark-error-container text-on-error-container dark:text-dark-on-error-container rounded-lg p-4 animate-fade-in">
      <div className="flex items-center gap-3">
        <span className="material-symbols-outlined text-[20px]">error</span>
        <span className="font-ui-label text-ui-label">{message}</span>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="material-symbols-outlined text-[20px] hover:opacity-70 transition-opacity"
        >
          close
        </button>
      )}
    </div>
  );
};

export default ErrorBanner;
