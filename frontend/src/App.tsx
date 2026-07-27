import { useState, useEffect } from 'react';
import type { PageId, Candidate, Requirement, RecruiterNote, TimelineEvent, AppReportStats } from './types';
import { api } from './api/client';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { CandidateDetailDrawer } from './components/candidate/CandidateDetailDrawer';
import { DashboardPage } from './pages/DashboardPage';
import { TalentVaultPage } from './pages/TalentVaultPage';
import { UploadResumesPage } from './pages/UploadResumesPage';
import { RequirementsPage } from './pages/RequirementsPage';
import { AiRecommendationsPage } from './pages/AiRecommendationsPage';
import { AiChatPage } from './pages/AiChatPage';
import { ReportsPage } from './pages/ReportsPage';
import { SettingsPage } from './pages/SettingsPage';

const EMPTY_STATS: AppReportStats = {
  totalCandidates: 0,
  newResumesThisWeek: 0,
  activeRequirements: 0,
  topMatchesCount: 0,
  candidatesContacted: 0,
  avgMatchScore: 0,
  skillsDistribution: [],
  experienceDistribution: [],
  uploadActivity: []
};

export function mapBackendCandidateToCandidate(c: any): Candidate {
  return {
    id: c.id,
    name: c.name,
    designation: c.current_designation || c.latest_designation || 'Unspecified',
    email: c.email,
    phone: c.phone,
    linkedinUrl: c.linkedin_url,
    githubUrl: c.github_url,
    portfolioUrl: c.portfolio_url,
    location: c.current_location,
    preferredLocation: c.preferred_location,
    noticePeriod: c.notice_period,
    expectedSalary: c.expected_salary,
    experienceMonths: c.experience_months !== null && c.experience_months !== undefined ? c.experience_months : null,
    experienceYears: c.experience_years !== null && c.experience_years !== undefined ? c.experience_years : null,
    experienceDisplay:
      c.experience_years !== null && c.experience_years !== undefined
        ? `${Math.round(c.experience_years * 10) / 10} Years`
        : c.experience_months !== null && c.experience_months !== undefined
        ? `${c.experience_months} Months`
        : 'Experience unavailable',
    currentCompany: c.current_company,
    currentDesignation: c.current_designation,
    latestCompany: c.latest_company,
    latestDesignation: c.latest_designation,
    professionalSummary: c.professional_summary || '',
    summary: c.professional_summary || '',
    topSkills: c.skills ? c.skills.map((s: any) => s.skill_name) : [],
    categorizedSkills: [
      {
        category: 'Extracted Skills',
        skills: c.skills ? c.skills.map((s: any) => s.skill_name) : []
      }
    ],
    experiences: (c.experiences || []).map((exp: any) => ({
      id: exp.id || `exp-${Date.now()}`,
      company: exp.company,
      designation: exp.designation,
      startDate: exp.start_date || '',
      endDate: exp.end_date || '',
      isCurrent: exp.is_current || false,
      durationDisplay: `${exp.duration_months || 0} Months`,
      responsibilities: exp.responsibilities || [],
      clients: exp.clients || []
    })),
    education: (c.education || []).map((ed: any) => ({
      id: ed.id || `edu-${Date.now()}`,
      institution: ed.institution,
      degree: ed.degree,
      field: ed.field || '',
      startDate: ed.start_date || '',
      endDate: ed.end_date || ''
    })),
    certifications: (c.certifications || []).map((cert: any) => ({
      name: cert.name,
      issuer: cert.issuer || '',
      issueDate: cert.issue_date || '',
      expiryDate: cert.expiry_date || ''
    })),
    projects: (c.projects || []).map((proj: any) => ({
      name: proj.name,
      description: proj.description || '',
      technologies: proj.technologies || []
    })),
    aiInsights: {
      strengths: ['Relevant professional experience', 'Verified skill background'],
      experienceSummary: `${c.name} has ${c.experience_years || 0} years experience.`,
      coreSkills: c.skills ? c.skills.map((s: any) => s.skill_name) : [],
      potentialRoles: [c.current_designation || 'Software Professional'],
      careerProgression: 'Demonstrates steady experience.'
    },
    contactHistory: [],
    uploadedAt: c.created_at ? new Date(c.created_at).toLocaleDateString() : 'Recently'
  };
}

