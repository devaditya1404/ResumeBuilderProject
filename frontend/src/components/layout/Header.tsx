import React, { useState, useEffect } from 'react';
import { Search, Cpu, Database, Bell } from 'lucide-react';
import { PageId } from '../../types';
import { api } from '../../api/client';

interface HeaderProps {
  activePage: PageId;
  onSearchClick?: () => void;
  selectedRequirementTitle?: string;
}

const PAGE_TITLES: Record<PageId, { title: string; subtitle: string }> = {
  dashboard: {
    title: 'Recruitment Dashboard',
    subtitle: 'AI-powered talent insights and candidate tracking overview.'
  },
  vault: {
    title: 'AI Talent Vault',
    subtitle: 'Search candidates semantically or apply filters to screen profiles.'
  },
  upload: {
    title: 'Upload Resumes',
    subtitle: 'Drag & drop resumes for deterministic parsing & AI structured extraction.'
  },
  requirements: {
    title: 'Job Requirements',
    subtitle: 'Manage target job openings and auto-extract structured JD criteria.'
  },
  recommendations: {
    title: 'AI Recommendations',
    subtitle: 'Automated candidate matching and skill gap breakdown.'
  },
  chat: {
    title: 'AI Recruiter Chat',
    subtitle: 'Query your candidate database using natural language AI.'
  },
  reports: {
    title: 'Analytics & Reports',
    subtitle: 'Local talent metrics, skill distribution, and recruitment statistics.'
  },
  settings: {
    title: 'System Settings',
    subtitle: 'Manage AI provider models, storage directories, and debug parser options.'
  }
};

export const Header: React.FC<HeaderProps> = ({ activePage, onSearchClick, selectedRequirementTitle }) => {
  const currentInfo = PAGE_TITLES[activePage] || { title: 'TalentVault', subtitle: 'AI Recruitment Intelligence' };
  const [aiHealth, setAiHealth] = useState<{ available: boolean; provider: string; model: string; error?: string } | null>(null);

  useEffect(() => {
    let mounted = true;
    api.getAiHealth()
      .then((data) => {
        if (mounted) setAiHealth(data);
      })
      .catch(() => {
        if (mounted) setAiHealth({ available: false, provider: 'offline', model: 'Unavailable' });
      });
    return () => { mounted = false; };
  }, []);

  const isGroq = aiHealth?.provider === 'groq';
  const isOllama = aiHealth?.provider === 'ollama';
  const isAvailable = aiHealth?.available ?? true;

  const providerLabel = isGroq ? 'Groq Cloud' : isOllama ? 'Ollama Local' : isAvailable ? 'AI Engine' : 'AI Offline';
  const modelLabel = isGroq 
    ? 'Llama 3.1 Active' 
    : isOllama 
      ? `${aiHealth?.model || 'Qwen2.5'} Active` 
      : (aiHealth?.error ? 'Needs Config' : 'Active');

  return (
    <header className="bg-white border-b border-slate-200/80 px-6 py-4 flex items-center justify-between sticky top-0 z-10 shadow-xs">
      <div>
        <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
          {currentInfo.title}
          {selectedRequirementTitle && (
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
              Active: {selectedRequirementTitle}
            </span>
          )}
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">{currentInfo.subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        {/* Quick Search trigger */}
        <button
          onClick={onSearchClick}
          className="flex items-center gap-2 px-3.5 py-2 text-xs font-medium text-slate-500 bg-slate-100 hover:bg-slate-200/80 rounded-lg border border-slate-200/80 transition-colors"
        >
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <span>Quick candidate search...</span>
          <kbd className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] font-semibold text-slate-400 bg-white border border-slate-200 rounded shadow-2xs">
            ⌘K
          </kbd>
        </button>

        {/* Dynamic AI Engine Status Badge */}
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-white text-xs font-medium border shadow-xs ${
          isAvailable ? 'bg-slate-900 border-slate-800' : 'bg-amber-950 border-amber-800'
        }`}>
          <Cpu className={`w-3.5 h-3.5 ${isAvailable ? 'text-indigo-400 animate-pulse' : 'text-amber-400'}`} />
          <div className="flex flex-col text-[11px]">
            <span className="font-semibold text-slate-200 leading-tight">{providerLabel}</span>
            <span className={`text-[9px] font-mono ${isAvailable ? 'text-indigo-300' : 'text-amber-300'}`}>{modelLabel}</span>
          </div>
        </div>

        {/* SQLite Database Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-50 text-emerald-800 text-xs font-medium border border-emerald-200">
          <Database className="w-3.5 h-3.5 text-emerald-600" />
          <span className="text-[11px] font-semibold">SQLite WAL</span>
        </div>
      </div>
    </header>
  );
};
