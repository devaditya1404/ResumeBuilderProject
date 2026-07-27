import React from 'react';
import { 
  Users, 
  Upload, 
  Briefcase, 
  Sparkles, 
  PhoneCall, 
  Award, 
  ArrowUpRight, 
  ChevronRight,
  TrendingUp,
  FileText,
  Clock
} from 'lucide-react';
import type { Candidate, Requirement, AppReportStats, PageId } from '../types';

interface DashboardPageProps {
  candidates: Candidate[];
  requirements: Requirement[];
  stats: AppReportStats;
  loading?: boolean;
  onSelectCandidate: (candidate: Candidate) => void;
  onNavigate: (page: PageId) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({
  candidates,
  requirements,
  stats,
  loading = false,
  onSelectCandidate,
  onNavigate
}) => {
  const metricCards = [
    { label: 'Total Candidates', value: stats.totalCandidates, change: 'SQLite Database', icon: Users, color: 'from-indigo-600 to-blue-600' },
    { label: 'New Resumes', value: stats.newResumesThisWeek, change: 'Uploaded locally', icon: Upload, color: 'from-purple-600 to-indigo-600' },
    { label: 'Active Requirements', value: stats.activeRequirements, change: 'Active job criteria', icon: Briefcase, color: 'from-blue-600 to-cyan-600' },
    { label: 'Top Matches', value: stats.topMatchesCount, change: '>80% Match score', icon: Sparkles, color: 'from-emerald-600 to-teal-600' },
    { label: 'Candidates Contacted', value: stats.candidatesContacted, change: 'Outreach logged', icon: PhoneCall, color: 'from-amber-600 to-orange-600' },
    { label: 'Avg Match Score', value: stats.totalCandidates > 0 ? `${stats.avgMatchScore}%` : '-', change: 'Deterministic avg', icon: Award, color: 'from-rose-600 to-pink-600' },
  ];

  return (
    <div className="space-y-6 pb-12">
      {/* Metrics Banner */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {metricCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className="bg-white rounded-xl border border-slate-200/80 p-4 shadow-2xs hover:shadow-md transition-shadow relative overflow-hidden group"
            >
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">{card.label}</span>
                <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${card.color} text-white flex items-center justify-center shadow-xs`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <p className="text-2xl font-extrabold text-slate-900 mt-2 tracking-tight">
                {loading ? '...' : card.value}
              </p>
              <p className="text-[10px] text-slate-500 font-medium flex items-center gap-1 mt-1">
                <TrendingUp className="w-3 h-3 text-emerald-500" />
                {card.change}
              </p>
            </div>
          );
        })}
      </div>

      {/* Main Grid Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Recent Candidates & Top AI Recommendations */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Top AI Recommendations */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  Top AI Match Recommendations
                </h3>
                <p className="text-xs text-slate-500">Highest scoring candidate matches for active job criteria.</p>
              </div>
              <button
                onClick={() => onNavigate('recommendations')}
                className="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
              >
                <span>View All</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {candidates.length === 0 ? (
              <div className="p-8 text-center bg-slate-50/50 rounded-xl border border-dashed border-slate-200 text-xs text-slate-500 space-y-1">
                <Sparkles className="w-6 h-6 text-slate-300 mx-auto mb-1" />
                <p className="font-semibold text-slate-700">No candidate recommendations yet.</p>
                <p className="text-[11px] text-slate-400">Upload resumes in Phase 3 to populate talent vault matches.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {candidates.slice(0, 3).map((cand) => (
                  <div
                    key={cand.id}
                    onClick={() => onSelectCandidate(cand)}
                    className="p-3.5 rounded-xl bg-slate-50 hover:bg-indigo-50/50 border border-slate-200/70 hover:border-indigo-200 transition-all cursor-pointer flex items-center justify-between group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-bold flex items-center justify-center text-sm shadow-2xs">
                        {cand.name.charAt(0)}
                      </div>
                      <div>
                        <h4 className="font-bold text-slate-900 group-hover:text-indigo-600 transition-colors text-sm">
                          {cand.name}
                        </h4>
                        <p className="text-xs text-slate-500 font-medium">
                          {cand.designation} • {cand.experienceDisplay}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {cand.matchScore !== undefined && (
                        <span className="px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-800 font-extrabold text-xs">
                          {cand.matchScore}% Match
                        </span>
                      )}
                      <ChevronRight className="w-4 h-4 text-slate-400 group-hover:translate-x-0.5 transition-transform" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recent Resume Uploads Table */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                  <FileText className="w-4 h-4 text-indigo-600" />
                  Recent Resume Uploads & Parsed Candidates
                </h3>
                <p className="text-xs text-slate-500">Processed locally via PyMuPDF + Ollama Qwen pipeline.</p>
              </div>
              <button
                onClick={() => onNavigate('upload')}
                className="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
              >
                <span>Upload New</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {candidates.length === 0 ? (
              <div className="p-8 text-center bg-slate-50/50 rounded-xl border border-dashed border-slate-200 text-xs text-slate-500 space-y-1">
                <FileText className="w-6 h-6 text-slate-300 mx-auto mb-1" />
                <p className="font-semibold text-slate-700">No resumes uploaded yet.</p>
                <p className="text-[11px] text-slate-400">Go to Upload Resumes page to add candidates.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider">
                      <th className="py-2.5 px-3">Candidate</th>
                      <th className="py-2.5 px-3">Designation</th>
                      <th className="py-2.5 px-3">Exp</th>
                      <th className="py-2.5 px-3">Employer</th>
                      <th className="py-2.5 px-3">Notice</th>
                      <th className="py-2.5 px-3">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {candidates.map((cand) => (
                      <tr key={cand.id} className="hover:bg-slate-50">
                        <td className="py-3 px-3 font-bold text-slate-900">{cand.name}</td>
                        <td className="py-3 px-3 text-slate-600">{cand.designation}</td>
                        <td className="py-3 px-3 font-semibold text-indigo-600">{cand.experienceDisplay}</td>
                        <td className="py-3 px-3 text-slate-600">{cand.currentCompany || cand.latestCompany || '-'}</td>
                        <td className="py-3 px-3 text-slate-500">{cand.noticePeriod || 'Unspecified'}</td>
                        <td className="py-3 px-3">
                          <button
                            onClick={() => onSelectCandidate(cand)}
                            className="px-2.5 py-1 text-xs font-semibold rounded bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
                          >
                            View Drawer
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Active Requirements & Recruitment Activity */}
        <div className="space-y-6">

          {/* Active Requirements List */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-indigo-600" />
                Active Requirements
              </h3>
              <button
                onClick={() => onNavigate('requirements')}
                className="text-xs font-bold text-indigo-600 hover:text-indigo-700"
              >
                Manage
              </button>
            </div>

            {requirements.length === 0 ? (
              <div className="p-6 text-center bg-slate-50/50 rounded-xl border border-dashed border-slate-200 text-xs text-slate-500 space-y-1">
                <Briefcase className="w-6 h-6 text-slate-300 mx-auto mb-1" />
                <p className="font-semibold text-slate-700">No active requirements yet.</p>
                <p className="text-[11px] text-slate-400">Create a job requirement to start matching candidates.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {requirements.map((req) => (
                  <div key={req.id} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <div className="flex items-start justify-between">
                      <h4 className="font-bold text-slate-900 text-xs">{req.title}</h4>
                      <span className="px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 text-[10px] font-bold">
                        {req.activeCandidateMatchesCount} matches
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 line-clamp-2">{req.description}</p>
                    <div className="flex flex-wrap gap-1 pt-1">
                      {req.requiredSkills.slice(0, 3).map((s, i) => (
                        <span key={i} className="px-1.5 py-0.5 rounded bg-white text-slate-700 text-[10px] border border-slate-200">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Recruitment Activity Log */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-5 shadow-2xs space-y-4">
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2 border-b border-slate-100 pb-3">
              <Clock className="w-4 h-4 text-indigo-600" />
              Recent Recruitment Activity
            </h3>

            <div className="space-y-3 text-xs">
              <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 flex items-start gap-2.5">
                <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1 shrink-0" />
                <div>
                  <p className="font-bold text-slate-800">SQLite Database Connected</p>
                  <p className="text-slate-500 text-[11px]">backend/data/talentvault.db active in WAL mode.</p>
                  <span className="text-[10px] text-slate-400">System Ready</span>
                </div>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
};
