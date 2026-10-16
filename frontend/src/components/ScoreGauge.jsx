import { useEffect, useRef, useState } from 'react';

export default function ScoreGauge({ score = 0, size = 160, label = 'Match Score' }) {
  const [displayed, setDisplayed] = useState(0);
  const rafRef = useRef(null);
  const radius = 52;
  const circumference = 2 * Math.PI * radius;

  // Animate from 0 → score on mount
  useEffect(() => {
    const start = performance.now();
    const duration = 1200;

    const tick = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayed(Math.round(eased * score));
      if (progress < 1) rafRef.current = requestAnimationFrame(tick);
    };

    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [score]);

  const pct = Math.min(Math.max(displayed, 0), 100);
  const offset = circumference - (pct / 100) * circumference;

  const color =
    pct >= 75 ? '#0d9488' :
    pct >= 50 ? '#d97706' :
                '#dc2626';

  const trackColor =
    pct >= 75 ? '#ccfbf1' :
    pct >= 50 ? '#fef3c7' :
                '#fee2e2';

  const bgColor =
    pct >= 75 ? '#f0fdfa' :
    pct >= 50 ? '#fffbeb' :
                '#fef2f2';

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className="relative rounded-full animate-bounce-in"
        style={{ width: size, height: size, background: bgColor }}
      >
        <svg width={size} height={size} viewBox="0 0 120 120" className="-rotate-90">
          {/* Track */}
          <circle
            cx="60" cy="60" r={radius}
            fill="none"
            stroke={trackColor}
            strokeWidth="9"
          />
          {/* Progress */}
          <circle
            cx="60" cy="60" r={radius}
            fill="none"
            stroke={color}
            strokeWidth="9"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 0.05s linear' }}
          />
        </svg>
        {/* Center label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-black leading-none" style={{ color }}>{pct}</span>
          <span className="text-xs font-medium mt-0.5" style={{ color, opacity: 0.6 }}>/100</span>
        </div>
      </div>
      <p className="text-sm font-medium text-ink-500">{label}</p>
    </div>
  );
}
