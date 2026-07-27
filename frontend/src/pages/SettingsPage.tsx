import React, { useState } from 'react';
import { Settings, Cpu, Database, Folder, Bug, Save, ShieldCheck } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [ollamaModel, setOllamaModel] = useState('qwen2.5:7b-instruct');
  const [resumePath, setResumePath] = useState('backend/data/resumes/');
  const [dbPath, setDbPath] = useState('backend/data/talentvault.db');
  const [debugMode, setDebugMode] = useState(true);
  const [savedSuccess, setSavedSuccess] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl">
      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-2xs space-y-1">
        <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
          <Settings className="w-5 h-5 text-indigo-600" />
          Local Environment Settings
        </h2>
        <p className="text-xs text-slate-500">
          Configure local Ollama model parameters, SQLite storage, and parser debug options. No cloud keys required.
        </p>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* Local AI Configuration */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Cpu className="w-4 h-4 text-indigo-600" />
            Local LLM (Ollama Model) Settings
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="font-bold text-slate-700 block mb-1">Active Ollama Model Target (`.env` sync)</label>
              <select
                value={ollamaModel}
                onChange={(e) => setOllamaModel(e.target.value)}
                className="w-full p-3 rounded-lg border border-slate-200 bg-white font-mono font-semibold focus:ring-2 focus:ring-indigo-500"
              >
                <option value="qwen2.5:7b-instruct">qwen2.5:7b-instruct (Recommended)</option>
                <option value="qwen2.5:14b-instruct">qwen2.5:14b-instruct (Higher precision)</option>
                <option value="llama3.1:8b">llama3.1:8b</option>
                <option value="mistral:7b">mistral:7b</option>
              </select>
              <p className="text-[11px] text-slate-400 mt-1">
                Selected model will be invoked via backend AI service API.
              </p>
            </div>
          </div>
        </div>

        {/* Database & Storage Paths */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Database className="w-4 h-4 text-emerald-600" />
            Local File System Storage & SQLite Configuration
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="font-bold text-slate-700 block mb-1 flex items-center gap-1">
                <Folder className="w-3.5 h-3.5 text-slate-400" /> Resume Storage Path
              </label>
              <input
                type="text"
                value={resumePath}
                onChange={(e) => setResumePath(e.target.value)}
                className="w-full p-2.5 rounded-lg border border-slate-200 font-mono font-semibold text-slate-800 focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="font-bold text-slate-700 block mb-1 flex items-center gap-1">
                <Database className="w-3.5 h-3.5 text-slate-400" /> SQLite Database URI
              </label>
              <input
                type="text"
                value={dbPath}
                onChange={(e) => setDbPath(e.target.value)}
                className="w-full p-2.5 rounded-lg border border-slate-200 font-mono font-semibold text-slate-800 focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Debug & Verification Mode */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
            <Bug className="w-4 h-4 text-purple-600" />
            Parser Debug & Validation Mode
          </h3>

          <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <div>
              <p className="text-xs font-bold text-slate-900">Enable Parser Step-by-Step Inspector</p>
              <p className="text-[11px] text-slate-500">
                Log original resume → extracted text → deterministic regex contact → raw LLM JSON → validated candidate.
              </p>
            </div>

            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={debugMode}
                onChange={(e) => setDebugMode(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-300 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600" />
            </label>
          </div>
        </div>

        {/* Save button */}
        <div className="flex items-center justify-between pt-2">
          {savedSuccess ? (
            <span className="text-xs font-bold text-emerald-600 flex items-center gap-1">
              <ShieldCheck className="w-4 h-4" /> Local settings updated successfully!
            </span>
          ) : <span />}

          <button
            type="submit"
            className="flex items-center gap-2 py-2.5 px-5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl shadow-md transition-colors"
          >
            <Save className="w-4 h-4" />
            Save Configurations
          </button>
        </div>
      </form>
    </div>
  );
};
