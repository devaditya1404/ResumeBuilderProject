import React, { useState } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2, Cpu, ShieldCheck } from 'lucide-react';
import { api } from '../api/client';

interface UploadResumesPageProps {
  onCandidateCreated?: () => void;
}

interface UploadTask {
  id: string;
  filename: string;
  size: string;
  progress: number;
  status: 'uploading' | 'parsing' | 'success' | 'partial' | 'failed';
  parsedName?: string;
  errorMessage?: string;
  extractionSummary?: {
    skills_count: number;
    experience_count: number;
    education_count: number;
    extraction_method: string;
    llm_model: string | null;
    total_experience_months: number | null;
  };
  timings?: {
    extraction_ms: number;
    llm_ms: number;
    total_ms: number;
  };
}

export const UploadResumesPage: React.FC<UploadResumesPageProps> = ({ onCandidateCreated }) => {
  const [tasks, setTasks] = useState<UploadTask[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  const handleUpload = async (files: FileList | File[]) => {
    const fileArray = Array.from(files);

    // Create upload tasks for each file
    const newTasks: UploadTask[] = fileArray.map((file) => ({
      id: `task-${Date.now()}-${Math.random().toString(36).substr(2, 4)}`,
      filename: file.name,
      size: `${(file.size / 1024).toFixed(0)} KB`,
      progress: 10,
      status: 'uploading' as const,
    }));

    setTasks((prev) => [...newTasks, ...prev]);

    // Simulate progress to parsing state
    setTimeout(() => {
      setTasks((prev) =>
        prev.map((t) =>
          newTasks.find((nt) => nt.id === t.id)
            ? { ...t, progress: 60, status: 'parsing' as const }
            : t
        )
      );
    }, 500);

    // Call real API
    try {
      const response = await api.uploadResumes(fileArray);

      // Update tasks with real results
      setTasks((prev) =>
        prev.map((t) => {
          const matchingNewTask = newTasks.find((nt) => nt.id === t.id);
          if (!matchingNewTask) return t;

          // Find the matching result from the API response
          const result = response.results?.find(
            (r: any) => r.filename === matchingNewTask.filename
          );

          if (!result) return { ...t, progress: 100, status: 'failed' as const, errorMessage: 'No response for this file' };

          const isPartial = result.parsing_status === 'PARTIAL';
          const isSuccess = result.success && !isPartial;

          if (result.success) {
            return {
              ...t,
              progress: 100,
              status: isPartial ? ('partial' as const) : ('success' as const),
              parsedName: result.candidate_name
                ? `${result.candidate_name}${result.extraction_summary?.current_title ? ` (${result.extraction_summary.current_title})` : ''}`
                : result.filename,
              extractionSummary: result.extraction_summary,
              timings: result.timings,
              errorMessage: isPartial ? 'AI extraction unavailable — contacts & name extracted' : undefined,
            };
          } else {
            return {
              ...t,
              progress: 100,
              status: 'failed' as const,
              errorMessage: result.errors?.join(', ') || 'Parse failed',
            };
          }
        })
      );

      // Notify parent that candidates may have been created
      if (response.success > 0 && onCandidateCreated) {
        onCandidateCreated();
      }
    } catch (error: any) {
      // Mark all tasks as failed
      setTasks((prev) =>
        prev.map((t) =>
          newTasks.find((nt) => nt.id === t.id)
            ? { ...t, progress: 100, status: 'failed' as const, errorMessage: error.message || 'Upload failed' }
            : t
        )
      );
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleUpload(e.dataTransfer.files);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleUpload(e.target.files);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-2xs space-y-2">
        <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
          <Upload className="w-5 h-5 text-indigo-600" />
          Drag & Drop Resume Parser
        </h2>
        <p className="text-xs text-slate-500">
          Upload individual PDF, DOCX or bulk ZIP resume archives. Extraction runs entirely locally on your Mac.
        </p>
      </div>

      {/* Dropzone Box */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-2xl p-10 text-center transition-all bg-white shadow-2xs ${
          isDragging ? 'border-indigo-600 bg-indigo-50/50 scale-[0.99]' : 'border-slate-300 hover:border-indigo-400'
        }`}
      >
        <div className="max-w-md mx-auto space-y-4">
          <div className="w-16 h-16 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center mx-auto shadow-2xs">
            <Upload className="w-8 h-8" />
          </div>

          <div>
            <h3 className="font-bold text-slate-900 text-base">Drop resumes here to parse</h3>
            <p className="text-xs text-slate-500 mt-1">Supports .pdf, .docx, and batch .zip resume bundles</p>
          </div>

          <label className="inline-block px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs rounded-xl shadow-md cursor-pointer transition-colors">
            Browse Local Files
            <input
              type="file"
              multiple
              accept=".pdf,.docx,.zip"
              onChange={handleFileSelect}
              className="hidden"
            />
          </label>

          <div className="flex items-center justify-center gap-4 text-[11px] text-slate-400 pt-2 border-t border-slate-100">
            <span className="flex items-center gap-1">
              <Cpu className="w-3.5 h-3.5 text-indigo-500" /> Local Ollama Parsing
            </span>
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" /> 100% Private & Off-line
            </span>
          </div>
        </div>
      </div>

      {/* Parser Pipeline Steps Visual */}
      <div className="p-4 rounded-xl bg-slate-900 text-white text-xs space-y-3">
        <h4 className="font-bold uppercase tracking-wider text-indigo-300 text-[11px]">
          Local Parser Pipeline Architecture
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2 text-[10px] text-center font-mono">
          <div className="p-2 rounded bg-slate-800 border border-slate-700">Resume File</div>
          <div className="p-2 rounded bg-slate-800 border border-slate-700 text-indigo-300">PyMuPDF / DOCX</div>
          <div className="p-2 rounded bg-slate-800 border border-slate-700">Text Normalizer</div>
          <div className="p-2 rounded bg-slate-800 border border-slate-700 text-emerald-300">Contact Regex</div>
          <div className="p-2 rounded bg-slate-800 border border-slate-700 text-purple-300">Ollama Qwen</div>
          <div className="p-2 rounded bg-slate-800 border border-slate-700">Pydantic Validate</div>
          <div className="p-2 rounded bg-slate-800 border border-slate-700 text-amber-300">Exp Calculation</div>
          <div className="p-2 rounded bg-slate-800 border border-slate-700 text-indigo-400">SQLite DB</div>
        </div>
      </div>

      {/* Recent Upload Progress Queue */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-2xs space-y-4">
        <h3 className="font-bold text-slate-900 text-sm">Processing Queue ({tasks.length})</h3>

        {tasks.length === 0 && (
          <div className="text-center py-8 text-slate-400 text-xs">
            No resumes uploaded yet. Drop or browse files above to begin.
          </div>
        )}

        <div className="space-y-3">
          {tasks.map((t) => (
            <div key={t.id} className="p-4 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2.5">
                  <FileText className="w-4 h-4 text-indigo-600" />
                  <div>
                    <p className="font-bold text-slate-900">{t.filename}</p>
                    <p className="text-[10px] text-slate-400">{t.size}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {t.status === 'uploading' && (
                    <span className="flex items-center gap-1 font-semibold text-blue-600 text-[11px]">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" /> Uploading ({t.progress}%)
                    </span>
                  )}
                  {t.status === 'parsing' && (
                    <span className="flex items-center gap-1 font-semibold text-purple-600 text-[11px]">
                      <Cpu className="w-3.5 h-3.5 animate-spin text-purple-600" /> Parsing via Ollama Qwen...
                    </span>
                  )}
                  {t.status === 'success' && (
                    <span className="flex items-center gap-1 font-semibold text-emerald-600 text-[11px]">
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Success
                    </span>
                  )}
                  {t.status === 'partial' && (
                    <span className="flex items-center gap-1 font-semibold text-amber-600 text-[11px]">
                      <AlertCircle className="w-4 h-4 text-amber-600" /> Partially Parsed (AI Unavailable)
                    </span>
                  )}
                  {t.status === 'failed' && (
                    <span className="flex items-center gap-1 font-semibold text-rose-600 text-[11px]">
                      <AlertCircle className="w-4 h-4 text-rose-600" /> Failed
                    </span>
                  )}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    t.status === 'success' ? 'bg-emerald-500' : t.status === 'failed' ? 'bg-rose-500' : 'bg-indigo-600'
                  }`}
                  style={{ width: `${t.progress}%` }}
                />
              </div>

              {t.parsedName && (
                <div className="text-[11px] font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded border border-indigo-100 flex items-center justify-between">
                  <span>Parsed Candidate: {t.parsedName}</span>
                  <span className="text-[10px] text-slate-500 font-normal">Stored in backend/data/talentvault.db</span>
                </div>
              )}

              {/* Extraction Summary for successful parses */}
              {t.status === 'success' && t.extractionSummary && (
                <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5 text-[10px] mt-1">
                  <div className="bg-white rounded px-2 py-1 border border-slate-200 text-center">
                    <div className="font-bold text-slate-900">{t.extractionSummary.skills_count}</div>
                    <div className="text-slate-400">Skills</div>
                  </div>
                  <div className="bg-white rounded px-2 py-1 border border-slate-200 text-center">
                    <div className="font-bold text-slate-900">{t.extractionSummary.experience_count}</div>
                    <div className="text-slate-400">Exp</div>
                  </div>
                  <div className="bg-white rounded px-2 py-1 border border-slate-200 text-center">
                    <div className="font-bold text-slate-900">{t.extractionSummary.education_count}</div>
                    <div className="text-slate-400">Edu</div>
                  </div>
                  <div className="bg-white rounded px-2 py-1 border border-slate-200 text-center">
                    <div className="font-bold text-slate-900">{t.extractionSummary.extraction_method}</div>
                    <div className="text-slate-400">Method</div>
                  </div>
                  <div className="bg-white rounded px-2 py-1 border border-slate-200 text-center">
                    <div className="font-bold text-slate-900">
                      {t.extractionSummary.total_experience_months !== null && t.extractionSummary.total_experience_months !== undefined
                        ? `${t.extractionSummary.total_experience_months}m`
                        : 'N/A'}
                    </div>
                    <div className="text-slate-400">Tot Exp</div>
                  </div>
                  <div className="bg-white rounded px-2 py-1 border border-slate-200 text-center">
                    <div className="font-bold text-slate-900">{t.timings?.total_ms?.toFixed(0) || '?'}ms</div>
                    <div className="text-slate-400">Time</div>
                  </div>
                </div>
              )}

              {t.errorMessage && (
                <div
                  className={`text-[11px] px-2.5 py-1 rounded border ${
                    t.status === 'partial'
                      ? 'text-amber-700 bg-amber-50 border-amber-200'
                      : 'text-rose-600 bg-rose-50 border-rose-100'
                  }`}
                >
                  {t.errorMessage}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
