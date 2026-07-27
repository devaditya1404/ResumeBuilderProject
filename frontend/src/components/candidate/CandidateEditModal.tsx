import React, { useState } from 'react';
import { X, Plus, Trash2, Save, RefreshCw, Briefcase, User, Tag, Award, GraduationCap, FolderGit2 } from 'lucide-react';
import type { Candidate } from '../../types';

interface CandidateEditModalProps {
  candidate: Candidate;
  onClose: () => void;
  onSave: (candidateId: string, updatedData: any) => Promise<void>;
}

export const CandidateEditModal: React.FC<CandidateEditModalProps> = ({
  candidate,
  onClose,
  onSave,
}) => {
  // Form State initialized from candidate defaults
  const [name, setName] = useState(candidate.name || '');
  const [email, setEmail] = useState(candidate.email || '');
  const [phone, setPhone] = useState(candidate.phone || '');
  const [location, setLocation] = useState(candidate.location || '');
  const [preferredLocation, setPreferredLocation] = useState(candidate.preferredLocation || '');
  const [linkedinUrl, setLinkedinUrl] = useState(candidate.linkedinUrl || '');
  const [githubUrl, setGithubUrl] = useState(candidate.githubUrl || '');
  const [portfolioUrl, setPortfolioUrl] = useState(candidate.portfolioUrl || '');

  const [currentCompany, setCurrentCompany] = useState(candidate.currentCompany || '');
  const [currentDesignation, setCurrentDesignation] = useState(candidate.currentDesignation || '');
  const [latestCompany, setLatestCompany] = useState(candidate.latestCompany || '');
  const [latestDesignation, setLatestDesignation] = useState(candidate.latestDesignation || '');

  const [noticePeriod, setNoticePeriod] = useState(candidate.noticePeriod || '');
  const [expectedSalary, setExpectedSalary] = useState(candidate.expectedSalary || '');
  const [professionalSummary, setProfessionalSummary] = useState(candidate.summary || '');

  // Skills List
  const [skills, setSkills] = useState<string[]>([...candidate.topSkills]);
  const [newSkillInput, setNewSkillInput] = useState('');

  // Experience Records
  const [experiences, setExperiences] = useState(
    (candidate.experiences || []).map((exp) => ({
      company: exp.company || '',
      designation: exp.designation || '',
      start_date: exp.startDate || '',
      end_date: exp.endDate || '',
      is_current: exp.isCurrent || false,
      responsibilities: exp.responsibilities ? [...exp.responsibilities] : [],
    }))
  );

  // Education Records
  const [education, setEducation] = useState(
    (candidate.education || []).map((edu) => ({
      institution: edu.institution || '',
      degree: edu.degree || '',
      field: edu.field || '',
      start_date: edu.startDate || '',
      end_date: edu.endDate || '',
    }))
  );

  // Certification Records
  const [certifications, setCertifications] = useState(
    (candidate.certifications || []).map((cert: any) => ({
      name: typeof cert === 'string' ? cert : cert.name || '',
      issuer: typeof cert === 'string' ? '' : cert.issuer || '',
      issue_date: typeof cert === 'string' ? '' : cert.issueDate || '',
      expiry_date: typeof cert === 'string' ? '' : cert.expiryDate || '',
    }))
  );

  // Project Records
  const [projects, setProjects] = useState(
    (candidate.projects || []).map((proj) => ({
      name: proj.name || '',
      description: proj.description || '',
      technologies: proj.technologies ? [...proj.technologies] : [],
    }))
  );

  const [isSaving, setIsSaving] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Skill Add / Remove helpers
  const handleAddSkill = () => {
    const trimmed = newSkillInput.trim();
    if (!trimmed) return;
    if (!skills.some((s) => s.toLowerCase() === trimmed.toLowerCase())) {
      setSkills([...skills, trimmed]);
    }
    setNewSkillInput('');
  };

  const handleRemoveSkill = (index: number) => {
    setSkills(skills.filter((_, i) => i !== index));
  };

  // Experience handlers
  const handleAddExperience = () => {
    setExperiences([
      ...experiences,
      { company: '', designation: '', start_date: '', end_date: '', is_current: false, responsibilities: [] },
    ]);
  };

  const handleRemoveExperience = (index: number) => {
    setExperiences(experiences.filter((_, i) => i !== index));
  };

  // Education handlers
  const handleAddEducation = () => {
    setEducation([...education, { institution: '', degree: '', field: '', start_date: '', end_date: '' }]);
  };

  const handleRemoveEducation = (index: number) => {
    setEducation(education.filter((_, i) => i !== index));
  };

  // Certification handlers
  const handleAddCertification = () => {
    setCertifications([...certifications, { name: '', issuer: '', issue_date: '', expiry_date: '' }]);
  };

  const handleRemoveCertification = (index: number) => {
    setCertifications(certifications.filter((_, i) => i !== index));
  };

  // Save handler
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setIsSaving(true);

    const payload = {
      name: name.trim(),
      email: email.trim() || null,
      phone: phone.trim() || null,
      current_location: location.trim() || null,
      preferred_location: preferredLocation.trim() || null,
      linkedin_url: linkedinUrl.trim() || null,
      github_url: githubUrl.trim() || null,
      portfolio_url: portfolioUrl.trim() || null,

      current_company: currentCompany.trim() || null,
      current_designation: currentDesignation.trim() || null,
      latest_company: latestCompany.trim() || null,
      latest_designation: latestDesignation.trim() || null,

      notice_period: noticePeriod.trim() || null,
      expected_salary: expectedSalary.trim() || null,
      professional_summary: professionalSummary.trim() || null,

      skills: skills,
      experiences: experiences.map((exp) => ({
        company: exp.company.trim(),
        designation: exp.designation.trim(),
        start_date: exp.start_date.trim() || null,
        end_date: exp.end_date.trim() || null,
        is_current: exp.is_current,
        responsibilities: exp.responsibilities,
      })),
      education: education.map((edu) => ({
        institution: edu.institution.trim(),
        degree: edu.degree.trim(),
        field: edu.field.trim() || null,
        start_date: edu.start_date.trim() || null,
        end_date: edu.end_date.trim() || null,
      })),
      certifications: certifications.map((cert) => ({
        name: cert.name.trim(),
        issuer: cert.issuer.trim() || null,
        issue_date: cert.issue_date.trim() || null,
        expiry_date: cert.expiry_date.trim() || null,
      })),
      projects: projects.map((proj) => ({
        name: proj.name.trim(),
        description: proj.description.trim() || null,
        technologies: proj.technologies,
      })),
    };

    try {
      await onSave(candidate.id, payload);
      onClose();
    } catch (err) {
      console.error('Failed to update candidate profile:', err);
      setErrorMessage('Unable to update candidate profile. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/60 backdrop-blur-xs flex justify-end animate-fade-in select-text">
      <div className="w-full max-w-3xl bg-white h-full flex flex-col shadow-2xl border-l border-slate-200">
        
        {/* Header */}
        <div className="p-6 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <User className="w-5 h-5 text-indigo-400" />
              Edit Candidate Profile — {candidate.name}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Manually correct parsed candidate information, skills, and employment history.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSaving}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="bg-rose-50 border-b border-rose-200 text-rose-700 px-6 py-3 text-xs font-bold flex items-center justify-between">
            <span>{errorMessage}</span>
            <button onClick={() => setErrorMessage(null)} className="text-rose-500 hover:text-rose-800">
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Form Body */}
        <form onSubmit={handleSave} className="flex-1 overflow-y-auto p-6 space-y-8 text-xs text-slate-700">
          
          {/* Section 1: Basic Information */}
          <div className="space-y-4 bg-slate-50/50 p-4 rounded-xl border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2 border-b border-slate-200 pb-2">
              <User className="w-4 h-4 text-indigo-600" /> Basic & Contact Details
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Full Name *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Phone Number</label>
                <input
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Current Location</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">LinkedIn URL</label>
                <input
                  type="text"
                  value={linkedinUrl}
                  onChange={(e) => setLinkedinUrl(e.target.value)}
                  placeholder="https://linkedin.com/in/..."
                  className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">GitHub URL</label>
                <input
                  type="text"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  placeholder="https://github.com/..."
                  className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Current Company</label>
                <input
                  type="text"
                  value={currentCompany}
                  onChange={(e) => setCurrentCompany(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Current Designation</label>
                <input
                  type="text"
                  value={currentDesignation}
                  onChange={(e) => setCurrentDesignation(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Latest Company</label>
                <input
                  type="text"
                  value={latestCompany}
                  onChange={(e) => setLatestCompany(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Latest Designation</label>
                <input
                  type="text"
                  value={latestDesignation}
                  onChange={(e) => setLatestDesignation(e.target.value)}
                  className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>
            </div>

            <div>
              <label className="block font-semibold text-slate-700 mb-1">Professional Summary</label>
              <textarea
                rows={3}
                value={professionalSummary}
                onChange={(e) => setProfessionalSummary(e.target.value)}
                className="w-full p-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 bg-white"
              />
            </div>
          </div>

          {/* Section 2: Skills */}
          <div className="space-y-4 bg-slate-50/50 p-4 rounded-xl border border-slate-200">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2 border-b border-slate-200 pb-2">
              <Tag className="w-4 h-4 text-indigo-600" /> Skills Catalog
            </h3>

            <div className="flex flex-wrap gap-2 mb-3">
              {skills.map((skill, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg text-xs font-bold"
                >
                  <span>{skill}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveSkill(idx)}
                    className="text-indigo-400 hover:text-rose-600 ml-1"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <input
                type="text"
                value={newSkillInput}
                onChange={(e) => setNewSkillInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleAddSkill();
                  }
                }}
                placeholder="Type new skill (e.g. Power BI, SQL)..."
                className="flex-1 p-2.5 rounded-lg border border-slate-300 bg-white"
              />
              <button
                type="button"
                onClick={handleAddSkill}
                className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-lg flex items-center gap-1 shrink-0"
              >
                <Plus className="w-4 h-4" /> Add Skill
              </button>
            </div>
          </div>

          {/* Section 3: Employment History */}
          <div className="space-y-4 bg-slate-50/50 p-4 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-indigo-600" /> Employment History & Experience
              </h3>
              <button
                type="button"
                onClick={handleAddExperience}
                className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" /> Add Employment Record
              </button>
            </div>

            {experiences.map((exp, idx) => (
              <div key={idx} className="p-3 bg-white border border-slate-200 rounded-lg space-y-3 relative">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-700 text-xs">Role #{idx + 1}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveExperience(idx)}
                    className="text-rose-500 hover:text-rose-700 p-1"
                    title="Remove experience"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Company *</label>
                    <input
                      type="text"
                      required
                      value={exp.company}
                      onChange={(e) => {
                        const copy = [...experiences];
                        copy[idx].company = e.target.value;
                        setExperiences(copy);
                      }}
                      className="w-full p-2 rounded-md border border-slate-300"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Designation *</label>
                    <input
                      type="text"
                      required
                      value={exp.designation}
                      onChange={(e) => {
                        const copy = [...experiences];
                        copy[idx].designation = e.target.value;
                        setExperiences(copy);
                      }}
                      className="w-full p-2 rounded-md border border-slate-300"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Start Date</label>
                    <input
                      type="text"
                      placeholder="YYYY-MM or Month YYYY"
                      value={exp.start_date}
                      onChange={(e) => {
                        const copy = [...experiences];
                        copy[idx].start_date = e.target.value;
                        setExperiences(copy);
                      }}
                      className="w-full p-2 rounded-md border border-slate-300"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">End Date</label>
                    <input
                      type="text"
                      placeholder="YYYY-MM or Present"
                      disabled={exp.is_current}
                      value={exp.is_current ? 'Present' : exp.end_date}
                      onChange={(e) => {
                        const copy = [...experiences];
                        copy[idx].end_date = e.target.value;
                        setExperiences(copy);
                      }}
                      className="w-full p-2 rounded-md border border-slate-300 disabled:bg-slate-100"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id={`current-${idx}`}
                    checked={exp.is_current}
                    onChange={(e) => {
                      const copy = [...experiences];
                      copy[idx].is_current = e.target.checked;
                      if (e.target.checked) copy[idx].end_date = 'Present';
                      setExperiences(copy);
                    }}
                    className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <label htmlFor={`current-${idx}`} className="text-xs font-semibold text-slate-700">
                    Currently working in this role
                  </label>
                </div>
              </div>
            ))}
          </div>

          {/* Section 4: Education */}
          <div className="space-y-4 bg-slate-50/50 p-4 rounded-xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-200 pb-2">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-indigo-600" /> Education
              </h3>
              <button
                type="button"
                onClick={handleAddEducation}
                className="text-xs font-bold text-indigo-600 hover:text-indigo-800 flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" /> Add Education
              </button>
            </div>

            {education.map((edu, idx) => (
              <div key={idx} className="p-3 bg-white border border-slate-200 rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-700 text-xs">Education #{idx + 1}</span>
                  <button
                    type="button"
                    onClick={() => handleRemoveEducation(idx)}
                    className="text-rose-500 hover:text-rose-700 p-1"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Institution *</label>
                    <input
                      type="text"
                      required
                      value={edu.institution}
                      onChange={(e) => {
                        const copy = [...education];
                        copy[idx].institution = e.target.value;
                        setEducation(copy);
                      }}
                      className="w-full p-2 rounded-md border border-slate-300"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Degree *</label>
                    <input
                      type="text"
                      required
                      value={edu.degree}
                      onChange={(e) => {
                        const copy = [...education];
                        copy[idx].degree = e.target.value;
                        setEducation(copy);
                      }}
                      className="w-full p-2 rounded-md border border-slate-300"
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-semibold text-slate-600 mb-0.5">Field of Study</label>
                    <input
                      type="text"
                      value={edu.field}
                      onChange={(e) => {
                        const copy = [...education];
                        copy[idx].field = e.target.value;
                        setEducation(copy);
                      }}
                      className="w-full p-2 rounded-md border border-slate-300"
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>

        </form>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-100 border-t border-slate-200 flex items-center justify-end gap-3">
          <button
            type="button"
            disabled={isSaving}
            onClick={onClose}
            className="px-4 py-2.5 text-xs font-bold text-slate-600 hover:bg-slate-200 rounded-lg transition-colors cursor-pointer disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            onClick={handleSave}
            disabled={isSaving}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-bold text-xs rounded-lg flex items-center gap-1.5 shadow-md cursor-pointer"
          >
            {isSaving ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                <span>Save Changes</span>
              </>
            )}
          </button>
        </div>

      </div>
    </div>
  );
};
