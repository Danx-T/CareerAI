import { useCallback, useState } from 'react';
import { Upload, FileText, X, CheckCircle } from 'lucide-react';

export default function FileUpload({ onFileSelect, accept = '.pdf', maxSizeMB = 10 }) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [error, setError] = useState('');

  const validate = (file) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported.');
      return false;
    }
    if (file.size > maxSizeMB * 1024 * 1024) {
      setError(`File must be under ${maxSizeMB}MB.`);
      return false;
    }
    return true;
  };

  const handleFile = useCallback((file) => {
    setError('');
    if (!validate(file)) return;
    setSelectedFile(file);
    onFileSelect?.(file);
  }, [onFileSelect]);

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const onInputChange = (e) => {
    const file = e.target.files[0];
    if (file) handleFile(file);
  };

  const clearFile = (e) => {
    e.stopPropagation();
    setSelectedFile(null);
    setError('');
    onFileSelect?.(null);
  };

  return (
    <div className="w-full">
      <label
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`upload-zone ${dragOver ? 'upload-zone-active' : ''} ${selectedFile ? 'upload-zone-done' : ''}`}
      >
        <input type="file" accept={accept} className="hidden" onChange={onInputChange} />

        {selectedFile ? (
          <div className="flex flex-col items-center gap-3 p-8 animate-bounce-in">
            <div className="w-14 h-14 rounded-2xl bg-teal-100 flex items-center justify-center">
              <CheckCircle className="w-7 h-7 text-teal-600" />
            </div>
            <div className="text-center">
              <p className="text-ink-900 font-semibold text-sm">{selectedFile.name}</p>
              <p className="text-ink-400 text-xs mt-0.5">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB · PDF
              </p>
            </div>
            <button
              onClick={clearFile}
              className="flex items-center gap-1 text-xs text-ink-400 hover:text-red-500 transition-colors"
            >
              <X className="w-3 h-3" /> Remove file
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-4 p-8">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-all duration-300 ${
              dragOver ? 'bg-teal-200 scale-110 rotate-3' : 'bg-teal-100'
            }`}>
              {dragOver
                ? <FileText className="w-8 h-8 text-teal-600" />
                : <Upload className="w-8 h-8 text-teal-500" />
              }
            </div>
            <div className="text-center">
              <p className="text-ink-800 font-semibold">
                {dragOver ? 'Drop your PDF here' : 'Drag & drop your CV'}
              </p>
              <p className="text-ink-400 text-sm mt-1">
                or <span className="text-teal-600 font-medium hover:text-teal-700">browse files</span>
                &nbsp;· PDF up to {maxSizeMB}MB
              </p>
            </div>
          </div>
        )}
      </label>

      {error && (
        <p className="mt-2 text-red-500 text-sm flex items-center gap-1.5">
          <X className="w-4 h-4 flex-shrink-0" /> {error}
        </p>
      )}
    </div>
  );
}
