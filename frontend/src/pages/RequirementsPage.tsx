import React, { useState } from 'react';
import { Briefcase, Plus, Sparkles, FileText, MapPin, Award, Check } from 'lucide-react';
import type { Requirement } from '../types';

interface RequirementsPageProps {
  requirements: Requirement[];
  loading?: boolean;
  onCreateRequirement?: (req: Partial<Requirement>) => void;
  onSelectRequirement?: (id: string) => void;
  onNavigateToRecommendations?: () => void;
}

export const RequirementsPage: React.FC<RequirementsPageProps> = ({
  requirements,
  loading = false,
  onCreateRequirement,
  onSelectRequirement,
  onNavigateToRecommendations,
}) => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showJdParserModal, setShowJdParserModal] = useState(false);
  const [pastedJdText, setPastedJdText] = useState('');
  const [isExtracting, setIsExtracting] = useState(false);

  // New Requirement form state
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');
  const [requiredSkillsStr, setRequiredSkillsStr] = useState('');
  const [preferredSkillsStr, setPreferredSkillsStr] = useState('');
  const [minExp, setMinExp] = useState(2);
  const [location, setLocation] = useState('Mumbai / Hybrid');

  const handleCreateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    const reqSkills = requiredSkillsStr.split(',').map(s => s.trim()).filter(Boolean);
    const prefSkills = preferredSkillsStr.split(',').map(s => s.trim()).filter(Boolean);

    if (onCreateRequirement) {
      onCreateRequirement({
        title,
        description: desc,
        requiredSkills: reqSkills,
        preferredSkills: prefSkills,
        minExperienceYears: minExp,
        location,
        employmentType: 'Full-time'
      });
    }

    setShowCreateModal(false);
    setTitle('');
    setDesc('');
    setRequiredSkillsStr('');
    setPreferredSkillsStr('');
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-2xs flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Briefcase className="w-5 h-5 text-indigo-600" />
            Job Requirements & Openings
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Manage target job profiles and run candidate matching criteria.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowJdParserModal(true)}
            className="flex items-center gap-2 py-2 px-3.5 rounded-lg bg-purple-50 text-purple-700 hover:bg-purple-100 font-bold text-xs border border-purple-200 transition-colors"
          >
            <Sparkles className="w-4 h-4 text-purple-600" />
            Paste JD & Auto-Extract
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 py-2 px-4 rounded-lg bg-indigo-600 text-white font-bold text-xs hover:bg-indigo-700 shadow-xs transition-colors"
          >
            <Plus className="w-4 h-4" />
            Create Requirement
          </button>
        </div>
      </div>

      {/* Requirements List Grid / Empty state */}
      {requirements.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center space-y-3">
          <Briefcase className="w-10 h-10 text-slate-300 mx-auto" />
          <h3 className="text-base font-bold text-slate-800">No job requirements created yet</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Create your first requirement above to start comparing and scoring candidate profiles.
          </p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-indigo-600 text-white font-bold text-xs rounded-lg hover:bg-indigo-700 shadow-xs"
          >
            + Create First Requirement
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {requirements.map((req) => (
            <div
              key={req.id}
              className="bg-white rounded-xl border border-slate-200/90 p-5 shadow-2xs hover:shadow-md transition-shadow flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-bold text-slate-900 text-base leading-snug">{req.title}</h3>
                  <span className="px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 font-extrabold text-xs shrink-0 border border-indigo-100">
                    {req.activeCandidateMatchesCount} Candidates
                  </span>
                </div>

                <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">{req.description}</p>

                <div className="space-y-2 pt-2 border-t border-slate-100 text-xs">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                      Mandatory Required Skills
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {req.requiredSkills.map((s, i) => (
                        <span key={i} className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200">
                          {s}
                        </span>
                      ))}
                    </div>
                  </div>

                  {req.preferredSkills.length > 0 && (
                    <div>
                      <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                        Preferred Skills
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {req.preferredSkills.map((s, i) => (
                          <span key={i} className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-2 gap-2 text-slate-500 pt-2 text-[11px] font-medium">
                    <div className="flex items-center gap-1">
                      <Award className="w-3.5 h-3.5 text-indigo-500" />
                      <span>Min Exp: {req.minExperienceYears}+ Yrs</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span className="truncate">{req.location}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-[10px] text-slate-400 font-mono">Created {req.createdAt}</span>
                <span
                  onClick={() => {
                    console.log('Selected Requirement ID:', req.id);
                    console.log('Selected Requirement Title:', req.title);
                    if (onSelectRequirement) onSelectRequirement(req.id);
                    if (onNavigateToRecommendations) onNavigateToRecommendations();
                  }}
                  className="font-semibold text-indigo-600 hover:underline cursor-pointer"
                >
                  View Matched Candidates →
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Requirement Modal Form */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <FileText className="w-5 h-5 text-indigo-600" />
              Create Job Requirement
            </h3>

            <form onSubmit={handleCreateSubmit} className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Job Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Senior PMO Executive"
                  className="w-full p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Job Description</label>
                <textarea
                  rows={3}
                  required
                  value={desc}
                  onChange={(e) => setDesc(e.target.value)}
                  placeholder="Brief role summary..."
                  className="w-full p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Required Skills (Comma separated)</label>
                  <input
                    type="text"
                    value={requiredSkillsStr}
                    onChange={(e) => setRequiredSkillsStr(e.target.value)}
                    placeholder="PMO, Power BI, SQL"
                    className="w-full p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Preferred Skills</label>
                  <input
                    type="text"
                    value={preferredSkillsStr}
                    onChange={(e) => setPreferredSkillsStr(e.target.value)}
                    placeholder="Jira, Python"
                    className="w-full p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Minimum Experience (Years)</label>
                  <input
                    type="number"
                    value={minExp}
                    onChange={(e) => setMinExp(Number(e.target.value))}
                    className="w-full p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Location</label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full p-2.5 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-lg flex items-center gap-1 shadow-xs"
                >
                  <Check className="w-4 h-4" /> Save Requirement
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
