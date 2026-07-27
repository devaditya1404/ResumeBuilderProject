import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False, unique=True)
    local_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, zip
    file_size = Column(Integer, nullable=False)     # bytes
    version = Column(Integer, default=1)

    raw_text = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    parsing_status = Column(String(50), default="PENDING")  # PENDING, PARSED, FAILED
    parsing_confidence = Column(Float, nullable=True, default=0.0)
    parsing_warnings = Column(Text, nullable=True)         # JSON or string warnings

    # Relationships
    candidate = relationship("Candidate", back_populates="resumes")
    experiences = relationship("CandidateExperience", back_populates="resume")
