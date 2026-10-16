import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { interviewAPI } from '../services/api';
import { FileText, MessageSquare, TrendingUp, ArrowRight, CheckCircle, Clock } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';

function StatCard({ icon: Icon, label, value, sub, color, delay }) {
  return (
    <div
      className="card flex items-start gap-4 animate-slide-up"
      style={{ animationDelay: delay }}
    >
      <div className={`w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-2xl font-black text-ink-900 leading-none">{value}</p>
        <p className="text-ink-500 text-sm mt-0.5">{label}</p>
        {sub && <p className="text-ink-400 text-xs mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

function QuickAction({ to, icon: Icon, title, desc, iconBg, delay }) {
  return (
    <Link
      to={to}
      className="card-hover group flex items-center gap-5 animate-slide-up"
      style={{ animationDelay: delay }}
    >
      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-teal transition-transform duration-300 group-hover:scale-110 ${iconBg}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div className="flex-1">
        <p className="text-ink-900 font-semibold">{title}</p>
        <p className="text-ink-500 text-sm">{desc}</p>
      </div>
      <ArrowRight className="w-4 h-4 text-ink-300 group-hover:text-teal-600 group-hover:translate-x-1 transition-all" />
    </Link>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    interviewAPI.sessions()
      .then(res => setSessions(res.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const completed = sessions.filter(s => s.status === 'completed');
  const avgScore  = completed.length
    ? Math.round(completed.reduce((s, x) => s + (x.overall_score || 0), 0) / completed.length)
    : 0;

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <LoadingSpinner size="lg" text="Loading…" />
    </div>
  );

  return (
    <div className="space-y-8 animate-fade-in">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-ink-900">
          Welcome back, <span className="text-teal-600">{user?.full_name?.split(' ')[0]}</span> 👋
        </h1>
        <p className="text-ink-500 mt-1 text-sm">Here's your career progress at a glance.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard icon={MessageSquare} label="Interview Sessions"  value={sessions.length}   color="bg-teal-600"   delay="0s" />
        <StatCard icon={CheckCircle}   label="Completed Sessions"  value={completed.length}  color="bg-emerald-600" delay="0.05s" />
        <StatCard
          icon={TrendingUp}
          label="Avg. Interview Score"
          value={avgScore ? `${avgScore}%` : '—'}
          sub={completed.length ? `from ${completed.length} completed` : 'No completed sessions yet'}
          color="bg-amber-500"
          delay="0.1s"
        />
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="section-title mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <QuickAction
            to="/cv"
            icon={FileText}
            title="Upload &amp; Optimize CV"
            desc="Get your CV matched to a job description"
            iconBg="bg-teal-600"
            delay="0.1s"
          />
          <QuickAction
            to="/interview"
            icon={MessageSquare}
            title="Start Interview Practice"
            desc="AI-powered mock interview session"
            iconBg="bg-emerald-600"
            delay="0.15s"
          />
        </div>
      </div>

      {/* Recent Sessions */}
      {sessions.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title">Recent Interviews</h2>
            <Link to="/interview" className="text-teal-600 text-sm font-medium hover:text-teal-700 flex items-center gap-1">
              View all <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
          <div className="space-y-3">
            {sessions.slice(0, 4).map((s, i) => (
              <Link
                key={s.id}
                to={s.status === 'completed' ? `/interview/${s.id}/report` : `/interview/${s.id}`}
                className="card-hover flex items-center gap-4 animate-slide-up"
                style={{ animationDelay: `${i * 0.05}s` }}
              >
                <div className={`w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  s.status === 'completed' ? 'bg-teal-100' : 'bg-ink-100'
                }`}>
                  <MessageSquare className={`w-4 h-4 ${s.status === 'completed' ? 'text-teal-600' : 'text-ink-500'}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-ink-900 text-sm font-semibold truncate">{s.job_title}</p>
                  <p className="text-ink-400 text-xs flex items-center gap-1 mt-0.5">
                    <Clock className="w-3 h-3" />
                    {new Date(s.created_at).toLocaleDateString()} · {s.answered_questions}/{s.total_questions} answered
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {s.overall_score != null && (
                    <span className={`text-sm font-bold ${
                      s.overall_score >= 75 ? 'text-teal-600' :
                      s.overall_score >= 50 ? 'text-amber-600' : 'text-red-500'
                    }`}>
                      {Math.round(s.overall_score)}%
                    </span>
                  )}
                  <span className={`badge ${s.status === 'completed' ? 'badge-teal' : 'badge-ink'}`}>
                    {s.status}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {sessions.length === 0 && (
        <div className="card text-center py-16 animate-fade-in">
          <div className="w-16 h-16 rounded-2xl bg-teal-50 flex items-center justify-center mx-auto mb-4">
            <TrendingUp className="w-8 h-8 text-teal-500" />
          </div>
          <h3 className="text-ink-900 font-bold text-lg mb-2">Your career journey starts here</h3>
          <p className="text-ink-500 text-sm mb-6 max-w-sm mx-auto">
            Upload your first CV or start an interview practice session to get personalized AI feedback.
          </p>
          <div className="flex items-center justify-center gap-3">
            <Link to="/cv" className="btn-primary text-sm">Upload CV</Link>
            <Link to="/interview" className="btn-secondary text-sm">Practice Interview</Link>
          </div>
        </div>
      )}
    </div>
  );
}
