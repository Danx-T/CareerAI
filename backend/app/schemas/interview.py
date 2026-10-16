from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class InterviewCreate(BaseModel):
    job_title: str
    job_description: str
    num_questions: int = Field(default=8, ge=1, le=20)


class QuestionResponse(BaseModel):
    id: int
    order_index: int
    question_text: str
    category: str
    user_answer: Optional[str] = None
    ai_feedback: Optional[str] = None
    score: Optional[float] = None

    model_config = {"from_attributes": True}


class InterviewSessionResponse(BaseModel):
    id: int
    job_title: str
    status: str
    overall_score: Optional[float] = None
    total_questions: int
    answered_questions: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class InterviewSessionDetailResponse(InterviewSessionResponse):
    questions: List[QuestionResponse] = []
    summary_feedback: Optional[str] = None

    model_config = {"from_attributes": True}


class AnswerSubmit(BaseModel):
    answer: str


class AnswerSaveResponse(BaseModel):
    question_id: int
    saved: bool
    answered_count: int


class InterviewReportResponse(BaseModel):
    session_id: int
    job_title: str
    overall_score: float
    total_questions: int
    questions: List[QuestionResponse]
    summary_feedback: str
    category_scores: dict
    top_strengths: List[str]
    top_improvements: List[str]
