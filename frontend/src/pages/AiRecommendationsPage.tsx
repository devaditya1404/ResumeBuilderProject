import React, { useState, useEffect } from 'react';
import { Sparkles, CheckCircle2, XCircle, AlertTriangle, ArrowRight, RefreshCw, X, Check } from 'lucide-react';
import { Candidate, Requirement } from '../types';
import { api } from '../api/client';

interface AiRecommendationsPageProps {
  candidates: Candidate[];
  requirements: Requirement[];
  selectedRequirementId: string;
  onSelectRequirementId: (id: string) => void;
  onSelectCandidate: (candidate: Candidate) => void;
}

export const AiRecommendationsPage: React.FC<AiRecommendationsPageProps> = ({
  candidates,
  requirements,
  selectedRequirementId,
  onSelectRequirementId,
  onSelectCandidate,
}) => {
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [matchingInProgress, setMatchingInProgress] = useState<boolean>(false);
  const [selectedMatchDetail, setSelectedMatchDetail] = useState<any | null>(null);

  const currentRequirement = requirements.find((r) => r.id === selectedRequirementId) || requirements[0];

  useEffect(() => {
    if (currentRequirement?.id) {
      loadRequirementMatches(currentRequirement.id);
    }
  }, [currentRequirement?.id]);

  const loadRequirementMatches = async (reqId: string) => {
    setLoading(true);
    console.log('Selected Requirement ID:', reqId);
    console.log('Selected Requirement Title:', currentRequirement?.title);
    console.log('Candidates in Talent Vault:', candidates.length);
    try {
      const data = await api.getRequirementMatches(reqId);
      console.log('Existing MatchResults:', data ? data.length : 0);
      console.log('Matches returned:', data);
      console.log('Candidate scores:', data ? data.map(d => `${d.candidate_name}: ${d.overall_score}%`) : []);

      if (data && data.length >= candidates.length && candidates.length > 0) {
        setMatches(data);
      } else {
        console.log('Matching triggered: YES');
        await runMatching(reqId);
      }
    } catch (err) {
      console.error('Failed to load requirement matches:', err);
    } finally {
      setLoading(false);
    }
  };

  const runMatching = async (reqId: string) => {
    setMatchingInProgress(true);
    try {
      await api.matchRequirement(reqId);
      const data = await api.getRequirementMatches(reqId);
      setMatches(data || []);
    } catch (err) {
      console.error('Failed to run requirement matching:', err);
    } finally {
      setMatchingInProgress(false);
    }
  };

  // Sort matches by overall_score descending (NO FAKE 70% FALLBACKS!)
  const rankedMatches = [...matches].sort((a, b) => (b.overall_score ?? -1) - (a.overall_score ?? -1));

  const formatScore = (val: number | null | undefined): string => {
    if (val === null || val === undefined) return 'N/A';
    return `${Math.round(val)}%`;
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header & Selector Banner */}
      <div className="bg-gradient-to-br from-indigo-900 via-purple-950 to-slate-900 rounded-2xl p-6 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h2 className="text-2xl font-black tracking-tight">AI Talent Intelligence & Matching</h2>
          </div>
          <p className="text-xs text-indigo-200 mt-1">
            Grounded deterministic scoring & candidate evaluation against job criteria.
          </p>
        </div>

        {/* Requirement Switcher */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => currentRequirement?.id && runMatching(currentRequirement.id)}
            disabled={matchingInProgress}
            className="flex items-center gap-1.5 px-3 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-bold rounded-xl transition-colors cursor-pointer"
            title="Recalculate match scores"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${matchingInProgress ? 'animate-spin' : ''}`} />
            <span>{matchingInProgress ? 'Matching...' : 'Re-Run Match'}</span>
          </button>

          <div className="bg-white/10 p-2.5 rounded-xl border border-white/15 backdrop-blur-xs space-y-1">
            <label className="text-[10px] uppercase font-extrabold text-indigo-300 block">
              Active Job Requirement:
            </label>
            <select
              value={currentRequirement?.id || ''}
              onChange={(e) => onSelectRequirementId(e.target.value)}
              className="w-full bg-slate-900 text-white text-xs font-bold rounded-lg px-3 py-1.5 focus:outline-none cursor-pointer border border-slate-700"
            >
              {requirements.map((req) => (
                <option key={req.id} value={req.id}>
                  {req.title}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Selected Job Requirement Summary Card */}
      {currentRequirement && (
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-2xs space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-extrabold text-slate-900 text-base">
              Target Opening: <span className="text-indigo-600">{currentRequirement.title}</span>
            </h3>
            <span className="px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold border border-indigo-200">
              Min {currentRequirement.minExperienceYears}+ Years Experience
            </span>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed">{currentRequirement.description}</p>
          
          <div className="flex flex-wrap items-center gap-2 text-xs pt-1">
            <span className="font-bold text-slate-400 uppercase text-[10px]">Required Skills:</span>
            {currentRequirement.requiredSkills && currentRequirement.requiredSkills.length > 0 ? (
              currentRequirement.requiredSkills.map((s, i) => (
                <span key={i} className="px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 font-semibold text-[11px] border border-indigo-200">
                  {s}
                </span>
              ))
            ) : (
              <span className="text-amber-600 italic text-xs">No structured skills extracted for this requirement yet.</span>
            )}
          </div>
        </div>
      )}

      {/* Ranked Candidate List */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-slate-900 flex items-center justify-between px-1">
          <span>Ranked Candidates ({rankedMatches.length})</span>
          <span className="text-xs text-slate-400 font-normal">Sorted Highest Match Score → Lowest Match Score</span>
        </h3>

        {loading ? (
          <div className="p-12 text-center text-slate-500 bg-white rounded-2xl border border-slate-200 space-y-2">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-indigo-600" />
            <p className="text-sm font-bold">Calculating Candidate Matches...</p>
          </div>
        ) : rankedMatches.length === 0 ? (
          <div className="p-12 text-center text-slate-500 bg-white rounded-2xl border border-slate-200">
            <p className="text-sm font-bold">No candidates found to match for this requirement.</p>
          </div>
        ) : (
          rankedMatches.map((m, index) => {
            const matchedSkills: string[] = m.matching_skills || [];
            const missingMandatory: string[] = m.missing_mandatory_skills || [];
            const missingPreferred: string[] = m.missing_preferred_skills || [];

            return (
              <div
                key={m.id || m.candidate_id || index}
                className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-2xs hover:border-indigo-300 transition-all space-y-4 group"
              >
                {/* Card Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-white font-extrabold flex items-center justify-center text-lg shadow-md">
                        {(m.candidate_name || 'C').charAt(0)}
                      </div>
                      <span className="absolute -top-1 -left-1 w-5 h-5 rounded-full bg-slate-900 text-white text-[10px] font-bold flex items-center justify-center border border-white">
                        #{index + 1}
                      </span>
                    </div>

                    <div>
                      <h4 className="font-bold text-slate-900 text-base group-hover:text-indigo-600 transition-colors">
                        {m.candidate_name}
                      </h4>
                      <p className="text-xs text-indigo-600 font-semibold">
                        {m.current_designation || 'Candidate'} • {m.experience_years ? `${m.experience_years} Years` : 'Experience N/A'}
                      </p>
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Company: <span className="font-medium text-slate-800">{m.current_company || 'N/A'}</span>
                        {m.location && ` • Location: ${m.location}`}
                      </p>
                    </div>
                  </div>

                  {/* Score & View Details Button */}
                  <div className="flex items-center gap-4 self-end md:self-center">
                    <div className="flex items-center gap-3 bg-slate-50 px-4 py-2.5 rounded-xl border border-slate-200">
                      <div className="text-right">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">Overall Score</span>
                        <span className="text-xl font-black text-indigo-600">
                          {m.overall_score !== null && m.overall_score !== undefined ? `${Math.round(m.overall_score)}%` : 'Not Scored'}
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => setSelectedMatchDetail(m)}
                      className="flex items-center gap-1.5 px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-xs transition-colors shrink-0 cursor-pointer"
                    >
                      <span>View Details</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>

                {/* Dynamic Skill Badges */}
                <div className="space-y-2">
                  <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider">
                    Requirement Badges (Matched vs Missing JD Skills):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {/* GREEN Badges = Matched JD requirements */}
                    {matchedSkills.map((s, i) => (
                      <span
                        key={`matched-${i}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                        {s}
                      </span>
                    ))}

                    {/* RED Badges = Missing JD requirements */}
                    {missingMandatory.map((s, i) => (
                      <span
                        key={`missing-m-${i}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200"
                      >
                        <XCircle className="w-3.5 h-3.5 text-rose-600" />
                        {s} (Missing)
                      </span>
                    ))}

                    {missingPreferred.map((s, i) => (
                      <span
                        key={`missing-p-${i}`}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200"
                      >
                        <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                        {s} (Preferred)
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* VIEW DETAILS MODAL — Resume Match Report */}
      {selectedMatchDetail && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 z-50 animate-fade-in">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200 p-6 space-y-6">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-slate-100 pb-4">
              <div>
                <h3 className="text-xl font-black text-slate-900">Resume Match Report</h3>
                <p className="text-xs text-indigo-600 font-semibold mt-0.5">
                  Candidate: {selectedMatchDetail.candidate_name} • Opening: {currentRequirement?.title}
                </p>
              </div>
              <button
                onClick={() => setSelectedMatchDetail(null)}
                className="p-2 text-slate-400 hover:text-slate-600 rounded-full hover:bg-slate-100 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Overall Score Box */}
            <div className="bg-gradient-to-br from-indigo-900 to-slate-900 rounded-xl p-5 text-white flex items-center justify-between">
              <div>
                <span className="text-[10px] uppercase font-bold text-indigo-300 block">Overall Match Score</span>
                <span className="text-3xl font-black text-white">
                  {formatScore(selectedMatchDetail.overall_score)}
                </span>
              </div>
              <div className="text-right text-xs text-indigo-200 space-y-1">
                <p>Skill Match: <span className="font-bold text-white">{formatScore(selectedMatchDetail.skill_score)}</span></p>
                <p>Experience: <span className="font-bold text-white">{formatScore(selectedMatchDetail.experience_score)}</span></p>
              </div>
            </div>

            {/* Strengths */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
                <Check className="w-4 h-4 text-emerald-600" />
                Strengths
              </h4>
              <div className="p-3.5 rounded-xl bg-emerald-50/60 border border-emerald-200 text-xs text-emerald-950 space-y-1.5">
                {selectedMatchDetail.strengths && selectedMatchDetail.strengths.length > 0 ? (
                  selectedMatchDetail.strengths.map((str: string, i: number) => (
                    <p key={i} className="flex items-start gap-2">
                      <span className="text-emerald-600 font-bold">✔</span>
                      <span>{str}</span>
                    </p>
                  ))
                ) : (
                  <p className="text-slate-500 italic">No specific strengths matched for this candidate.</p>
                )}
              </div>
            </div>

            {/* Missing Requirements */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-rose-800 flex items-center gap-1.5">
                <X className="w-4 h-4 text-rose-600" />
                Missing Requirements
              </h4>
              <div className="p-3.5 rounded-xl bg-rose-50/60 border border-rose-200 text-xs text-rose-950 space-y-1.5">
                {[...(selectedMatchDetail.missing_mandatory_skills || []), ...(selectedMatchDetail.missing_preferred_skills || [])].length > 0 ? (
                  [...(selectedMatchDetail.missing_mandatory_skills || []), ...(selectedMatchDetail.missing_preferred_skills || [])].map((m: string, i: number) => (
                    <p key={i} className="flex items-start gap-2">
                      <span className="text-rose-600 font-bold">✖</span>
                      <span>{m}</span>
                    </p>
                  ))
                ) : (currentRequirement?.requiredSkills && currentRequirement.requiredSkills.length > 0) ? (
                  <p className="text-slate-500 italic">No missing skills detected against this Job Description.</p>
                ) : (
                  <p className="text-amber-700 italic">JD skills have not been extracted. Reprocess the requirement.</p>
                )}
              </div>
            </div>

            {/* Resume Improvements */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-indigo-900 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                Resume Improvements
              </h4>
              <div className="p-3.5 rounded-xl bg-indigo-50/60 border border-indigo-200 text-xs text-indigo-950 space-y-1.5">
                {selectedMatchDetail.gaps && selectedMatchDetail.gaps.length > 0 ? (
                  selectedMatchDetail.gaps.map((tip: string, i: number) => (
                    <p key={i} className="flex items-start gap-2">
                      <span className="text-indigo-600 font-bold">•</span>
                      <span>{tip}</span>
                    </p>
                  ))
                ) : (
                  <p className="text-slate-500 italic">No specific resume improvement tips recorded.</p>
                )}
              </div>
            </div>

            {/* Score Breakdown Table */}
            <div className="space-y-2 border-t border-slate-100 pt-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">Score Breakdown</h4>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-center">
                  <span className="text-[10px] text-slate-400 font-bold block">Skills</span>
                  <span className="font-extrabold text-slate-900 text-sm">{formatScore(selectedMatchDetail.skill_score)}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-center">
                  <span className="text-[10px] text-slate-400 font-bold block">Experience</span>
                  <span className="font-extrabold text-slate-900 text-sm">{formatScore(selectedMatchDetail.experience_score)}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-center">
                  <span className="text-[10px] text-slate-400 font-bold block">Role</span>
                  <span className="font-extrabold text-slate-900 text-sm">{formatScore(selectedMatchDetail.role_score)}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-center">
                  <span className="text-[10px] text-slate-400 font-bold block">Education</span>
                  <span className="font-extrabold text-slate-900 text-sm">{formatScore(selectedMatchDetail.education_score)}</span>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-center">
                  <span className="text-[10px] text-slate-400 font-bold block">Location</span>
                  <span className="font-extrabold text-slate-900 text-sm">{formatScore(selectedMatchDetail.location_score)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
