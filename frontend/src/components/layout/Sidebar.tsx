import React from 'react';
import { 
  LayoutDashboard, 
  Users, 
  Upload, 
  Briefcase, 
  Sparkles, 
  MessageSquareText, 
  BarChart3, 
  Settings, 
  BrainCircuit,
  UserCheck
} from 'lucide-react';
import { PageId } from '../../types';

interface SidebarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activePage, onNavigate }) => {
  const navItems = [
    { id: 'dashboard' as PageId, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'vault' as PageId, label: 'Talent Vault', icon: Users },
    { id: 'upload' as PageId, label: 'Upload Resumes', icon: Upload },
    { id: 'requirements' as PageId, label: 'Requirements', icon: Briefcase },
    { id: 'recommendations' as PageId, label: 'AI Recommendations', icon: Sparkles },
    { id: 'chat' as PageId, label: 'AI Recruiter Chat', icon: MessageSquareText },
    { id: 'reports' as PageId, label: 'Reports', icon: BarChart3 },
    { id: 'settings' as PageId, label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-300 flex flex-col h-screen shrink-0 border-r border-slate-800 shadow-xl select-none">
      {/* App Branding */}
      <div className="p-5 flex items-center gap-3 border-b border-slate-800/80 bg-slate-950/40">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-500 flex items-center justify-center text-white shadow-lg shadow-indigo-500/25">
          <BrainCircuit className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center gap-1.5">
            <h1 className="font-bold text-white tracking-tight text-base">ResumeX</h1>
            <span className="text-[10px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
              Brain
            </span>
          </div>
          <p className="text-[11px] text-slate-400 font-medium">TalentVault AI • Local</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        <div className="px-3 pb-2 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
          Main Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg font-medium text-sm transition-all duration-150 group ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30 font-semibold'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800/60'
              }`}
            >
              <Icon
                className={`w-4 h-4 transition-colors ${
                  isActive ? 'text-white' : 'text-slate-400 group-hover:text-indigo-400'
                }`}
              />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Bottom Section: Local Recruiter Workspace */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/40">
        <div className="flex items-center gap-3 p-2.5 rounded-lg bg-slate-800/50 border border-slate-700/50">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold text-xs shadow">
            <UserCheck className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-white truncate">Recruiter</p>
            <p className="text-[11px] text-indigo-400 font-medium truncate">Workspace • Local Engine</p>
          </div>
          <span className="w-2 h-2 rounded-full bg-emerald-400 ring-4 ring-emerald-400/20" title="Local System Active" />
        </div>
      </div>
    </aside>
  );
};
