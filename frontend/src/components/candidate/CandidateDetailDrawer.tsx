import React, { useState } from 'react';
import { X, Briefcase, MapPin, Sparkles, User, FileText, Tag, StickyNote, Clock, Cpu, Edit3 } from 'lucide-react';
import { Candidate, RecruiterNote, TimelineEvent } from '../../types';
import { OverviewTab } from './tabs/OverviewTab';
import { ExperienceTab } from './tabs/ExperienceTab';
import { SkillsTab } from './tabs/SkillsTab';
import { NotesTab } from './tabs/NotesTab';
import { TimelineTab } from './tabs/TimelineTab';
import { AiInsightsTab } from './tabs/AiInsightsTab';
import { CandidateEditModal } from './CandidateEditModal';

interface CandidateDetailDrawerProps {
  candidate: Candidate | null;
  onClose: () => void;
  selectedRequirementTitle?: string;
  notes: RecruiterNote[];
  timelineEvents: TimelineEvent[];
  onAddNote: (candidateId: string, content: string) => void;
  onAddContactEvent: (candidateId: string, type: string, note: string) => void;
  onUpdateCandidateProfile?: (candidateId: string, updatedData: any) => Promise<void>;
}

type TabType = 'overview' | 'experience' | 'skills' | 'notes' | 'timeline' | 'insights';

export const CandidateDetailDrawer: React.FC<CandidateDetailDrawerProps> = ({
  candidate,
  onClose,
  selectedRequirementTitle,
  notes,
  timelineEvents,
  onAddNote,
  onAddContactEvent,
  onUpdateCandidateProfile,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [isEditingProfile, setIsEditingProfile] = useState(false);

  if (!candidate) return null;

  const tabs: { id: TabType; label: string; icon: React.ElementType }[] = [
    { id: 'overview', label: 'Overview', icon: User },
    { id: 'experience', label: 'Experience', icon: FileText },
    { id: 'skills', label: 'Skills', icon: Tag },
    { id: 'notes', label: `Notes (${notes.length})`, icon: StickyNote },
    { id: 'timeline', label: 'Timeline', icon: Clock },
    { id: 'insights', label: 'AI Insights', icon: Cpu },
  ];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden select-none">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-2xl bg-white shadow-2xl flex flex-col border-l border-slate-200">
          
          {/* Header */}
          <div className="p-6 bg-gradient-to-r from-slate-900 to-indigo-950 text-white relative flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 border-2 border-white/20 flex items-center justify-center text-white font-extrabold text-xl shadow-lg">
                {candidate.name.charAt(0)}
              </div>

              <div>
                <h2 className="text-xl font-bold text-white tracking-tight flex items-center gap-2">
                  {candidate.name}
                  {candidate.matchScore !== undefined && (
                    <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/30 text-indigo-300 border border-indigo-400/30 text-xs font-bold flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-indigo-400" />
                      {candidate.matchScore}% Match
                    </span>
                  )}
                </h2>
                <p className="text-xs font-semibold text-indigo-300 flex items-center gap-1.5 mt-0.5">
                  <Briefcase className="w-3.5 h-3.5" />
                  {candidate.designation}
                  <span className="text-slate-400">•</span>
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  <span className="text-slate-300">{candidate.location || 'Unspecified'}</span>
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Employer: <span className="text-slate-200 font-medium">{candidate.currentCompany || candidate.latestCompany || 'Unspecified'}</span>
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {onUpdateCandidateProfile && (
                <button
                  type="button"
                  onClick={() => setIsEditingProfile(true)}
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
                  title="Edit Candidate Profile"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                  <span>Edit Profile</span>
                </button>
              )}

              <button
                type="button"
                onClick={onClose}
                className="p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors cursor-pointer"
                title="Close Drawer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center border-b border-slate-200 bg-slate-50 px-6 gap-1 overflow-x-auto scrollbar-none">
            {tabs.map((t) => {
              const Icon = t.icon;
              const isActive = activeTab === t.id;
              return (
                <button
                  key={t.id}
                  onClick={() => setActiveTab(t.id)}
                  className={`flex items-center gap-2 py-3 px-3.5 border-b-2 font-semibold text-xs transition-colors shrink-0 ${
                    isActive
                      ? 'border-indigo-600 text-indigo-600 bg-white'
                      : 'border-transparent text-slate-500 hover:text-slate-800 hover:bg-slate-100/60'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                  <span>{t.label}</span>
                </button>
              );
            })}
          </div>

          {/* Tab Contents */}
          <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50 select-text">
            {activeTab === 'overview' && (
              <OverviewTab
                candidate={candidate}
                onAddContactEvent={(type, note) => onAddContactEvent(candidate.id, type, note)}
              />
            )}

            {activeTab === 'experience' && (
              <ExperienceTab candidate={candidate} />
            )}

            {activeTab === 'skills' && (
              <SkillsTab candidate={candidate} />
            )}

            {activeTab === 'notes' && (
              <NotesTab
                candidateId={candidate.id}
                notes={notes}
                onAddNote={(content) => onAddNote(candidate.id, content)}
              />
            )}

            {activeTab === 'timeline' && (
              <TimelineTab events={timelineEvents} />
            )}

            {activeTab === 'insights' && (
              <AiInsightsTab
                candidate={candidate}
                selectedRequirementTitle={selectedRequirementTitle}
              />
            )}
          </div>
        </div>
      </div>

      {/* Edit Profile Modal */}
      {isEditingProfile && onUpdateCandidateProfile && (
        <CandidateEditModal
          candidate={candidate}
          onClose={() => setIsEditingProfile(false)}
          onSave={onUpdateCandidateProfile}
        />
      )}
    </div>
  );
};
