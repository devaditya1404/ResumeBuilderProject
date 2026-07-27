import React from 'react';
import { Briefcase, MapPin, Clock, DollarSign, ChevronRight, Award, Sparkles, Trash2 } from 'lucide-react';
import { Candidate } from '../../types';

interface CandidateCardProps {
  candidate: Candidate;
  onSelect: (candidate: Candidate) => void;
  onDelete?: (candidate: Candidate, e: React.MouseEvent) => void;
  selectedRequirementId?: string;
}

export const CandidateCard: React.FC<CandidateCardProps> = ({ candidate, onSelect, onDelete, selectedRequirementId }) => {
  return (
    <div
      onClick={() => onSelect(candidate)}
      className="group bg-white rounded-xl border border-slate-200/90 hover:border-indigo-400 p-5 transition-all duration-200 hover:shadow-lg cursor-pointer flex flex-col justify-between relative overflow-hidden"
    >
      {/* Top accent bar on hover */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity" />

      <div>
        {/* Header section with Name & Match Score & Delete Icon */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 rounded-full bg-gradient-to-br from-indigo-100 to-purple-100 border border-indigo-200 flex items-center justify-center text-indigo-700 font-bold text-base shadow-2xs group-hover:scale-105 transition-transform">
              {candidate.name.charAt(0)}
            </div>
            <div>
              <h3 className="font-bold text-slate-900 group-hover:text-indigo-600 transition-colors text-base leading-tight">
                {candidate.name}
              </h3>
              <p className="text-xs font-semibold text-indigo-600 flex items-center gap-1 mt-0.5">
                <Briefcase className="w-3 h-3 text-indigo-500" />
                {candidate.designation}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Match Score Badge if applicable */}
            {candidate.matchScore !== undefined && (
              <div className="flex items-center gap-1 px-2.5 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 font-bold text-xs shadow-2xs">
                <Sparkles className="w-3 h-3 text-indigo-500" />
                <span>{candidate.matchScore}% Match</span>
              </div>
            )}

            {/* Trash Icon Button */}
            {onDelete && (
              <button
                type="button"
                title="Delete Candidate"
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(candidate, e);
                }}
                className="p-1 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer shrink-0"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Current / Latest employer badge */}
        <div className="mb-3 text-xs text-slate-500 flex items-center gap-1.5 bg-slate-50 px-2.5 py-1.5 rounded-md border border-slate-100">
          <span className="font-medium text-slate-700">Employer:</span>
          <span className="font-semibold text-slate-900 truncate">
            {candidate.currentCompany || candidate.latestCompany || 'Not specified'}
          </span>
          {candidate.currentCompany && (
            <span className="text-[10px] bg-emerald-100 text-emerald-700 px-1.5 py-0.2 rounded font-semibold ml-auto">
              Current
            </span>
          )}
        </div>

        {/* Key Metadata Grid */}
        <div className="grid grid-cols-2 gap-y-2 gap-x-3 text-xs text-slate-600 mb-4 bg-slate-50/50 p-2.5 rounded-lg border border-slate-100">
          <div className="flex items-center gap-1.5" title="Total calculated experience">
            <Award className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
            <span className="font-semibold text-slate-800">{candidate.experienceDisplay}</span>
          </div>

          <div className="flex items-center gap-1.5" title="Location">
            <MapPin className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className="truncate">{candidate.location || 'Not specified'}</span>
          </div>

          <div className="flex items-center gap-1.5" title="Notice Period">
            <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className={candidate.noticePeriod ? 'font-medium text-slate-700' : 'text-slate-400 italic'}>
              {candidate.noticePeriod || 'Notice: Unspecified'}
            </span>
          </div>

          <div className="flex items-center gap-1.5" title="Expected Salary">
            <DollarSign className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <span className={candidate.expectedSalary ? 'font-medium text-slate-700' : 'text-slate-400 italic'}>
              {candidate.expectedSalary || 'Salary: Unspecified'}
            </span>
          </div>
        </div>

        {/* Top Skills Tags */}
        <div className="space-y-1">
          <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Top Skills</p>
          <div className="flex flex-wrap gap-1.5 max-h-16 overflow-hidden">
            {candidate.topSkills.slice(0, 5).map((skill, idx) => (
              <span
                key={idx}
                className="px-2 py-0.5 text-[11px] font-medium rounded-md bg-slate-100 text-slate-700 border border-slate-200/80 group-hover:bg-indigo-50 group-hover:text-indigo-700 group-hover:border-indigo-200 transition-colors"
              >
                {skill}
              </span>
            ))}
            {candidate.topSkills.length > 5 && (
              <span className="px-1.5 py-0.5 text-[10px] font-medium rounded-md bg-slate-100 text-slate-500">
                +{candidate.topSkills.length - 5}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Footer Action */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-semibold text-indigo-600 group-hover:text-indigo-700">
        <span>View Full Profile</span>
        <ChevronRight className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" />
      </div>
    </div>
  );
};
