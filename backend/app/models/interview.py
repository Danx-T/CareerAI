from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_title = Column(String, nullable=False)
    job_description = Column(Text, nullable=False)
    status = Column(String, default="active")  # active | completed
    overall_score = Column(Float, nullable=True)
    total_questions = Column(Integer, default=0)
    answered_questions = Column(Integer, default=0)
    summary_feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="interview_sessions")
    questions = relationship(
        "InterviewQuestion", back_populates="session", cascade="all, delete-orphan"
    )


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(
        Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False
    )
    order_index = Column(Integer, nullable=False)
    question_text = Column(Text, nullable=False)
    category = Column(String, nullable=False)  # behavioral | technical | situational
    user_answer = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    answered_at = Column(DateTime, nullable=True)

    session = relationship("InterviewSession", back_populates="questions")
