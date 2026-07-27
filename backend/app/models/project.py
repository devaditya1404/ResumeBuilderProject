import uuid
from sqlalchemy import Column, String, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class CandidateProject(Base):
    __tablename__ = "candidate_projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(JSON, nullable=True, default=list)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)

    candidate = relationship("Candidate", back_populates="projects")
