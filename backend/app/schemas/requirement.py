from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class RequirementSkillBase(BaseModel):
    skill: str
    importance: str = "MANDATORY"  # MANDATORY or PREFERRED

class RequirementSkillCreate(RequirementSkillBase):
    pass

class RequirementSkillResponse(RequirementSkillBase):
    id: str

    model_config = ConfigDict(from_attributes=True)

class RequirementBase(BaseModel):
    job_title: str
    job_description: str
    minimum_experience: int = 0
    maximum_experience: Optional[int] = None
    location: Optional[str] = None
    employment_type: Optional[str] = "Full-time"
    education_requirement: Optional[str] = None
    status: Optional[str] = "ACTIVE"

class RequirementCreate(RequirementBase):
    skills: Optional[List[RequirementSkillCreate]] = []

class RequirementUpdate(BaseModel):
    job_title: Optional[str] = None
    job_description: Optional[str] = None
    minimum_experience: Optional[int] = None
    maximum_experience: Optional[int] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    education_requirement: Optional[str] = None
    status: Optional[str] = None

class RequirementResponse(RequirementBase):
    id: str
    created_at: datetime
    skills: List[RequirementSkillResponse] = []
    active_candidate_matches_count: int = 0

    model_config = ConfigDict(from_attributes=True)
