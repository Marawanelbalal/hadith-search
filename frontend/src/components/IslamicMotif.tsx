interface IslamicMotifProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeMap = {
  sm: 'w-8 h-8',
  md: 'w-16 h-16',
  lg: 'w-24 h-24',
};

const innerSizeMap = {
  sm: 'w-6 h-6',
  md: 'w-12 h-12',
  lg: 'w-18 h-18',
};

const IslamicMotif = ({ size = 'md', className = '' }: IslamicMotifProps) => {
  return (
    <div
      className={`${sizeMap[size]} bg-secondary-container dark:bg-dark-secondary-container rounded-sm rotate-45 flex items-center justify-center ${className}`}
    >
      <div
        className={`${innerSizeMap[size]} border border-on-secondary-container dark:border-dark-on-secondary-container rotate-[-45deg] bg-background dark:bg-dark-background`}
      />
    </div>
  );
};

export default IslamicMotif;
