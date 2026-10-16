from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List


class InterviewCreate(BaseModel):
    job_title: str = Field(..., min_length=1, max_length=200)
    job_description: str = Field(..., min_length=1, max_length=10000)
    num_questions: int = Field(default=8, ge=1, le=20)


class QuestionResponse(BaseModel):
    id: int
    order_index: int
    question_text: str
    category: str
    user_answer: Optional[str] = None
    ai_feedback: Optional[str] = None
    score: Optional[float] = None
    strengths: List[str] = []
    improvements: List[str] = []
    model_answer_hint: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("strengths", "improvements", mode="before")
    @classmethod
    def coerce_none_to_list(cls, v):
        return v if v is not None else []


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
    top_strengths: List[str] = []
    top_improvements: List[str] = []

    model_config = {"from_attributes": True}

    @field_validator("top_strengths", "top_improvements", mode="before")
    @classmethod
    def coerce_none_to_list(cls, v):
        return v if v is not None else []


class AnswerSubmit(BaseModel):
    answer: str = Field(..., min_length=1, max_length=5000)


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
