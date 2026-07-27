import React from 'react';
import { Cpu, CheckCircle, Target, TrendingUp, AlertTriangle } from 'lucide-react';
import { Candidate } from '../../../types';

interface AiInsightsTabProps {
  candidate: Candidate;
  selectedRequirementTitle?: string;
}

export const AiInsightsTab: React.FC<AiInsightsTabProps> = ({ candidate, selectedRequirementTitle }) => {
  const { aiInsights, matchBreakdown } = candidate;

  return (
    <div className="space-y-5">
      {/* AI Grounding Header */}
      <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 to-indigo-950 text-white shadow-md space-y-1">
        <div className="flex items-center gap-2">
          <Cpu className="w-4 h-4 text-indigo-400" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-200">
            Local Ollama Intelligence Summary
          </h4>
        </div>
        <p className="text-xs text-slate-300">
          Strictly grounded analysis extracted from original resume text. Zero external API calls.
        </p>
      </div>

      {/* Requirement Match Gap Analysis if matched */}
      {selectedRequirementTitle && matchBreakdown && (
        <div className="p-4 rounded-xl bg-indigo-50/80 border border-indigo-200 space-y-3">
          <div className="flex items-center justify-between">
            <h5 className="text-xs font-bold text-indigo-900 uppercase tracking-wider flex items-center gap-1.5">
              <Target className="w-4 h-4 text-indigo-600" />
              Skill Gap & Match Analysis vs "{selectedRequirementTitle}"
            </h5>
            <span className="px-2.5 py-0.5 rounded-full bg-indigo-600 text-white font-bold text-xs">
              {matchBreakdown.overall}% Overall
            </span>
          </div>

          <p className="text-xs text-slate-700 leading-relaxed font-normal">
            {matchBreakdown.explanation}
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
            <div className="p-3 rounded-lg bg-white border border-indigo-100 space-y-1">
              <p className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1">
                <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                Matching Mandatory Skills ({matchBreakdown.matchingSkills.length})
              </p>
              <div className="flex flex-wrap gap-1">
                {matchBreakdown.matchingSkills.map((s, idx) => (
                  <span key={idx} className="px-2 py-0.5 text-[10px] font-semibold bg-emerald-50 text-emerald-800 rounded">
                    {s}
                  </span>
                ))}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-white border border-indigo-100 space-y-1">
              <p className="text-[10px] font-bold uppercase tracking-wider text-amber-700 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                Missing / Unverified Skills
              </p>
              <div className="flex flex-wrap gap-1">
                {matchBreakdown.missingPreferredSkills.length > 0 ? (
                  matchBreakdown.missingPreferredSkills.map((s, idx) => (
                    <span key={idx} className="px-2 py-0.5 text-[10px] font-semibold bg-amber-50 text-amber-800 rounded">
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-[11px] text-emerald-700 italic">All skills verified</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Candidate Strengths */}
      <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-2xs space-y-2">
        <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          Verified Strengths
        </h5>
        <ul className="space-y-1.5">
          {aiInsights.strengths.map((str, i) => (
            <li key={i} className="text-xs text-slate-700 flex items-start gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
              <span>{str}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Potential Roles */}
      <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-2xs space-y-2">
        <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
          <Target className="w-4 h-4 text-indigo-600" />
          Best-Fit Recommended Roles
        </h5>
        <div className="flex flex-wrap gap-2">
          {aiInsights.potentialRoles.map((role, rIdx) => (
            <span
              key={rIdx}
              className="px-3 py-1 text-xs font-semibold rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200"
            >
              {role}
            </span>
          ))}
        </div>
      </div>

      {/* Career Progression Analysis */}
      <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-2xs space-y-2">
        <h5 className="text-xs font-bold text-slate-900 uppercase tracking-wider flex items-center gap-1.5">
          <TrendingUp className="w-4 h-4 text-purple-600" />
          Career Progression Analysis
        </h5>
        <p className="text-xs text-slate-700 leading-relaxed font-normal">
          {aiInsights.careerProgression}
        </p>
      </div>
    </div>
  );
};
