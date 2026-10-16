export default function CVComparison({ original, optimized }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      {/* Original */}
      <div className="bg-white border border-ink-100 rounded-2xl overflow-hidden shadow-card">
        <div className="flex items-center gap-2.5 px-5 py-3.5 bg-ink-50 border-b border-ink-100">
          <span className="w-2.5 h-2.5 rounded-full bg-ink-300" />
          <span className="text-sm font-semibold text-ink-600">Original CV</span>
          <span className="ml-auto badge-ink">Before</span>
        </div>
        <div className="p-5 max-h-[520px] overflow-y-auto">
          <pre className="text-xs text-ink-600 leading-relaxed whitespace-pre-wrap font-mono">
            {original || <span className="italic text-ink-300">No text extracted yet.</span>}
          </pre>
        </div>
      </div>

      {/* Optimized */}
      <div className="bg-white border border-teal-200 rounded-2xl overflow-hidden shadow-teal">
        <div className="flex items-center gap-2.5 px-5 py-3.5 bg-teal-50 border-b border-teal-100">
          <span className="w-2.5 h-2.5 rounded-full bg-teal-500" />
          <span className="text-sm font-semibold text-teal-700">AI-Optimized CV</span>
          <span className="ml-auto badge-teal">Optimized</span>
        </div>
        <div className="p-5 max-h-[520px] overflow-y-auto">
          <pre className="text-xs text-ink-800 leading-relaxed whitespace-pre-wrap font-mono">
            {optimized || <span className="italic text-ink-300">Run optimization to see results.</span>}
          </pre>
        </div>
      </div>
    </div>
  );
}
