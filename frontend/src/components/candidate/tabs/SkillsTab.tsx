import React from 'react';
import { Tag, Sparkles, Check } from 'lucide-react';
import { Candidate } from '../../../types';

interface SkillsTabProps {
  candidate: Candidate;
}

export const SkillsTab: React.FC<SkillsTabProps> = ({ candidate }) => {
  return (
    <div className="space-y-6">
      {/* Top skills summary banner */}
      <div className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-2xs space-y-2">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-indigo-600" />
          Extracted Core Competencies
        </h4>
        <div className="flex flex-wrap gap-1.5">
          {candidate.topSkills.map((skill, idx) => (
            <span
              key={idx}
              className="px-3 py-1 rounded-lg text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1.5"
            >
              <Check className="w-3 h-3 text-indigo-500" />
              {skill}
            </span>
          ))}
        </div>
      </div>

      {/* Categorized Skills Breakdown */}
      <div className="space-y-4">
        {candidate.categorizedSkills.map((cat, idx) => (
          <div key={idx} className="p-4 rounded-xl bg-white border border-slate-200/80 shadow-2xs space-y-3">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
              <Tag className="w-4 h-4 text-purple-600" />
              <h5 className="text-xs font-bold text-slate-800 uppercase tracking-wider">{cat.category}</h5>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 font-semibold text-slate-500">
                {cat.skills.length} skills
              </span>
            </div>
            <div className="flex flex-wrap gap-2">
              {cat.skills.map((skill, sIdx) => (
                <span
                  key={sIdx}
                  className="px-2.5 py-1 text-xs font-medium rounded-md bg-slate-50 text-slate-700 border border-slate-200 hover:border-indigo-300 transition-colors"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Grounding note */}
      <p className="text-[11px] text-slate-400 italic text-center">
        * Skill names normalized (e.g., MS Power BI → Power BI). Skills extracted only from resume body.
      </p>
    </div>
  );
};
