import { useState, useEffect, useCallback } from 'react';
import { adminAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import toast from 'react-hot-toast';
import {
  Users, BarChart3, MessageSquare, ShieldCheck, ShieldOff,
  UserX, Trash2, TrendingUp, CheckCircle, Clock, RefreshCw,
} from 'lucide-react';

// ── Stat card ─────────────────────────────────────────────────────────────────
function StatCard({ icon: Icon, label, value, color }) {
  const colors = {
    teal:   'bg-teal-50   border-teal-200   text-teal-600',
    violet: 'bg-violet-50 border-violet-200 text-violet-600',
    amber:  'bg-amber-50  border-amber-200  text-amber-600',
    sky:    'bg-sky-50    border-sky-200    text-sky-600',
    rose:   'bg-rose-50   border-rose-200   text-rose-600',
    indigo: 'bg-indigo-50 border-indigo-200 text-indigo-600',
  };
  return (
    <div className="bg-white rounded-2xl border border-ink-100 p-5 shadow-card flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl border flex items-center justify-center flex-shrink-0 ${colors[color]}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-xs text-ink-400 font-medium uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-ink-900 mt-0.5">{value ?? '—'}</p>
      </div>
    </div>
  );
}

// ── Badge ─────────────────────────────────────────────────────────────────────
function Badge({ children, variant = 'neutral' }) {
  const v = {
    green:  'bg-teal-50   text-teal-700   border-teal-200',
    red:    'bg-rose-50   text-rose-700   border-rose-200',
    violet: 'bg-violet-50 text-violet-700 border-violet-200',
    amber:  'bg-amber-50  text-amber-700  border-amber-200',
    neutral:'bg-ink-50    text-ink-500    border-ink-200',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${v[variant]}`}>
      {children}
    </span>
  );
}

// ── Confirm modal ─────────────────────────────────────────────────────────────
function ConfirmModal({ message, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl border border-ink-100 p-6 w-full max-w-sm mx-4">
        <p className="text-ink-700 text-sm leading-relaxed">{message}</p>
        <div className="flex gap-3 mt-5">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 rounded-xl border border-ink-200 text-ink-600 text-sm font-medium hover:bg-ink-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="flex-1 px-4 py-2 rounded-xl bg-rose-600 text-white text-sm font-semibold hover:bg-rose-700 transition-colors"
          >
            Confirm
          </button>
        </div>
      </div>
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function AdminDashboard() {
  const { user: me } = useAuth();
  const [tab, setTab]         = useState('users');
  const [stats, setStats]     = useState(null);
  const [users, setUsers]     = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [confirm, setConfirm] = useState(null); // { message, action }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sRes, uRes, seRes] = await Promise.all([
        adminAPI.stats(),
        adminAPI.users(),
        adminAPI.sessions(),
      ]);
      setStats(sRes.data);
      setUsers(uRes.data);
      setSessions(seRes.data);
    } catch {
      toast.error('Failed to load admin data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const ask = (message, action) => setConfirm({ message, action });
  const closeConfirm = () => setConfirm(null);

  const doConfirm = async () => {
    if (!confirm) return;
    closeConfirm();
    await confirm.action();
    load();
  };

  // ── user actions ──────────────────────────────────────────────────────────
  const handleToggleActive = (u) =>
    ask(
      `${u.is_active ? 'Deactivate' : 'Activate'} account for ${u.full_name}?`,
      async () => {
        await adminAPI.toggleActive(u.id);
        toast.success(`User ${u.is_active ? 'deactivated' : 'activated'}`);
      },
    );

  const handleToggleAdmin = (u) =>
    ask(
      `${u.is_admin ? 'Revoke' : 'Grant'} admin privileges for ${u.full_name}?`,
      async () => {
        await adminAPI.toggleAdmin(u.id);
        toast.success(`Admin status ${u.is_admin ? 'revoked' : 'granted'}`);
      },
    );

  const handleDeleteUser = (u) =>
    ask(
      `Permanently delete ${u.full_name} (${u.email}) and all their data?`,
      async () => {
        await adminAPI.deleteUser(u.id);
        toast.success('User deleted');
      },
    );

  const handleDeleteSession = (s) =>
    ask(
      `Delete interview session "${s.job_title}" by ${s.user_name}?`,
      async () => {
        await adminAPI.deleteSession(s.id);
        toast.success('Session deleted');
      },
    );

  const fmt = (iso) =>
    iso ? new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';

  return (
    <div className="max-w-7xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink-900">Admin Dashboard</h1>
          <p className="text-sm text-ink-400 mt-0.5">Logged in as <span className="font-medium text-violet-600">{me?.email}</span></p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl border border-ink-200 text-ink-600 text-sm font-medium hover:bg-ink-50 transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats grid */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard icon={Users}        label="Total Users"        value={stats.total_users}        color="teal"   />
          <StatCard icon={CheckCircle}  label="Active Users"       value={stats.active_users}       color="violet" />
          <StatCard icon={ShieldCheck}  label="Admin Users"        value={stats.admin_users}        color="indigo" />
          <StatCard icon={MessageSquare}label="Total Sessions"     value={stats.total_sessions}     color="sky"    />
          <StatCard icon={TrendingUp}   label="Completed Sessions" value={stats.completed_sessions} color="amber"  />
          <StatCard icon={BarChart3}    label="Avg Score"          value={stats.avg_score !== null ? `${stats.avg_score}%` : '—'} color="rose" />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-ink-100 pb-0">
        {[['users', 'Users', Users], ['sessions', 'Sessions', MessageSquare]].map(([key, label, Icon]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-t-xl border transition-all ${
              tab === key
                ? 'bg-white border-ink-200 border-b-white text-teal-700 -mb-px z-10'
                : 'border-transparent text-ink-500 hover:text-ink-700'
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Users table */}
      {tab === 'users' && (
        <div className="bg-white rounded-2xl border border-ink-100 shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-ink-50 border-b border-ink-100">
                <tr>
                  {['ID', 'Name', 'Email', 'Status', 'Role', 'Joined', 'Actions'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-ink-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-50">
                {loading ? (
                  <tr><td colSpan={7} className="px-5 py-10 text-center text-ink-400">Loading…</td></tr>
                ) : users.length === 0 ? (
                  <tr><td colSpan={7} className="px-5 py-10 text-center text-ink-400">No users found</td></tr>
                ) : users.map(u => (
                  <tr key={u.id} className="hover:bg-ink-50/50 transition-colors">
                    <td className="px-5 py-3 text-ink-400 font-mono text-xs">#{u.id}</td>
                    <td className="px-5 py-3 font-medium text-ink-900">{u.full_name}</td>
                    <td className="px-5 py-3 text-ink-500">{u.email}</td>
                    <td className="px-5 py-3">
                      <Badge variant={u.is_active ? 'green' : 'red'}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </td>
                    <td className="px-5 py-3">
                      <Badge variant={u.is_admin ? 'violet' : 'neutral'}>
                        {u.is_admin ? 'Admin' : 'User'}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 text-ink-400 text-xs">{fmt(u.created_at)}</td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleToggleActive(u)}
                          disabled={u.id === me?.id}
                          title={u.is_active ? 'Deactivate' : 'Activate'}
                          className="p-1.5 rounded-lg text-ink-400 hover:bg-amber-50 hover:text-amber-600 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          {u.is_active ? <ShieldOff className="w-4 h-4" /> : <CheckCircle className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => handleToggleAdmin(u)}
                          disabled={u.id === me?.id}
                          title={u.is_admin ? 'Revoke Admin' : 'Grant Admin'}
                          className="p-1.5 rounded-lg text-ink-400 hover:bg-violet-50 hover:text-violet-600 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          <ShieldCheck className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteUser(u)}
                          disabled={u.id === me?.id}
                          title="Delete User"
                          className="p-1.5 rounded-lg text-ink-400 hover:bg-rose-50 hover:text-rose-600 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        >
                          <UserX className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Sessions table */}
      {tab === 'sessions' && (
        <div className="bg-white rounded-2xl border border-ink-100 shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-ink-50 border-b border-ink-100">
                <tr>
                  {['ID', 'User', 'Job Title', 'Status', 'Score', 'Q\'s', 'Date', 'Actions'].map(h => (
                    <th key={h} className="px-5 py-3 text-left text-xs font-semibold text-ink-500 uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-50">
                {loading ? (
                  <tr><td colSpan={8} className="px-5 py-10 text-center text-ink-400">Loading…</td></tr>
                ) : sessions.length === 0 ? (
                  <tr><td colSpan={8} className="px-5 py-10 text-center text-ink-400">No sessions found</td></tr>
                ) : sessions.map(s => (
                  <tr key={s.id} className="hover:bg-ink-50/50 transition-colors">
                    <td className="px-5 py-3 text-ink-400 font-mono text-xs">#{s.id}</td>
                    <td className="px-5 py-3">
                      <p className="font-medium text-ink-900">{s.user_name}</p>
                      <p className="text-ink-400 text-xs">{s.user_email}</p>
                    </td>
                    <td className="px-5 py-3 text-ink-700 max-w-[160px] truncate" title={s.job_title}>{s.job_title}</td>
                    <td className="px-5 py-3">
                      <Badge variant={s.status === 'completed' ? 'green' : 'amber'}>
                        {s.status === 'completed' ? 'Completed' : 'Active'}
                      </Badge>
                    </td>
                    <td className="px-5 py-3 font-semibold text-ink-700">
                      {s.overall_score != null ? `${s.overall_score.toFixed(0)}%` : '—'}
                    </td>
                    <td className="px-5 py-3 text-ink-500">
                      {s.answered_questions}/{s.total_questions}
                    </td>
                    <td className="px-5 py-3 text-ink-400 text-xs">{fmt(s.created_at)}</td>
                    <td className="px-5 py-3">
                      <button
                        onClick={() => handleDeleteSession(s)}
                        title="Delete Session"
                        className="p-1.5 rounded-lg text-ink-400 hover:bg-rose-50 hover:text-rose-600 transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Confirm modal */}
      {confirm && (
        <ConfirmModal
          message={confirm.message}
          onConfirm={doConfirm}
          onCancel={closeConfirm}
        />
      )}
    </div>
  );
}
