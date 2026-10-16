import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Zap, Mail, Lock, User, ArrowRight, CheckCircle } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';

const perks = [
  'AI-powered CV optimization',
  'Role-specific interview questions',
  'Instant answer feedback',
  'Free to get started',
];

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm) { toast.error('Passwords do not match'); return; }
    if (form.password.length < 8)       { toast.error('Password must be at least 8 characters'); return; }
    setLoading(true);
    try {
      await register({ full_name: form.full_name, email: form.email, password: form.password });
      toast.success('Account created! Please sign in.');
      navigate('/login');
    } catch (err) {
      const detail = err.response?.data?.detail;
      toast.error(Array.isArray(detail) ? detail[0]?.msg : (detail || 'Registration failed.'));
    } finally {
      setLoading(false);
    }
  };

  const set = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  return (
    <div className="min-h-screen flex bg-white">
      {/* Left panel — decorative */}
      <div className="hidden lg:flex lg:w-5/12 bg-ink-900 flex-col items-center justify-center p-12 relative overflow-hidden">
        <div className="absolute inset-0 bg-dot-grid bg-dot opacity-10" />
        <div className="relative">
          <Link to="/" className="inline-flex items-center gap-3 mb-14">
            <div className="w-11 h-11 rounded-2xl bg-teal-600 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-black text-white">CareerAI</span>
          </Link>
          <h2 className="text-3xl font-black text-white mb-3 leading-tight">
            Start your career<br />
            <span className="text-teal-400">journey today.</span>
          </h2>
          <p className="text-ink-300 text-sm leading-relaxed mb-10">
            Join thousands of professionals who've landed better jobs with AI-powered coaching.
          </p>
          <ul className="space-y-3">
            {perks.map(p => (
              <li key={p} className="flex items-center gap-3">
                <div className="w-6 h-6 rounded-full bg-teal-500/20 flex items-center justify-center flex-shrink-0">
                  <CheckCircle className="w-3.5 h-3.5 text-teal-400" />
                </div>
                <span className="text-ink-300 text-sm">{p}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Right panel — form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-sm animate-slide-up">
          {/* Mobile logo */}
          <Link to="/" className="lg:hidden inline-flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-ink-900">CareerAI</span>
          </Link>

          <h1 className="text-2xl font-bold text-ink-900 mb-1">Create your account</h1>
          <p className="text-ink-500 text-sm mb-8">Start optimizing your career today</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label" htmlFor="full_name">Full Name</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-400" />
                <input
                  id="full_name" type="text" required placeholder="Jane Doe"
                  value={form.full_name} onChange={set('full_name')}
                  className="input-field pl-10"
                  autoComplete="name"
                />
              </div>
            </div>

            <div>
              <label className="label" htmlFor="reg_email">Email</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-400" />
                <input
                  id="reg_email" type="email" required placeholder="you@example.com"
                  value={form.email} onChange={set('email')}
                  className="input-field pl-10"
                  autoComplete="email"
                />
              </div>
            </div>

            <div>
              <label className="label" htmlFor="reg_password">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-400" />
                <input
                  id="reg_password" type="password" required placeholder="Min. 8 characters"
                  value={form.password} onChange={set('password')}
                  className="input-field pl-10"
                  autoComplete="new-password"
                />
              </div>
            </div>

            <div>
              <label className="label" htmlFor="reg_confirm">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-ink-400" />
                <input
                  id="reg_confirm" type="password" required placeholder="Repeat password"
                  value={form.confirm} onChange={set('confirm')}
                  className="input-field pl-10"
                  autoComplete="new-password"
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-3.5 mt-2">
              {loading
                ? <><LoadingSpinner size="sm" /> Creating account…</>
                : <>Create Account <ArrowRight className="w-4 h-4" /></>
              }
            </button>
          </form>

          <p className="text-center text-ink-500 text-sm mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-teal-600 hover:text-teal-700 font-semibold">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