export function App() {
  const [activePage, setActivePage] = useState<PageId>('dashboard');
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [selectedRequirementId, setSelectedRequirementId] = useState<string>('');
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [stats, setStats] = useState<AppReportStats>(EMPTY_STATS);
  const [loading, setLoading] = useState<boolean>(true);

  // Local state maps for recruiter notes & events
  const [notesMap, setNotesMap] = useState<Record<string, RecruiterNote[]>>({});
  const [timelineMap, setTimelineMap] = useState<Record<string, TimelineEvent[]>>({});

  // Fetch real database records from FastAPI
  const loadData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Dashboard Stats from SQLite
      const statsRes = await api.getDashboardStats();
      setStats({
        totalCandidates: statsRes.total_candidates || 0,
        newResumesThisWeek: statsRes.new_resumes || 0,
        activeRequirements: statsRes.active_requirements || 0,
        topMatchesCount: statsRes.top_matches || 0,
        candidatesContacted: statsRes.candidates_contacted || 0,
        avgMatchScore: statsRes.average_match_score || 0,
        skillsDistribution: statsRes.skills_distribution || [],
        experienceDistribution: statsRes.experience_distribution || [],
        uploadActivity: statsRes.upload_activity || []
      });

      // 2. Fetch Candidates
      const candsRes = await api.getCandidates();
      const mappedCands: Candidate[] = candsRes.map((c) => mapBackendCandidateToCandidate(c));
      setCandidates(mappedCands);

      // 3. Fetch Requirements
      const reqsRes = await api.getRequirements();
      const mappedReqs: Requirement[] = reqsRes.map((r) => ({
        id: r.id,
        title: r.job_title,
        description: r.job_description,
        requiredSkills: (r.skills || []).filter((s: any) => s.importance === 'MANDATORY').map((s: any) => s.skill),
        preferredSkills: (r.skills || []).filter((s: any) => s.importance === 'PREFERRED').map((s: any) => s.skill),
        minExperienceYears: r.minimum_experience || 0,
        maxExperienceYears: r.maximum_experience,
        location: r.location || 'Unspecified',
        employmentType: r.employment_type || 'Full-time',
        education: r.education_requirement,
        activeCandidateMatchesCount: r.active_candidate_matches_count || 0,
        createdAt: r.created_at
      }));
      setRequirements(mappedReqs);
      if (mappedReqs.length > 0 && !selectedRequirementId) {
        setSelectedRequirementId(mappedReqs[0].id);
      }
    } catch (err) {
      console.warn('Backend API connection pending or SQLite empty:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreateRequirement = async (reqData: Partial<Requirement>) => {
    try {
      const payload = {
        job_title: reqData.title,
        job_description: reqData.description,
        minimum_experience: reqData.minExperienceYears || 0,
        location: reqData.location,
        skills: [
          ...(reqData.requiredSkills || []).map((s) => ({ skill: s, importance: 'MANDATORY' })),
          ...(reqData.preferredSkills || []).map((s) => ({ skill: s, importance: 'PREFERRED' }))
        ]
      };
      await api.createRequirement(payload);
      await loadData();
    } catch (err) {
      console.error('Failed to create requirement:', err);
    }
  };

  const handleAddNote = (candidateId: string, content: string) => {
    const newNote: RecruiterNote = {
      id: `note-${Date.now()}`,
      candidateId,
      content,
      createdAt: new Date().toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }),
      author: 'Recruiter Workspace'
    };

    setNotesMap((prev) => ({
      ...prev,
      [candidateId]: [newNote, ...(prev[candidateId] || [])]
    }));

    const newEvt: TimelineEvent = {
      id: `time-${Date.now()}`,
      candidateId,
      type: 'NOTE',
      title: 'Recruiter Note Added',
      description: content.length > 50 ? `${content.substring(0, 50)}...` : content,
      timestamp: new Date().toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })
    };

    setTimelineMap((prev) => ({
      ...prev,
      [candidateId]: [newEvt, ...(prev[candidateId] || [])]
    }));
  };

  const handleAddContactEvent = (candidateId: string, type: string, note: string) => {
    const newEvt: TimelineEvent = {
      id: `time-${Date.now()}`,
      candidateId,
      type: 'CONTACTED',
      title: `Outreach: ${type}`,
      description: note,
      timestamp: new Date().toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })
    };

    setTimelineMap((prev) => ({
      ...prev,
      [candidateId]: [newEvt, ...(prev[candidateId] || [])]
    }));
  };

  const activeRequirementTitle = requirements.find((r) => r.id === selectedRequirementId)?.title;

  const handleUpdateCandidateProfile = async (candidateId: string, updatedData: any) => {
    const rawRes = await api.updateCandidateProfile(candidateId, updatedData);
    await loadData();
    if (selectedCandidate?.id === candidateId && rawRes) {
      const updatedCand = mapBackendCandidateToCandidate(rawRes);
      setSelectedCandidate(updatedCand);
    }
  };

  const handleDeleteCandidate = async (candidateId: string) => {
    await api.deleteCandidate(candidateId);
    setCandidates((prev) => prev.filter((c) => c.id !== candidateId));
    if (selectedCandidate?.id === candidateId) {
      setSelectedCandidate(null);
    }
    await loadData();
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans overflow-hidden">
      {/* Sidebar Navigation */}
      <Sidebar activePage={activePage} onNavigate={setActivePage} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <Header
          activePage={activePage}
          onSearchClick={() => setActivePage('vault')}
          selectedRequirementTitle={activeRequirementTitle}
        />

        {/* Scrollable Page Body */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {activePage === 'dashboard' && (
            <DashboardPage
              candidates={candidates}
              requirements={requirements}
              stats={stats}
              loading={loading}
              onSelectCandidate={setSelectedCandidate}
              onNavigate={setActivePage}
            />
          )}

          {activePage === 'vault' && (
            <TalentVaultPage
              candidates={candidates}
              requirements={requirements}
              loading={loading}
              selectedRequirementId={selectedRequirementId}
              onSelectRequirementId={setSelectedRequirementId}
              onSelectCandidate={setSelectedCandidate}
              onDeleteCandidate={handleDeleteCandidate}
            />
          )}

          {activePage === 'upload' && <UploadResumesPage />}

          {activePage === 'requirements' && (
            <RequirementsPage
              requirements={requirements}
              loading={loading}
              onCreateRequirement={handleCreateRequirement}
              onSelectRequirement={setSelectedRequirementId}
              onNavigateToRecommendations={() => setActivePage('recommendations')}
            />
          )}

          {activePage === 'recommendations' && (
            <AiRecommendationsPage
              candidates={candidates}
              requirements={requirements}
              selectedRequirementId={selectedRequirementId}
              onSelectRequirementId={setSelectedRequirementId}
              onSelectCandidate={setSelectedCandidate}
            />
          )}

          {activePage === 'chat' && (
            <AiChatPage
              candidates={candidates}
              onSelectCandidate={setSelectedCandidate}
            />
          )}

          {activePage === 'reports' && <ReportsPage stats={stats} />}

          {activePage === 'settings' && <SettingsPage />}
        </main>
      </div>

      {/* Candidate Detail Right Drawer */}
      <CandidateDetailDrawer
        candidate={selectedCandidate}
        onClose={() => setSelectedCandidate(null)}
        selectedRequirementTitle={activeRequirementTitle}
        notes={selectedCandidate ? notesMap[selectedCandidate.id] || [] : []}
        timelineEvents={selectedCandidate ? timelineMap[selectedCandidate.id] || [] : []}
        onAddNote={handleAddNote}
        onAddContactEvent={handleAddContactEvent}
        onUpdateCandidateProfile={handleUpdateCandidateProfile}
      />
    </div>
  );
}

export default App;
