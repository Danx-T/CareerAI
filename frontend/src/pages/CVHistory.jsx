import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { cvAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import toast from 'react-hot-toast';
import {
  FileText, Trash2, ChevronDown, ChevronUp, TrendingUp,
  Lightbulb, Tag, ArrowRight, Download,
} from 'lucide-react';

function ScoreBadge({ score }) {
  const pct = Math.round(score);
  const color =
    pct >= 75 ? 'bg-teal-50 text-teal-700 border-teal-200' :
    pct >= 50 ? 'bg-amber-50 text-amber-700 border-amber-200' :
                'bg-rose-50  text-rose-700  border-rose-200';
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-sm font-bold border ${color}`}>
      <TrendingUp className="w-3.5 h-3.5" /> {pct}%
    </span>
  );
}

function Chip({ children, variant = 'ink' }) {
  const colors = {
    ink:    'bg-ink-50   text-ink-600   border-ink-200',
    teal:   'bg-teal-50  text-teal-700  border-teal-200',
    amber:  'bg-amber-50 text-amber-700 border-amber-200',
    rose:   'bg-rose-50  text-rose-600  border-rose-200',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${colors[variant]}`}>
      {children}
    </span>
  );
}

function HistoryCard({ item, onDelete }) {
  const [open, setOpen] = useState(false);

  const download = () => {
    const blob = new Blob([item.optimized_text], { type: 'text/plain' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `cv_optimized_${item.job_title.replace(/\s+/g, '_')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const fmt = (iso) =>
    new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });

  return (
    <div className="bg-white rounded-2xl border border-ink-100 shadow-card overflow-hidden animate-slide-up">
      {/* Header row */}
      <div className="flex items-center gap-4 p-5">
        <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-200 flex items-center justify-center flex-shrink-0">
          <FileText className="w-5 h-5 text-teal-600" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-ink-900 truncate">{item.job_title}</p>
          <p className="text-xs text-ink-400 mt-0.5">{fmt(item.created_at)}</p>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <ScoreBadge score={item.match_score} />
          <button
            onClick={download}
            title="Download optimized CV"
            className="p-2 rounded-lg text-ink-400 hover:bg-teal-50 hover:text-teal-600 transition-colors"
          >
            <Download className="w-4 h-4" />
          </button>
          <button
            onClick={() => onDelete(item)}
            title="Delete"
            className="p-2 rounded-lg text-ink-400 hover:bg-rose-50 hover:text-rose-600 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
          <button
            onClick={() => setOpen(o => !o)}
            className="p-2 rounded-lg text-ink-400 hover:bg-ink-50 transition-colors"
          >
            {open ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Expandable details */}
      {open && (
        <div className="border-t border-ink-100 p-5 space-y-5 animate-slide-up-sm">

          {/* Optimized text */}
          <div>
            <p className="text-xs font-semibold text-ink-400 uppercase tracking-wider mb-2">Optimized CV Text</p>
            <pre className="bg-ink-50 rounded-xl p-4 text-xs text-ink-700 leading-relaxed whitespace-pre-wrap font-mono max-h-60 overflow-y-auto border border-ink-100">
              {item.optimized_text}
            </pre>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* Key improvements */}
            {item.key_improvements?.length > 0 && (
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <TrendingUp className="w-3.5 h-3.5 text-teal-600" />
                  <p className="text-xs font-semibold text-ink-500 uppercase tracking-wider">Key Improvements</p>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {item.key_improvements.map((k, i) => <Chip key={i} variant="teal">{k}</Chip>)}
                </div>
              </div>
            )}

            {/* Suggestions */}
            {item.suggestions?.length > 0 && (
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
                  <p className="text-xs font-semibold text-ink-500 uppercase tracking-wider">Suggestions</p>
                </div>
                <ul className="space-y-1">
                  {item.suggestions.map((s, i) => (
                    <li key={i} className="text-xs text-ink-600 flex items-start gap-1.5">
                      <span className="text-amber-500 mt-0.5">•</span> {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Missing keywords */}
            {item.missing_keywords?.length > 0 && (
              <div>
                <div className="flex items-center gap-1.5 mb-2">
                  <Tag className="w-3.5 h-3.5 text-rose-500" />
                  <p className="text-xs font-semibold text-ink-500 uppercase tracking-wider">Missing Keywords</p>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {item.missing_keywords.map((k, i) => <Chip key={i} variant="rose">{k}</Chip>)}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ConfirmModal({ message, onConfirm, onCancel }) {
  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl border border-ink-100 p-6 w-full max-w-sm mx-4">
        <p className="text-ink-700 text-sm leading-relaxed">{message}</p>
        <div className="flex gap-3 mt-5">
          <button onClick={onCancel} className="flex-1 px-4 py-2 rounded-xl border border-ink-200 text-ink-600 text-sm font-medium hover:bg-ink-50 transition-colors">
            Cancel
          </button>
          <button onClick={onConfirm} className="flex-1 px-4 py-2 rounded-xl bg-rose-600 text-white text-sm font-semibold hover:bg-rose-700 transition-colors">
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

export default function CVHistory() {
  const [history, setHistory]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [confirm, setConfirm]   = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await cvAPI.history();
      setHistory(data);
    } catch {
      toast.error('Failed to load CV history');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDelete = (item) => {
    setConfirm({
      message: `Delete the optimization for "${item.job_title}"? This cannot be undone.`,
      action: async () => {
        await cvAPI.deleteHistory(item.id);
        toast.success('Record deleted');
        load();
      },
    });
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-4xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink-900">CV Optimization History</h1>
          <p className="text-ink-500 text-sm mt-0.5">
            All your past CV optimizations — click any row to expand and review the results.
          </p>
        </div>
        <Link to="/cv" className="btn-primary flex-shrink-0 flex items-center gap-2">
          <FileText className="w-4 h-4" /> New Optimization
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {loading ? (
        <div className="flex justify-center py-20">
          <LoadingSpinner size="lg" text="Loading history…" />
        </div>
      ) : history.length === 0 ? (
        <div className="card text-center py-16">
          <div className="w-14 h-14 rounded-2xl bg-teal-50 flex items-center justify-center mx-auto mb-4">
            <FileText className="w-7 h-7 text-teal-500" />
          </div>
          <p className="text-ink-700 font-semibold mb-1">No optimizations yet</p>
          <p className="text-ink-400 text-sm mb-5">Upload your CV and run your first optimization to see results here.</p>
          <Link to="/cv" className="btn-primary text-sm inline-flex items-center gap-2">
            Upload & Optimize CV <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map(item => (
            <HistoryCard key={item.id} item={item} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {confirm && (
        <ConfirmModal
          message={confirm.message}
          onConfirm={async () => { setConfirm(null); await confirm.action(); }}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  );
}
