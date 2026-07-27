from typing import List, Optional
from pydantic import BaseModel

class SkillDistributionItem(BaseModel):
    name: str
    count: int

class ExperienceDistributionItem(BaseModel):
    range: str
    count: int

class UploadActivityItem(BaseModel):
    date: str
    uploads: int

class DashboardStatsResponse(BaseModel):
    total_candidates: int = 0
    new_resumes: int = 0
    active_requirements: int = 0
    top_matches: int = 0
    candidates_contacted: int = 0
    average_match_score: float = 0.0

    skills_distribution: List[SkillDistributionItem] = []
    experience_distribution: List[ExperienceDistributionItem] = []
    upload_activity: List[UploadActivityItem] = []
