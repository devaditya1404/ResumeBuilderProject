import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    current_location = Column(String(255), nullable=True, index=True)

    current_company = Column(String(255), nullable=True, index=True)
    current_designation = Column(String(255), nullable=True, index=True)

    latest_company = Column(String(255), nullable=True, index=True)
    latest_designation = Column(String(255), nullable=True, index=True)

    experience_months = Column(Integer, nullable=True, default=None)
    experience_years = Column(Float, nullable=True, default=None)

    # Missing information MUST stay NULL (Anti-hallucination rule)
    notice_period = Column(String(100), nullable=True, default=None)
    preferred_location = Column(String(255), nullable=True, default=None)
    expected_salary = Column(String(100), nullable=True, default=None)

    professional_summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    experiences = relationship("CandidateExperience", back_populates="candidate", cascade="all, delete-orphan")
    candidate_skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    education = relationship("CandidateEducation", back_populates="candidate", cascade="all, delete-orphan")
    certifications = relationship("CandidateCertification", back_populates="candidate", cascade="all, delete-orphan")
    projects = relationship("CandidateProject", back_populates="candidate", cascade="all, delete-orphan")
    notes = relationship("RecruiterNote", back_populates="candidate", cascade="all, delete-orphan")
    contact_events = relationship("CandidateContactEvent", back_populates="candidate", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="candidate", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="candidate", cascade="all, delete-orphan")
