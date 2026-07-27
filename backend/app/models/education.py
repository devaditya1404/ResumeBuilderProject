import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)

    institution = Column(String(255), nullable=False)
    degree = Column(String(255), nullable=False)
    field = Column(String(255), nullable=True)

    # Dates are explicitly nullable per prompt guidelines
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)

    candidate = relationship("Candidate", back_populates="education")
