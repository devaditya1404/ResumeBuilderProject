import React, { useState, useMemo } from 'react';
import { Search, Filter, X, Briefcase, RefreshCw, Users, Trash2 } from 'lucide-react';
import type { Candidate, Requirement } from '../types';
import { CandidateCard } from '../components/candidate/CandidateCard';

interface TalentVaultPageProps {
  candidates: Candidate[];
  requirements: Requirement[];
  loading?: boolean;
  onSelectCandidate: (candidate: Candidate) => void;
  onDeleteCandidate?: (candidateId: string) => Promise<void>;
  selectedRequirementId: string;
  onSelectRequirementId: (id: string) => void;
}

export const TalentVaultPage: React.FC<TalentVaultPageProps> = ({
  candidates,
  requirements,
  loading = false,
  onSelectCandidate,
  onDeleteCandidate,
  selectedRequirementId,
  onSelectRequirementId,
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSkill, setSelectedSkill] = useState('');
  const [selectedLocation, setSelectedLocation] = useState('');
  const [minExpYears, setMinExpYears] = useState<number>(0);
  const [selectedNotice, setSelectedNotice] = useState('');

  // Delete modal state
  const [candidateToDelete, setCandidateToDelete] = useState<Candidate | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Extract unique skills & locations
  const allSkills = useMemo(() => {
    const set = new Set<string>();
    candidates.forEach((c) => c.topSkills.forEach((s) => set.add(s)));
    return Array.from(set).sort();
  }, [candidates]);

  const allLocations = useMemo(() => {
    const set = new Set<string>();
    candidates.forEach((c) => {
      if (c.location) set.add(c.location.split(',')[0].trim());
    });
    return Array.from(set).sort();
  }, [candidates]);

  // Filtered candidate list computation
  const filteredCandidates = useMemo(() => {
    return candidates.filter((c) => {
      if (searchTerm.trim()) {
        const q = searchTerm.toLowerCase();
        const matchesName = c.name.toLowerCase().includes(q);
        const matchesDesig = c.designation.toLowerCase().includes(q);
        const matchesCompany = (c.currentCompany || c.latestCompany || '').toLowerCase().includes(q);
        const matchesSkill = c.topSkills.some((s) => s.toLowerCase().includes(q));
        if (!matchesName && !matchesDesig && !matchesCompany && !matchesSkill) return false;
      }

      if (selectedSkill && !c.topSkills.includes(selectedSkill)) {
        return false;
      }

      if (selectedLocation && !c.location?.toLowerCase().includes(selectedLocation.toLowerCase())) {
        return false;
      }

      if (minExpYears > 0 && (c.experienceYears || 0) < minExpYears) {
        return false;
      }

      if (selectedNotice) {
        if (!c.noticePeriod || !c.noticePeriod.toLowerCase().includes(selectedNotice.toLowerCase())) {
          return false;
        }
      }

      return true;
    });
  }, [candidates, searchTerm, selectedSkill, selectedLocation, minExpYears, selectedNotice]);

  const handleConfirmDelete = async () => {
    if (!candidateToDelete || !onDeleteCandidate) return;
    setIsDeleting(true);
    const cName = candidateToDelete.name;
    try {
      await onDeleteCandidate(candidateToDelete.id);
      setToastMessage(`${cName} deleted successfully.`);
      setTimeout(() => setToastMessage(null), 4000);
      setCandidateToDelete(null);
    } catch (err) {
      console.error('Failed to delete candidate:', err);
      setToastMessage(`Unable to delete candidate. Please try again.`);
      setTimeout(() => setToastMessage(null), 4000);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white text-xs font-bold px-4 py-3 rounded-xl shadow-xl flex items-center gap-2 animate-fade-in border border-slate-700">
          <span>{toastMessage}</span>
          <button onClick={() => setToastMessage(null)} className="text-slate-400 hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-6 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Users className="w-5 h-5 text-indigo-600" />
            Talent Vault Document Store
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Search, filter, and score candidate resumes stored locally in SQLite database.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
            Showing {filteredCandidates.length} of {candidates.length} Candidate Profiles
          </span>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="bg-white rounded-xl border border-slate-200/90 p-4 shadow-2xs space-y-3">
        <div className="flex flex-col md:flex-row items-center gap-3">
          {/* Search Input */}
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search candidate name, job title, employer, skill..."
              className="w-full text-xs pl-9 pr-8 py-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50/50"
            />
            {searchTerm && (
              <button
                onClick={() => setSearchTerm('')}
                className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Skill Filter Dropdown */}
          <div className="w-full md:w-48">
            <select
              value={selectedSkill}
              onChange={(e) => setSelectedSkill(e.target.value)}
              className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50/50 cursor-pointer font-medium"
            >
              <option value="">All Skills</option>
              {allSkills.map((sk) => (
                <option key={sk} value={sk}>
                  {sk}
                </option>
              ))}
            </select>
          </div>

          {/* Location Filter Dropdown */}
          <div className="w-full md:w-44">
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50/50 cursor-pointer font-medium"
            >
              <option value="">All Locations</option>
              {allLocations.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Candidates Grid */}
      {filteredCandidates.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center space-y-3">
          <Users className="w-10 h-10 text-slate-300 mx-auto" />
          <h3 className="text-base font-bold text-slate-800">No candidate profiles found</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Try adjusting your search query or filter parameters to find candidate profiles.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredCandidates.map((candidate) => (
            <CandidateCard
              key={candidate.id}
              candidate={candidate}
              onSelect={onSelectCandidate}
              onDelete={(c) => setCandidateToDelete(c)}
              selectedRequirementId={selectedRequirementId}
            />
          ))}
        </div>
      )}

      {/* Confirmation Modal before Deletion */}
      {candidateToDelete && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 animate-fade-in">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl border border-slate-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center shrink-0">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Delete Candidate?</h3>
                <p className="text-xs text-slate-500 font-medium">Permanent deletion from Talent Vault</p>
              </div>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Are you sure you want to permanently delete <strong className="text-slate-900 font-bold">"{candidateToDelete.name}"</strong> from Talent Vault?
              This will also remove the candidate's resume data, skills, experience and existing match results.
            </p>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                disabled={isDeleting}
                onClick={() => setCandidateToDelete(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg cursor-pointer disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isDeleting}
                onClick={handleConfirmDelete}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 disabled:opacity-50 text-white text-xs font-bold rounded-lg flex items-center gap-1.5 shadow-xs cursor-pointer"
              >
                {isDeleting ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Deleting...</span>
                  </>
                ) : (
                  <>
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete Candidate</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
