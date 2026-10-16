import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, FileText, MessageSquare, LogOut, User, Zap, ShieldCheck, History } from 'lucide-react';

const navItems = [
  { to: '/dashboard',  icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/cv',         icon: FileText,        label: 'CV Optimizer' },
  { to: '/cv/history', icon: History,         label: 'CV History' },
  { to: '/interview',  icon: MessageSquare,   label: 'Interview Coach' },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => { logout(); navigate('/'); };

  return (
    <aside className="fixed left-0 top-0 h-full w-64 bg-white border-r border-ink-100 flex flex-col z-40 shadow-card">
      {/* Logo */}
      <div className="p-6 border-b border-ink-100">
        <NavLink to="/dashboard" className="flex items-center gap-3 group">
          <div className="w-9 h-9 rounded-xl bg-teal-600 flex items-center justify-center shadow-teal transition-all duration-200 group-hover:scale-105">
            <Zap className="w-5 h-5 text-white" />
          </div>
          <div>
            <p className="font-bold text-ink-900 text-sm leading-none">CareerAI</p>
            <p className="text-xs text-ink-400 mt-0.5">CV · Interview</p>
          </div>
        </NavLink>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                isActive
                  ? 'bg-teal-50 text-teal-700 border border-teal-200'
                  : 'text-ink-600 hover:text-ink-900 hover:bg-ink-50'
              }`
            }
          >
            <Icon className="w-5 h-5 flex-shrink-0" />
            {label}
          </NavLink>
        ))}

        {/* Admin link — only visible to admins */}
        {user?.is_admin && (
          <NavLink
            to="/admin"
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 mt-2 ${
                isActive
                  ? 'bg-violet-50 text-violet-700 border border-violet-200'
                  : 'text-violet-500 hover:text-violet-700 hover:bg-violet-50'
              }`
            }
          >
            <ShieldCheck className="w-5 h-5 flex-shrink-0" />
            Admin Panel
          </NavLink>
        )}
      </nav>

      {/* User */}
      <div className="p-4 border-t border-ink-100">
        <div className="flex items-center gap-3 px-3 py-3 rounded-xl bg-ink-50">
          <div className="w-8 h-8 rounded-full bg-teal-100 border border-teal-200 flex items-center justify-center flex-shrink-0">
            <User className="w-4 h-4 text-teal-600" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-ink-900 text-sm font-semibold truncate">{user?.full_name}</p>
            <p className="text-ink-400 text-xs truncate">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            title="Logout"
            className="text-ink-400 hover:text-red-500 transition-colors p-1 rounded-lg hover:bg-red-50"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
