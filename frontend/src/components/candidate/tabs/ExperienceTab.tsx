import React from 'react';
import { Building2, Calendar, Users2, CheckCircle2 } from 'lucide-react';
import { Candidate } from '../../../types';

interface ExperienceTabProps {
  candidate: Candidate;
}

export const ExperienceTab: React.FC<ExperienceTabProps> = ({ candidate }) => {
  return (
    <div className="space-y-6">
      {/* Experience Summary Header */}
      <div className="p-3.5 rounded-xl bg-indigo-50/60 border border-indigo-100 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-500">Total Calculated Experience</p>
          <p className="text-sm font-bold text-indigo-900">{candidate.experienceDisplay}</p>
        </div>
        <div className="text-right">
          <p className="text-[10px] font-bold uppercase tracking-wider text-indigo-500">Employment Entries</p>
          <p className="text-sm font-bold text-indigo-900">{candidate.experiences.length} Positions Recorded</p>
        </div>
      </div>

      {/* Complete Employment History Timeline */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-slate-200">
        {candidate.experiences.map((exp) => (
          <div key={exp.id} className="relative group">
            {/* Timeline node */}
            <div className="absolute -left-[23px] top-1.5 w-4 h-4 rounded-full bg-white border-2 border-indigo-600 group-hover:bg-indigo-600 transition-colors shadow-2xs" />

            <div className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-xs hover:border-slate-300 transition-all space-y-3">
              {/* Designation & Employer */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 border-b border-slate-100 pb-3">
                <div>
                  <h4 className="font-bold text-slate-900 text-base flex items-center gap-2">
                    {exp.designation}
                    {exp.isCurrent && (
                      <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-emerald-100 text-emerald-800 border border-emerald-200">
                        Current Employer
                      </span>
                    )}
                  </h4>
                  <p className="text-xs font-semibold text-indigo-600 flex items-center gap-1.5 mt-0.5">
                    <Building2 className="w-3.5 h-3.5 text-indigo-500" />
                    {exp.company}
                  </p>
                </div>

                <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium bg-slate-50 px-2.5 py-1 rounded-md border border-slate-100 self-start sm:self-auto">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>{exp.startDate} - {exp.endDate}</span>
                  <span className="font-semibold text-slate-700">({exp.durationDisplay})</span>
                </div>
              </div>

              {/* Responsibilities list */}
              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
                  Key Responsibilities & Deliverables
                </p>
                <ul className="space-y-1.5">
                  {exp.responsibilities.map((resp, i) => (
                    <li key={i} className="text-xs text-slate-700 flex items-start gap-2 leading-relaxed">
                      <CheckCircle2 className="w-3.5 h-3.5 text-indigo-500 shrink-0 mt-0.5" />
                      <span>{resp}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* CLIENTS section - Enforcing EMPLOYER != CLIENT distinction */}
              {exp.clients && exp.clients.length > 0 && (
                <div className="mt-3 pt-3 border-t border-slate-100 bg-amber-50/50 -mx-5 -mb-5 p-4 rounded-b-xl border-t-amber-100">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <Users2 className="w-3.5 h-3.5 text-amber-700" />
                    <span className="text-[11px] font-bold uppercase tracking-wider text-amber-800">
                      Assigned Clients / Projects
                    </span>
                    <span className="text-[10px] text-amber-600 font-medium">(Employer: {exp.company})</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {exp.clients.map((client, cIdx) => (
                      <span
                        key={cIdx}
                        className="px-2.5 py-1 text-xs font-semibold rounded-md bg-amber-100 text-amber-900 border border-amber-200"
                      >
                        {client}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
