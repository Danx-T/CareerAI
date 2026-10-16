from pydantic import BaseModel, Field
from typing import List
from datetime import datetime


class CVUploadResponse(BaseModel):
    filename: str
    extracted_text: str


class CVOptimizeRequest(BaseModel):
    cv_text: str = Field(..., min_length=1, max_length=20000)
    job_title: str = Field(..., min_length=1, max_length=200)
    job_description: str = Field(..., min_length=1, max_length=10000)


class CVOptimizeResponse(BaseModel):
    optimized_text: str
    match_score: float
    suggestions: List[str]
    key_improvements: List[str]
    missing_keywords: List[str]


class CVHistoryItem(BaseModel):
    id: int
    job_title: str
    match_score: float
    optimized_text: str
    suggestions: List[str]
    key_improvements: List[str]
    missing_keywords: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}
