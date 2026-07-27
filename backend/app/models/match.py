import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Text, JSON, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    requirement_id = Column(String(36), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True)

    overall_score = Column(Float, nullable=False, default=0.0)
    skill_score = Column(Float, nullable=True, default=0.0)
    experience_score = Column(Float, nullable=True, default=0.0)
    education_score = Column(Float, nullable=True, default=0.0)
    role_score = Column(Float, nullable=True, default=0.0)
    location_score = Column(Float, nullable=True, default=0.0)

    matching_skills = Column(JSON, nullable=True, default=list)
    missing_mandatory_skills = Column(JSON, nullable=True, default=list)
    missing_preferred_skills = Column(JSON, nullable=True, default=list)
    strengths = Column(JSON, nullable=True, default=list)
    gaps = Column(JSON, nullable=True, default=list)

    explanation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('candidate_id', 'requirement_id', name='uq_candidate_requirement_match'),
    )

    candidate = relationship("Candidate", back_populates="match_results")
    requirement = relationship("Requirement", back_populates="match_results")
