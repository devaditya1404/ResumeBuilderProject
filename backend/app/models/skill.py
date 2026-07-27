import uuid
from sqlalchemy import Column, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Skill(Base):
    __tablename__ = "skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(100), nullable=True)  # Technical, Management, Tools, etc.

    candidate_skills = relationship("CandidateSkill", back_populates="skill", cascade="all, delete-orphan")

class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(String(36), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False, index=True)

    source = Column(String(50), default="resume")  # resume, calculated, recruiter
    confidence = Column(Float, default=1.0)

    __table_args__ = (
        UniqueConstraint('candidate_id', 'skill_id', name='uq_candidate_skill'),
    )

    candidate = relationship("Candidate", back_populates="candidate_skills")
    skill = relationship("Skill", back_populates="candidate_skills")
