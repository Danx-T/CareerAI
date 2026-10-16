from pydantic import BaseModel
from typing import List
from datetime import datetime


class CVUploadResponse(BaseModel):
    filename: str
    extracted_text: str


class CVOptimizeRequest(BaseModel):
    cv_text: str
    job_title: str
    job_description: str


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
