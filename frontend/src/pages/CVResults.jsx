import { useLocation, Link } from 'react-router-dom';
import ScoreGauge from '../components/ScoreGauge';
import CVComparison from '../components/CVComparison';
import { ArrowLeft, Lightbulb, Tag, CheckCircle, TrendingUp, Download } from 'lucide-react';

/* ── Insight card ──────────────────────────────────────────── */
function InsightCard({ icon: Icon, title, iconBg, iconColor, children, delay }) {
  return (
    <div
      className="card space-y-3 animate-slide-up"
      style={{ animationDelay: delay }}
    >
      <div className="flex items-center gap-2.5">
        <div className={`w-8 h-8 rounded-lg ${iconBg} flex items-center justify-center`}>
          <Icon className={`w-4 h-4 ${iconColor}`} />
        </div>
        <h3 className="text-sm font-semibold text-ink-800">{title}</h3>
      </div>
      {children}
    </div>
  );
}

/* ── Download helper ──────────────────────────────────────── */
function downloadText(text, filename) {
  const blob = new Blob([text], { type: 'text/plain' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href     = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function CVResults() {
  const { state } = useLocation();

  if (!state?.result) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-4">
        <div className="w-16 h-16 rounded-2xl bg-ink-100 flex items-center justify-center">
          <TrendingUp className="w-8 h-8 text-ink-400" />
        </div>
        <p className="text-ink-500 font-medium">No results to display.</p>
        <Link to="/cv" className="btn-primary">← Optimize a CV</Link>
      </div>
    );
  }

  const { filename, original_text, result, job_title } = state;
  const {
    optimized_text,
    match_score,
    suggestions     = [],
    key_improvements = [],
    missing_keywords = [],
  } = result;

  const hasInsights = suggestions.length > 0 || key_improvements.length > 0 || missing_keywords.length > 0;

  return (
    <div className="space-y-8 animate-fade-in">

      {/* ── Header ─────────────────────────────────────────── */}
      <div className="flex items-start gap-4">
        <Link to="/cv" className="btn-ghost p-2 mt-1 rounded-lg">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-ink-900 truncate">{filename}</h1>
          <p className="text-ink-500 text-sm mt-0.5">
            Optimized for: <span className="text-teal-700 font-semibold">{job_title}</span>
          </p>
        </div>

        {/* Score gauge + download */}
        <div className="flex flex-col items-center gap-3 flex-shrink-0">
          <ScoreGauge score={match_score} size={130} label="Match Score" />
          <button
            onClick={() => downloadText(optimized_text, `optimized-cv-${job_title.replace(/\s+/g, '-')}.txt`)}
            className="btn-secondary text-xs py-1.5 px-3"
          >
            <Download className="w-3.5 h-3.5" /> Download
          </button>
        </div>
      </div>

      {/* ── Insights grid ──────────────────────────────────── */}
      {hasInsights && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {suggestions.length > 0 && (
            <InsightCard
              icon={Lightbulb}
              title="Suggestions"
              iconBg="bg-amber-100"
              iconColor="text-amber-600"
              delay="0.05s"
            >
              <ul className="space-y-2">
                {suggestions.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-ink-600">
                    <span className="text-amber-500 font-bold mt-0.5 flex-shrink-0">→</span>
                    {s}
                  </li>
                ))}
              </ul>
            </InsightCard>
          )}

          {key_improvements.length > 0 && (
            <InsightCard
              icon={CheckCircle}
              title="Improvements Made"
              iconBg="bg-teal-100"
              iconColor="text-teal-600"
              delay="0.1s"
            >
              <ul className="space-y-2">
                {key_improvements.map((s, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-ink-600">
                    <span className="text-teal-600 font-bold mt-0.5 flex-shrink-0">✓</span>
                    {s}
                  </li>
                ))}
              </ul>
            </InsightCard>
          )}

          {missing_keywords.length > 0 && (
            <InsightCard
              icon={Tag}
              title="Missing Keywords"
              iconBg="bg-red-100"
              iconColor="text-red-500"
              delay="0.15s"
            >
              <div className="flex flex-wrap gap-1.5">
                {missing_keywords.map((kw, i) => (
                  <span key={i} className="badge-red">{kw}</span>
                ))}
              </div>
            </InsightCard>
          )}
        </div>
      )}

      {/* ── Side-by-side diff ──────────────────────────────── */}
      <div className="animate-slide-up" style={{ animationDelay: '0.2s' }}>
        <div className="flex items-center gap-2 mb-4">
          <h2 className="section-title">CV Comparison</h2>
          <span className="text-xs text-ink-400 ml-2">Original vs AI-Optimized</span>
        </div>
        <CVComparison original={original_text} optimized={optimized_text} />
      </div>
    </div>
  );
}
