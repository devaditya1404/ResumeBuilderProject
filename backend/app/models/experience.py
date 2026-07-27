import uuid
from sqlalchemy import Column, String, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class CandidateExperience(Base):
    __tablename__ = "candidate_experiences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(String(36), ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)

    company = Column(String(255), nullable=False)
    designation = Column(String(255), nullable=False)
    start_date = Column(String(100), nullable=True)
    end_date = Column(String(100), nullable=True)
    is_current = Column(Boolean, default=False)
    duration_months = Column(Integer, nullable=True, default=0)

    responsibilities = Column(JSON, nullable=True, default=list)  # list of strings
    clients = Column(JSON, nullable=True, default=list)           # list of strings (EMPLOYER != CLIENT)
    display_order = Column(Integer, default=0)

    # Relationships
    candidate = relationship("Candidate", back_populates="experiences")
    resume = relationship("Resume", back_populates="experiences")
