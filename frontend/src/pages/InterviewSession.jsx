import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { interviewAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { ArrowLeft, ChevronLeft, ChevronRight, Flag, CheckCircle, MessageSquare } from 'lucide-react';
import toast from 'react-hot-toast';

/* ── Question card ──────────────────────────────────────────── */
function QuestionCard({ question, index, children }) {
  const categoryColors = {
    behavioral:  'bg-violet-100 text-violet-700',
    technical:   'bg-teal-100 text-teal-700',
    situational: 'bg-amber-100 text-amber-700',
    general:     'bg-ink-100 text-ink-600',
  };
  const cat = question.category?.toLowerCase() || 'general';

  return (
    <div className="card space-y-4 animate-slide-up">
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-lg bg-ink-100 flex items-center justify-center flex-shrink-0 text-sm font-bold text-ink-600">
          {index + 1}
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <span className={`badge text-xs ${categoryColors[cat] || categoryColors.general}`}>
              {question.category}
            </span>
          </div>
          <p className="text-ink-900 font-medium leading-relaxed">{question.question_text}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

export default function InterviewSession() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [savedIds, setSavedIds] = useState(new Set());
  const [completing, setCompleting] = useState(false);
  const saveTimers = useRef({});

  useEffect(() => {
    interviewAPI.getSession(id)
      .then(r => {
        setSession(r.data);
        const existing = {};
        const alreadySaved = new Set();
        r.data.questions.forEach(q => {
          if (q.user_answer) { existing[q.id] = q.user_answer; alreadySaved.add(q.id); }
        });
        setAnswers(existing);
        setSavedIds(alreadySaved);
      })
      .catch(() => toast.error('Session not found'))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="flex justify-center py-20"><LoadingSpinner size="lg" text="Loading session…" /></div>;
  if (!session) return <div className="text-center py-20 text-ink-500">Session not found.</div>;

  const questions = session.questions;
  const currentQ  = questions[currentIdx];
  const totalAnswered = savedIds.size;
  const progress = (totalAnswered / questions.length) * 100;

  const handleAnswerChange = (questionId, value) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
    if (saveTimers.current[questionId]) clearTimeout(saveTimers.current[questionId]);
    saveTimers.current[questionId] = setTimeout(async () => {
      if (!value.trim()) return;
      try {
        await interviewAPI.saveAnswer(id, questionId, value);
        setSavedIds(prev => new Set([...prev, questionId]));
      } catch { /* silent */ }
    }, 800);
  };

  const handleComplete = async () => {
    const unanswered = questions.filter(q => !savedIds.has(q.id) && !answers[q.id]?.trim());
    if (unanswered.length === questions.length) {
      toast.error('Please answer at least one question before finishing.');
      return;
    }
    if (unanswered.length > 0 && !window.confirm(`${unanswered.length} question(s) are unanswered. Finish anyway?`)) return;

    setCompleting(true);
    try {
      const pending = questions.filter(q => answers[q.id]?.trim() && !savedIds.has(q.id));
      await Promise.all(pending.map(q => interviewAPI.saveAnswer(id, q.id, answers[q.id])));
      toast.loading('Evaluating your answers… this may take a moment.', { id: 'completing' });
      await interviewAPI.complete(id);
      toast.dismiss('completing');
      toast.success('Interview complete! Loading your report…');
      navigate(`/interview/${id}/report`);
    } catch (err) {
      toast.dismiss('completing');
      toast.error(err.response?.data?.detail || 'Failed to complete session');
    } finally {
      setCompleting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">

      {/* Header */}
      <div className="flex items-start gap-4">
        <Link to="/interview" className="btn-ghost p-2 rounded-lg mt-1">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold text-ink-900 truncate">{session.job_title}</h1>
          <p className="text-ink-500 text-sm mt-0.5">
            Question {currentIdx + 1} of {questions.length} · {totalAnswered} saved
          </p>
          {/* Progress bar */}
          <div className="mt-3 h-1.5 bg-ink-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-teal-500 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
        <button
          onClick={handleComplete}
          disabled={completing}
          className="btn-secondary text-sm py-2 flex-shrink-0"
        >
          {completing ? <LoadingSpinner size="sm" /> : <><Flag className="w-4 h-4" /> Finish</>}
        </button>
      </div>

      {/* Question */}
      <QuestionCard question={currentQ} index={currentIdx}>
        <textarea
          rows={6}
          placeholder="Type your answer here… Be specific and use the STAR method for behavioral questions."
          value={answers[currentQ.id] || ''}
          onChange={e => handleAnswerChange(currentQ.id, e.target.value)}
          disabled={completing}
          className="textarea-field text-sm"
        />
        <div className="h-5">
          {savedIds.has(currentQ.id) && answers[currentQ.id]?.trim() && (
            <span className="flex items-center gap-1.5 text-xs text-teal-600">
              <CheckCircle className="w-3.5 h-3.5" /> Answer saved
            </span>
          )}
        </div>
      </QuestionCard>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setCurrentIdx(i => Math.max(0, i - 1))}
          disabled={currentIdx === 0}
          className="btn-secondary text-sm py-2"
        >
          <ChevronLeft className="w-4 h-4" /> Previous
        </button>

        {/* Dot nav */}
        <div className="flex items-center gap-1.5 flex-wrap justify-center max-w-[200px]">
          {questions.map((q, i) => (
            <button
              key={q.id}
              onClick={() => setCurrentIdx(i)}
              title={`Question ${i + 1}`}
              className={`w-2.5 h-2.5 rounded-full transition-all duration-200 ${
                i === currentIdx   ? 'bg-teal-600 scale-125' :
                savedIds.has(q.id) ? 'bg-teal-300' :
                                     'bg-ink-200 hover:bg-ink-300'
              }`}
            />
          ))}
        </div>

        {currentIdx < questions.length - 1 ? (
          <button onClick={() => setCurrentIdx(i => i + 1)} className="btn-secondary text-sm py-2">
            Next <ChevronRight className="w-4 h-4" />
          </button>
        ) : (
          <button onClick={handleComplete} disabled={completing} className="btn-primary text-sm py-2">
            {completing ? <LoadingSpinner size="sm" /> : <><Flag className="w-4 h-4" /> Complete</>}
          </button>
        )}
      </div>
    </div>
  );
}
