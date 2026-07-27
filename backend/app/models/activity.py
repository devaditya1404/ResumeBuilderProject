import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class RecruiterNote(Base):
    __tablename__ = "recruiter_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)

    content = Column(Text, nullable=False)
    author = Column(String(100), default="Recruiter Workspace")
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="notes")

class CandidateContactEvent(Base):
    __tablename__ = "candidate_contact_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(100), nullable=False)  # Phone Call, Email Sent, Interview Scheduled
    date = Column(String(100), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="contact_events")

class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(50), nullable=False)  # UPLOAD, UPDATE, CONTACTED, NOTE, MATCHED
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="timeline_events")
