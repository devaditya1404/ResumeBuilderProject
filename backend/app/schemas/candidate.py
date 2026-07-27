from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

# Experience Schemas
class ExperienceBase(BaseModel):
    company: str
    designation: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    duration_months: Optional[int] = 0
    responsibilities: Optional[List[str]] = []
    clients: Optional[List[str]] = []
    display_order: Optional[int] = 0

class ExperienceCreate(ExperienceBase):
    pass

class ExperienceResponse(ExperienceBase):
    id: str
    candidate_id: str

    model_config = ConfigDict(from_attributes=True)

# Skill Schemas
class CandidateSkillResponse(BaseModel):
    skill_name: str
    category: Optional[str] = "Technical"
    source: Optional[str] = "resume"
    confidence: Optional[float] = 1.0

# Education Schemas
class EducationBase(BaseModel):
    institution: str
    degree: str
    field: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class EducationCreate(EducationBase):
    pass

class EducationResponse(EducationBase):
    id: str
    candidate_id: str

    model_config = ConfigDict(from_attributes=True)

# Certification Schemas
class CertificationBase(BaseModel):
    name: str
    issuer: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None

class CertificationCreate(CertificationBase):
    pass

class CertificationResponse(CertificationBase):
    id: str
    candidate_id: str

    model_config = ConfigDict(from_attributes=True)

# Project Schemas
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: Optional[List[str]] = []
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: str
    candidate_id: str

    model_config = ConfigDict(from_attributes=True)

# Candidate Core Schemas
class CandidateBase(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    current_location: Optional[str] = None

    current_company: Optional[str] = None
    current_designation: Optional[str] = None

    latest_company: Optional[str] = None
    latest_designation: Optional[str] = None

    experience_months: Optional[int] = 0
    experience_years: Optional[float] = 0.0

    notice_period: Optional[str] = None
    preferred_location: Optional[str] = None
    expected_salary: Optional[str] = None

    professional_summary: Optional[str] = None

class CandidateCreate(CandidateBase):
    experiences: Optional[List[ExperienceCreate]] = []
    skills: Optional[List[str]] = []
    education: Optional[List[EducationCreate]] = []
    certifications: Optional[List[CertificationCreate]] = []

class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    current_location: Optional[str] = None
    current_company: Optional[str] = None
    current_designation: Optional[str] = None
    latest_company: Optional[str] = None
    latest_designation: Optional[str] = None
    experience_months: Optional[int] = None
    experience_years: Optional[float] = None
    notice_period: Optional[str] = None
    preferred_location: Optional[str] = None
    expected_salary: Optional[str] = None
    professional_summary: Optional[str] = None

class CandidateProfileUpdate(CandidateUpdate):
    experiences: Optional[List[ExperienceCreate]] = None
    skills: Optional[List[str]] = None
    education: Optional[List[EducationCreate]] = None
    certifications: Optional[List[CertificationCreate]] = None
    projects: Optional[List[ProjectBase]] = None

class CandidateResponse(CandidateBase):
    id: str
    created_at: datetime
    updated_at: datetime

    experiences: List[ExperienceResponse] = []
    skills: List[CandidateSkillResponse] = []
    education: List[EducationResponse] = []
    certifications: List[CertificationResponse] = []

    model_config = ConfigDict(from_attributes=True)
