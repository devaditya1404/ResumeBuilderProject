import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_title = Column(String(255), nullable=False, index=True)
    job_description = Column(Text, nullable=False)

    minimum_experience = Column(Integer, nullable=False, default=0)
    maximum_experience = Column(Integer, nullable=True)

    location = Column(String(255), nullable=True)
    employment_type = Column(String(100), default="Full-time")
    education_requirement = Column(String(255), nullable=True)

    status = Column(String(50), default="ACTIVE")  # ACTIVE, CLOSED, DRAFT
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    requirement_skills = relationship("RequirementSkill", back_populates="requirement", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="requirement", cascade="all, delete-orphan")

class RequirementSkill(Base):
    __tablename__ = "requirement_skills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    requirement_id = Column(String(36), ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True)

    skill = Column(String(100), nullable=False)
    importance = Column(String(20), nullable=False, default="MANDATORY")  # MANDATORY, PREFERRED

    requirement = relationship("Requirement", back_populates="requirement_skills")
