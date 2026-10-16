import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { interviewAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import { MessageSquare, Plus, ChevronRight, Briefcase, Clock, X } from 'lucide-react';
import toast from 'react-hot-toast';

function SessionRow({ s, index }) {
  const isComplete = s.status === 'completed';
  const dest = isComplete ? `/interview/${s.id}/report` : `/interview/${s.id}`;
  return (
    <Link
      to={dest}
      className="card-hover flex items-center gap-4 animate-slide-up"
      style={{ animationDelay: `${index * 0.05}s` }}
    >
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
        isComplete ? 'bg-teal-100' : 'bg-ink-100'
      }`}>
        <MessageSquare className={`w-5 h-5 ${isComplete ? 'text-teal-600' : 'text-ink-500'}`} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-ink-900 font-semibold truncate">{s.job_title}</p>
        <p className="text-ink-400 text-xs flex items-center gap-2 mt-0.5">
          <Clock className="w-3 h-3" />
          {new Date(s.created_at).toLocaleDateString()}
          <span>·</span>
          {s.answered_questions}/{s.total_questions} answered
        </p>
      </div>
      <div className="flex items-center gap-2.5">
        {s.overall_score != null && (
          <span className={`text-sm font-bold ${
            s.overall_score >= 75 ? 'text-teal-600' :
            s.overall_score >= 50 ? 'text-amber-600' : 'text-red-500'
          }`}>
            {Math.round(s.overall_score)}%
          </span>
        )}
        <span className={`badge ${isComplete ? 'badge-teal' : 'badge-ink'}`}>{s.status}</span>
        <ChevronRight className="w-4 h-4 text-ink-300 group-hover:text-teal-600 transition-colors" />
      </div>
    </Link>
  );
}

export default function InterviewSetup() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ job_title: '', job_description: '', num_questions: 8 });

  useEffect(() => {
    interviewAPI.sessions()
      .then(res => setSessions(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleStart = async (e) => {
    e.preventDefault();
    if (!form.job_title || !form.job_description) {
      toast.error('Please fill in job title and description');
      return;
    }
    setStarting(true);
    try {
      const { data } = await interviewAPI.start({
        job_title: form.job_title,
        job_description: form.job_description,
        num_questions: parseInt(form.num_questions),
      });
      toast.success('Session created!');
      navigate(`/interview/${data.id}`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create session');
    } finally {
      setStarting(false);
    }
  };

  const set = (field) => (e) => setForm(f => ({ ...f, [field]: e.target.value }));

  if (loading) return (
    <div className="flex justify-center py-20">
      <LoadingSpinner size="lg" text="Loading sessions…" />
    </div>
  );

  return (
    <div className="space-y-8 animate-fade-in">

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-900">Interview Coach</h1>
          <p className="text-ink-500 mt-1 text-sm">Practice with AI-generated questions and get instant feedback on every answer.</p>
        </div>
        {!showForm && (
          <button onClick={() => setShowForm(true)} className="btn-primary flex-shrink-0">
            <Plus className="w-4 h-4" /> New Session
          </button>
        )}
      </div>

      {/* ── New Session Form ──────────────────────────────────── */}
      {showForm && (
        <div className="card animate-slide-up space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-teal-100 flex items-center justify-center">
                <Briefcase className="w-4 h-4 text-teal-600" />
              </div>
              <h2 className="font-semibold text-ink-900">New Interview Session</h2>
            </div>
            <button onClick={() => setShowForm(false)} className="btn-ghost p-2 rounded-lg">
              <X className="w-4 h-4" />
            </button>
          </div>

          <form onSubmit={handleStart} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">Job Title *</label>
                <input
                  type="text" required placeholder="e.g. Frontend Developer"
                  value={form.job_title} onChange={set('job_title')} className="input-field"
                />
              </div>
              <div>
                <label className="label">Number of Questions</label>
                <select value={form.num_questions} onChange={set('num_questions')} className="input-field">
                  {[5, 8, 10, 12, 15].map(n => (
                    <option key={n} value={n}>{n} questions</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="label">Job Description *</label>
              <textarea
                rows={6} required placeholder="Paste the job description here…"
                value={form.job_description} onChange={set('job_description')} className="textarea-field"
              />
            </div>

            <div className="flex items-center gap-3 pt-1">
              <button type="submit" disabled={starting} className="btn-primary">
                {starting
                  ? <><LoadingSpinner size="sm" /> Generating questions…</>
                  : 'Start Interview'
                }
              </button>
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">
                Cancel
              </button>
              {starting && (
                <p className="text-teal-600 text-xs animate-pulse ml-2">
                  ✨ AI is crafting your questions…
                </p>
              )}
            </div>
          </form>
        </div>
      )}

      {/* ── Sessions list ─────────────────────────────────────── */}
      <div>
        <h2 className="section-title mb-4">Your Sessions</h2>
        {sessions.length === 0 ? (
          <div className="card text-center py-14">
            <div className="w-14 h-14 rounded-2xl bg-ink-100 flex items-center justify-center mx-auto mb-4">
              <MessageSquare className="w-7 h-7 text-ink-400" />
            </div>
            <p className="text-ink-600 font-medium mb-1">No interview sessions yet</p>
            <p className="text-ink-400 text-sm mb-5">Create your first session to start practicing.</p>
            <button onClick={() => setShowForm(true)} className="btn-primary text-sm mx-auto">
              Start Your First Session
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {sessions.map((s, i) => <SessionRow key={s.id} s={s} index={i} />)}
          </div>
        )}
      </div>
    </div>
  );
}
