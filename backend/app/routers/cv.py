import asyncio
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.user import User
from app.models.cv import CVOptimization
from app.schemas.cv import CVUploadResponse, CVOptimizeRequest, CVOptimizeResponse, CVHistoryItem
from app.core.security import get_current_user
from app.core.config import settings
from app.services import pdf_service, ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cv", tags=["CV"])


@router.post("/upload", response_model=CVUploadResponse, status_code=status.HTTP_200_OK)
async def upload_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF, extract its text in-memory with zero disk persistence, return the text."""
    # Validate extension
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported",
        )

    # Read entire file into memory buffer
    content = await file.read()

    # Check file size against MAX_FILE_SIZE_MB
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Validate magic bytes
    if not content.startswith(b"%PDF"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PDF file",
        )

    # Extract text purely in-memory
    try:
        extracted_text = await asyncio.to_thread(pdf_service.extract_text_from_pdf, content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return CVUploadResponse(
        filename=file.filename,
        extracted_text=extracted_text,
    )


@router.post("/optimize", response_model=CVOptimizeResponse)
async def optimize_cv(
    request: CVOptimizeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run AI optimization on provided CV text and persist the result to history."""
    if not request.cv_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CV text cannot be empty",
        )

    try:
        ai_result = await ai_service.optimize_cv(
            cv_text=request.cv_text,
            job_title=request.job_title,
            job_description=request.job_description,
        )
    except Exception as e:
        logger.error("AI CV optimization failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again later.",
        )

    # Persist to history
    record = CVOptimization(
        user_id          = current_user.id,
        job_title        = request.job_title,
        match_score      = ai_result["match_score"],
        optimized_text   = ai_result["optimized_text"],
        suggestions      = ai_result.get("suggestions", []),
        key_improvements = ai_result.get("key_improvements", []),
        missing_keywords = ai_result.get("missing_keywords", []),
    )
    db.add(record)
    await db.flush()

    return CVOptimizeResponse(
        optimized_text   = ai_result["optimized_text"],
        match_score      = ai_result["match_score"],
        suggestions      = ai_result.get("suggestions", []),
        key_improvements = ai_result.get("key_improvements", []),
        missing_keywords = ai_result.get("missing_keywords", []),
    )


@router.get("/history", response_model=List[CVHistoryItem])
async def get_cv_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current user's past CV optimizations, newest first."""
    result = await db.execute(
        select(CVOptimization)
        .where(CVOptimization.user_id == current_user.id)
        .order_by(CVOptimization.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/history/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cv_history_item(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a single CV optimization record owned by the current user."""
    result = await db.execute(
        select(CVOptimization).where(
            CVOptimization.id == record_id,
            CVOptimization.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    await db.delete(record)
