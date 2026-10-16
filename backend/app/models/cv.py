from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.db.database import Base


class CVOptimization(Base):
    __tablename__ = "cv_optimizations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    job_title = Column(String, nullable=False)
    match_score = Column(Float, nullable=False)
    optimized_text = Column(Text, nullable=False)
    suggestions = Column(JSON, default=list)
    key_improvements = Column(JSON, default=list)
    missing_keywords = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="cv_optimizations")
