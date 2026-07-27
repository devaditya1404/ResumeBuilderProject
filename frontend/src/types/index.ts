export type PageId = 
  | 'dashboard'
  | 'vault'
  | 'upload'
  | 'requirements'
  | 'recommendations'
  | 'chat'
  | 'reports'
  | 'settings';

export interface ExperienceEntry {
  id: string;
  company: string;
  designation: string;
  startDate: string;
  endDate: string;
  isCurrent: boolean;
  durationDisplay: string;
  responsibilities: string[];
  clients?: string[];
}

export interface SkillCategory {
  category: string;
  skills: string[];
}

export interface EducationEntry {
  id: string;
  institution: string;
  degree: string;
  field?: string;
  startDate?: string;
  endDate?: string;
}

export interface CertificationEntry {
  id?: string;
  name: string;
  issuer?: string;
  issueDate?: string;
  expiryDate?: string;
}

export interface ProjectEntry {
  id?: string;
  name: string;
  description?: string;
  technologies?: string[];
  startDate?: string;
  endDate?: string;
}

export interface GroundedEvidence {
  value: string;
  source: 'resume' | 'calculated' | 'inferred';
  evidence?: string;
}

export interface RecruiterNote {
  id: string;
  candidateId: string;
  content: string;
  createdAt: string;
  author: string;
}

export interface TimelineEvent {
  id: string;
  candidateId: string;
  type: 'UPLOAD' | 'UPDATE' | 'CONTACTED' | 'NOTE' | 'MATCHED';
  title: string;
  description: string;
  timestamp: string;
}

export interface Candidate {
  id: string;
  name: string;
  designation: string;
  email: string | null;
  phone: string | null;
  linkedinUrl: string | null;
  githubUrl: string | null;
  portfolioUrl: string | null;
  location: string | null;
  preferredLocation?: string | null;
  noticePeriod: string | null; // e.g. "30 Days", null if not in resume
  expectedSalary: string | null; // e.g. "$120,000 / yr", null if not in resume
  experienceMonths: number | null;
  experienceYears: number | null;
  experienceDisplay: string; // e.g. "5 Years 2 Months"
  currentCompany: string | null;
  currentDesignation?: string | null;
  latestCompany: string | null;
  latestDesignation?: string | null;
  professionalSummary: string;
  summary?: string;
  topSkills: string[];
  categorizedSkills: SkillCategory[];
  experiences: ExperienceEntry[];
  education: EducationEntry[];
  certifications: (string | CertificationEntry)[];
  projects?: ProjectEntry[];
  matchScore?: number; // Present when matched against a requirement
  matchBreakdown?: {
    overall: number;
    mandatorySkills: number;
    preferredSkills: number;
    experience: number;
    education: number;
    roleMatch: number;
    matchingSkills: string[];
    missingMandatorySkills: string[];
    missingPreferredSkills: string[];
    strengths: string[];
    gaps: string[];
    explanation: string;
  };
  aiInsights: {
    strengths: string[];
    experienceSummary: string;
    coreSkills: string[];
    potentialRoles: string[];
    careerProgression: string;
  };
  contactHistory: {
    date: string;
    type: string;
    note: string;
  }[];
  uploadedAt: string;
}

export interface Requirement {
  id: string;
  title: string;
  description: string;
  requiredSkills: string[];
  preferredSkills: string[];
  minExperienceYears: number;
  maxExperienceYears?: number;
  location: string;
  noticePeriod?: string;
  employmentType: string;
  education?: string;
  activeCandidateMatchesCount: number;
  createdAt: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  matchedCandidates?: Candidate[];
}

export interface AppReportStats {
  totalCandidates: number;
  newResumesThisWeek: number;
  activeRequirements: number;
  topMatchesCount: number;
  candidatesContacted: number;
  avgMatchScore: number;
  skillsDistribution: { name: string; count: number }[];
  experienceDistribution: { range: string; count: number }[];
  uploadActivity: { date: string; uploads: number }[];
}
