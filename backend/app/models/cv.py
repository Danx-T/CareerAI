from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from datetime import datetime

from app.db.database import Base


class CVOptimization(Base):
    __tablename__ = "cv_optimizations"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_title        = Column(String, nullable=False)
    match_score      = Column(Float, nullable=False)
    optimized_text   = Column(Text, nullable=False)
    suggestions      = Column(JSON, default=list)
    key_improvements = Column(JSON, default=list)
    missing_keywords = Column(JSON, default=list)
    created_at       = Column(DateTime, default=datetime.utcnow)
