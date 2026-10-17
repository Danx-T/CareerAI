import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { cvAPI } from '../services/api';
import FileUpload from '../components/FileUpload';
import LoadingSpinner from '../components/LoadingSpinner';
import { FileText, Sparkles, ChevronRight, Info } from 'lucide-react';
import toast from 'react-hot-toast';

/* ── Step indicator ───────────────────────────────────────── */
function StepBadge({ num, active, done }) {
  return (
    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
      done  ? 'bg-teal-600 text-white' :
      active ? 'bg-teal-600 text-white shadow-teal' :
               'bg-ink-100 text-ink-400'
    }`}>
      {done ? '✓' : num}
    </div>
  );
}

export default function CVPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [extractedText, setExtractedText] = useState('');
  const [filename, setFilename] = useState('');
  const [uploading, setUploading] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [form, setForm] = useState({ job_title: '', job_description: '' });

  const step1Done = !!extractedText;

  // Step 1: Upload PDF → extract text
  const handleUpload = async () => {
    if (!file) { toast.error('Please select a PDF file first'); return; }
    setUploading(true);
    try {
      const { data } = await cvAPI.upload(file);
      const rawText = data.extracted_text || '';
      if (rawText.length > 20000) {
        setExtractedText(rawText.slice(0, 20000));
        toast('CV text exceeded 20,000 characters and was trimmed to fit the analysis limit.', { icon: '⚠️' });
      } else {
        setExtractedText(rawText);
      }
      setFilename(data.filename);
      toast.success('Text extracted — fill in the job details below');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  // Step 2: Optimize → navigate to results
  const handleOptimize = async () => {
    if (!form.job_title.trim() || !form.job_description.trim()) {
      toast.error('Please enter both job title and description');
      return;
    }
    setOptimizing(true);
    try {
      const { data } = await cvAPI.optimize({
        cv_text: extractedText,
        job_title: form.job_title,
        job_description: form.job_description,
      });
      navigate('/cv/results', {
        state: { filename, original_text: extractedText, result: data, job_title: form.job_title },
      });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Optimization failed');
    } finally {
      setOptimizing(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6 animate-fade-in">

      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-ink-900">CV Optimizer</h1>
        <p className="text-ink-500 mt-1 text-sm">Upload your CV, paste a job description, and get an AI-tailored version in seconds.</p>
      </div>

      {/* Step progress */}
      <div className="flex items-center gap-3">
        <StepBadge num={1} active={!step1Done} done={step1Done} />
        <span className={`text-sm font-medium ${step1Done ? 'text-teal-700' : 'text-ink-900'}`}>Upload CV</span>
        <div className="flex-1 h-px bg-ink-100 mx-2" />
        <StepBadge num={2} active={step1Done} done={false} />
        <span className={`text-sm font-medium ${step1Done ? 'text-ink-900' : 'text-ink-400'}`}>Job Details</span>
      </div>

      {/* ── Step 1: Upload ──────────────────────────────────── */}
      <div className={`card transition-all duration-300 ${step1Done ? 'opacity-60' : ''}`}>
        <div className="flex items-center gap-2 mb-4">
          <FileText className="w-5 h-5 text-teal-600" />
          <h2 className="font-semibold text-ink-900">Upload Your CV</h2>
        </div>
        <FileUpload onFileSelect={setFile} />
        <button
          onClick={handleUpload}
          disabled={!file || uploading || step1Done}
          className="btn-primary mt-4 w-full"
        >
          {uploading ? (
            <><LoadingSpinner size="sm" /> Extracting text…</>
          ) : step1Done ? (
            <>✓ Text extracted from {filename}</>
          ) : (
            <>Upload &amp; Extract Text</>
          )}
        </button>
      </div>

      {/* ── Step 2: Job Details ─────────────────────────────── */}
      <div className={`transition-all duration-500 ${step1Done ? 'animate-slide-up' : 'opacity-40 pointer-events-none'}`}>
        <div className="card space-y-5">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-teal-600" />
            <h2 className="font-semibold text-ink-900">Target Job</h2>
          </div>

          <div>
            <label className="label">Job Title</label>
            <input
              type="text"
              maxLength={200}
              placeholder="e.g. Senior Software Engineer"
              value={form.job_title}
              onChange={e => setForm(f => ({ ...f, job_title: e.target.value }))}
              className="input-field"
              disabled={!step1Done}
            />
          </div>

          <div>
            <label className="label">Job Description</label>
            <div className="flex items-center gap-1.5 mb-1.5">
              <Info className="w-3 h-3 text-ink-400" />
              <span className="text-xs text-ink-400">Paste the full listing for the best match analysis (max 10,000 characters)</span>
            </div>
            <textarea
              rows={8}
              maxLength={10000}
              placeholder="Paste the full job description here…"
              value={form.job_description}
              onChange={e => setForm(f => ({ ...f, job_description: e.target.value }))}
              className="textarea-field"
              disabled={!step1Done}
            />
          </div>

          <button
            onClick={handleOptimize}
            disabled={!step1Done || optimizing}
            className="btn-primary w-full py-3.5"
          >
            {optimizing ? (
              <><LoadingSpinner size="sm" /> Optimizing with AI…</>
            ) : (
              <><Sparkles className="w-4 h-4" /> Optimize My CV <ChevronRight className="w-4 h-4" /></>
            )}
          </button>

          {optimizing && (
            <p className="text-teal-600 text-xs text-center animate-pulse">
              ✨ AI is analyzing your CV against the job — this takes about 20 seconds…
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
