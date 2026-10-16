export default function LoadingSpinner({ size = 'md', text = '' }) {
  const dim = size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-8 h-8' : 'w-6 h-6';
  return (
    <span className="inline-flex items-center gap-2">
      <svg
        className={`${dim} animate-spin text-teal-600 flex-shrink-0`}
        xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
      >
        <circle className="opacity-20" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
        <path className="opacity-75" fill="currentColor"
          d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
      </svg>
      {text && <span className="text-ink-500 text-sm">{text}</span>}
    </span>
  );
}
