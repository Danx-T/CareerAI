import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { interviewAPI } from '../services/api';
import ScoreGauge from '../components/ScoreGauge';
import LoadingSpinner from '../components/LoadingSpinner';
import { ArrowLeft, Trophy, BarChart3, MessageSquare, CheckCircle, TrendingUp, Lightbulb } from 'lucide-react';
import toast from 'react-hot-toast';

function CategoryBar({ name, score, delay }) {
  const color = score >= 75 ? 'bg-teal-500' : score >= 50 ? 'bg-amber-400' : 'bg-red-400';
  const textColor = score >= 75 ? 'text-teal-700' : score >= 50 ? 'text-amber-700' : 'text-red-600';
  return (
    <div className="animate-slide-up" style={{ animationDelay: delay }}>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-sm text-ink-700 capitalize font-medium">{name}</span>
        <span className={`text-sm font-bold ${textColor}`}>{Math.round(score)}/100</span>
      </div>
      <div className="h-2 bg-ink-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-700`}
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

function QuestionFeedbackRow({ q, index }) {
  const [open, setOpen] = useState(false);
  const scoreColor = q.score >= 75 ? 'text-teal-600' : q.score >= 50 ? 'text-amber-600' : 'text-red-500';
  const scoreBg    = q.score >= 75 ? 'bg-teal-50 border-teal-200' : q.score >= 50 ? 'bg-amber-50 border-amber-200' : 'bg-red-50 border-red-200';

  const hasStrengths = Array.isArray(q.strengths) && q.strengths.length > 0;
  const hasImprovements = Array.isArray(q.improvements) && q.improvements.length > 0;

  return (
    <div className={`border rounded-xl overflow-hidden transition-all duration-300 ${open ? 'border-teal-200 shadow-teal' : 'border-ink-100'} bg-white animate-slide-up`}
      style={{ animationDelay: `${index * 0.04}s` }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-ink-50/50 transition-colors"
      >
        <span className="w-7 h-7 rounded-lg bg-ink-100 flex items-center justify-center text-xs font-bold text-ink-600 flex-shrink-0 mt-0.5">
          {index + 1}
        </span>
        <div className="flex-1 min-w-0">
          <p className="text-ink-900 text-sm font-medium leading-relaxed line-clamp-2">{q.question_text}</p>
          <div className="flex items-center gap-2 mt-1.5">
            <span className="badge badge-ink text-xs capitalize">{q.category}</span>
            {!q.user_answer && <span className="badge badge-yellow text-xs">Not answered</span>}
            {q.score == null && q.user_answer && (
              <span className="badge badge-ink text-xs">Not scored</span>
            )}
          </div>
        </div>
        {q.score != null && (
          <div className={`flex-shrink-0 px-3 py-1.5 rounded-lg border text-sm font-bold ${scoreBg} ${scoreColor}`}>
            {Math.round(q.score)}
          </div>
        )}
      </button>

      {open && (
        <div className="border-t border-ink-100 p-4 space-y-3 animate-slide-up-sm">
          {q.user_answer && (
            <div>
              <p className="text-xs font-semibold text-ink-400 uppercase tracking-wider mb-1.5">Your Answer</p>
              <p className="text-ink-700 text-sm leading-relaxed bg-ink-50 rounded-lg p-3">{q.user_answer}</p>
            </div>
          )}
          {q.ai_feedback && (
            <div>
              <p className="text-xs font-semibold text-ink-400 uppercase tracking-wider mb-1.5">AI Feedback</p>
              <p className="text-ink-700 text-sm leading-relaxed">{q.ai_feedback}</p>
            </div>
          )}

          {/* Question-level Strengths and Improvements */}
          {(hasStrengths || hasImprovements) && (
            <div className={`grid gap-3 ${hasStrengths && hasImprovements ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1'}`}>
              {hasStrengths && (
                <div className="bg-teal-50/60 border border-teal-100 rounded-lg p-3">
                  <p className="text-xs font-semibold text-teal-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <CheckCircle className="w-3.5 h-3.5 text-teal-600 flex-shrink-0" /> Strengths
                  </p>
                  <ul className="space-y-1.5">
                    {q.strengths.map((s, i) => (
                      <li key={i} className="text-ink-700 text-xs leading-relaxed flex items-start gap-2">
                        <span className="text-teal-600 font-bold flex-shrink-0">✓</span>
                        <span>{s}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {hasImprovements && (
                <div className="bg-amber-50/60 border border-amber-100 rounded-lg p-3">
                  <p className="text-xs font-semibold text-amber-800 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <TrendingUp className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" /> Areas for Improvement
                  </p>
                  <ul className="space-y-1.5">
                    {q.improvements.map((imp, i) => (
                      <li key={i} className="text-ink-700 text-xs leading-relaxed flex items-start gap-2">
                        <span className="text-amber-600 font-bold flex-shrink-0">→</span>
                        <span>{imp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Question-level Model Answer Guidance */}
          {q.model_answer_hint && (
            <div className="bg-ink-50/80 border border-ink-100 rounded-lg p-3">
              <p className="text-xs font-semibold text-ink-600 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
                <Lightbulb className="w-3.5 h-3.5 text-amber-500 flex-shrink-0" /> Model Answer Guidance
              </p>
              <p className="text-ink-700 text-xs leading-relaxed">
                {q.model_answer_hint}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function InterviewReport() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    interviewAPI.getSession(id)
      .then(r => setReport(r.data))
      .catch(() => toast.error('Report not found'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" text="Loading report…" /></div>;
  if (!report) return <div className="text-center py-20 text-ink-500">Report not found.</div>;

  const {
    overall_score,
    summary_feedback,
    questions = [],
    job_title,
    top_strengths = [],
    top_improvements = [],
  } = report;
  const scoredQs = questions.filter(q => q.score != null);

  // Category scores
  const catMap = {};
  questions.forEach(q => {
    if (q.score != null) {
      if (!catMap[q.category]) catMap[q.category] = { sum: 0, n: 0 };
      catMap[q.category].sum += q.score;
      catMap[q.category].n++;
    }
  });

  return (
    <div className="space-y-8 animate-fade-in max-w-3xl">

      {/* Header */}
      <div className="flex items-start gap-4">
        <Link to="/interview" className="btn-ghost p-2 rounded-lg mt-1">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-ink-900 flex items-center gap-2">
            <Trophy className="w-6 h-6 text-amber-500" /> Interview Report
          </h1>
          <p className="text-ink-500 text-sm mt-0.5">{job_title}</p>
        </div>
      </div>

      {/* Score + Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="card flex flex-col items-center justify-center py-8 animate-bounce-in">
          <ScoreGauge score={overall_score || 0} size={150} label="Overall Score" />
          <p className="text-ink-400 text-xs mt-3">{scoredQs.length} of {questions.length} answered</p>
        </div>
        <div className="card col-span-2 space-y-3 animate-slide-up stagger-1">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-teal-100 flex items-center justify-center">
              <MessageSquare className="w-4 h-4 text-teal-600" />
            </div>
            <h2 className="font-semibold text-ink-900">Performance Summary</h2>
          </div>
          <p className="text-ink-600 leading-relaxed text-sm">
            {summary_feedback || 'Session completed. Review individual question feedback below.'}
          </p>
        </div>
      </div>

      {/* Top Strengths & Areas for Improvement */}
      {((top_strengths && top_strengths.length > 0) || (top_improvements && top_improvements.length > 0)) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 animate-slide-up stagger-2">
          {top_strengths && top_strengths.length > 0 && (
            <div className={`card space-y-3 ${(!top_improvements || top_improvements.length === 0) ? 'md:col-span-2' : ''}`}>
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-teal-100 flex items-center justify-center">
                  <CheckCircle className="w-4 h-4 text-teal-600" />
                </div>
                <h2 className="font-semibold text-ink-900">Top Strengths</h2>
              </div>
              <ul className="space-y-2">
                {top_strengths.map((str, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-ink-700 leading-relaxed">
                    <span className="text-teal-600 font-bold flex-shrink-0 mt-0.5">✓</span>
                    <span>{str}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {top_improvements && top_improvements.length > 0 && (
            <div className={`card space-y-3 ${(!top_strengths || top_strengths.length === 0) ? 'md:col-span-2' : ''}`}>
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-amber-100 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 text-amber-600" />
                </div>
                <h2 className="font-semibold text-ink-900">Areas for Improvement</h2>
              </div>
              <ul className="space-y-2">
                {top_improvements.map((imp, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-ink-700 leading-relaxed">
                    <span className="text-amber-600 font-bold flex-shrink-0 mt-0.5">→</span>
                    <span>{imp}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Category breakdown */}
      {Object.keys(catMap).length > 0 && (
        <div className="card space-y-4 animate-slide-up stagger-2">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-ink-100 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-ink-600" />
            </div>
            <h2 className="font-semibold text-ink-900">Category Breakdown</h2>
          </div>
          <div className="space-y-3">
            {Object.entries(catMap).map(([cat, { sum, n }], i) => (
              <CategoryBar key={cat} name={cat} score={sum / n} delay={`${i * 0.08}s`} />
            ))}
          </div>
        </div>
      )}

      {/* Question-by-question feedback */}
      <div className="animate-slide-up stagger-3">
        <h2 className="section-title mb-4">Question-by-Question Feedback</h2>
        <div className="space-y-2">
          {questions.map((q, i) => (
            <QuestionFeedbackRow key={q.id} q={q} index={i} />
          ))}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-3 pb-4">
        <Link to="/interview" className="btn-secondary">Back to Sessions</Link>
        <Link to="/interview" className="btn-primary">
          <MessageSquare className="w-4 h-4" /> New Session
        </Link>
      </div>
    </div>
  );
}
