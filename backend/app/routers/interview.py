import asyncio
import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.models.user import User
from app.models.interview import InterviewSession, InterviewQuestion
from app.schemas.interview import (
    InterviewCreate,
    InterviewSessionResponse,
    InterviewSessionDetailResponse,
    AnswerSubmit,
    AnswerSaveResponse,
    InterviewReportResponse,
    QuestionResponse,
)
from app.core.security import get_current_user
from app.services import ai_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/interview", tags=["Interview"])


@router.post("/start", response_model=InterviewSessionDetailResponse, status_code=status.HTTP_201_CREATED)
async def start_interview(
    request: InterviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Generate questions via AI
    try:
        questions_data = await ai_service.generate_interview_questions(
            job_title=request.job_title,
            job_description=request.job_description,
            num_questions=request.num_questions,
        )
    except Exception as exc:
        logger.error("AI question generation failed: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again later.",
        )

    # Create session
    session = InterviewSession(
        user_id=current_user.id,
        job_title=request.job_title,
        job_description=request.job_description,
        total_questions=len(questions_data),
        answered_questions=0,
    )
    db.add(session)
    await db.flush()

    # Create question records
    question_objs = []
    for q in questions_data:
        question = InterviewQuestion(
            session_id=session.id,
            order_index=q.get("order_index", 0),
            question_text=q["question_text"],
            category=q.get("category", "general"),
        )
        db.add(question)
        question_objs.append(question)

    await db.flush()
    await db.refresh(session)
    for q in question_objs:
        await db.refresh(q)

    return InterviewSessionDetailResponse(
        id=session.id,
        job_title=session.job_title,
        status=session.status,
        overall_score=session.overall_score,
        total_questions=session.total_questions,
        answered_questions=session.answered_questions,
        created_at=session.created_at,
        completed_at=session.completed_at,
        summary_feedback=session.summary_feedback,
        top_strengths=session.top_strengths or [],
        top_improvements=session.top_improvements or [],
        questions=[QuestionResponse.model_validate(q) for q in question_objs],
    )


@router.get("/sessions", response_model=List[InterviewSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InterviewSession)
        .where(InterviewSession.user_id == current_user.id)
        .order_by(InterviewSession.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{session_id}", response_model=InterviewSessionDetailResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    q_result = await db.execute(
        select(InterviewQuestion)
        .where(InterviewQuestion.session_id == session_id)
        .order_by(InterviewQuestion.order_index)
    )
    questions = q_result.scalars().all()

    return InterviewSessionDetailResponse(
        id=session.id,
        job_title=session.job_title,
        status=session.status,
        overall_score=session.overall_score,
        total_questions=session.total_questions,
        answered_questions=session.answered_questions,
        created_at=session.created_at,
        completed_at=session.completed_at,
        summary_feedback=session.summary_feedback,
        top_strengths=session.top_strengths or [],
        top_improvements=session.top_improvements or [],
        questions=[QuestionResponse.model_validate(q) for q in questions],
    )


@router.patch("/{session_id}/answer/{question_id}", response_model=AnswerSaveResponse)
async def save_answer(
    session_id: int,
    question_id: int,
    answer_data: AnswerSubmit,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Save an answer locally (no AI evaluation). Called as user fills in answers."""
    sess_result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )
    session = sess_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if session.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session already completed",
        )

    q_result = await db.execute(
        select(InterviewQuestion).where(
            InterviewQuestion.id == question_id,
            InterviewQuestion.session_id == session_id,
        )
    )
    question = q_result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    is_clearing = not bool(answer_data.answer.strip()) if answer_data.answer else True
    had_answer = bool(question.user_answer and question.user_answer.strip())
    question.user_answer = answer_data.answer.strip() if not is_clearing else None

    if is_clearing and had_answer:
        session.answered_questions = max(0, session.answered_questions - 1)
    elif not is_clearing and not had_answer:
        session.answered_questions = min(session.total_questions, session.answered_questions + 1)

    await db.flush()

    return AnswerSaveResponse(
        question_id=question_id,
        saved=True,
        answered_count=session.answered_questions,
    )


@router.post("/{session_id}/complete", response_model=InterviewReportResponse)
async def complete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Evaluate all saved answers with AI, then generate the report."""
    sess_result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == current_user.id,
        )
    )
    session = sess_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if session.status == "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session already completed",
        )

    q_result = await db.execute(
        select(InterviewQuestion)
        .where(InterviewQuestion.session_id == session_id)
        .order_by(InterviewQuestion.order_index)
    )
    questions = q_result.scalars().all()

    now = datetime.now(timezone.utc)

    # ── Step 1: Evaluate all answered questions concurrently ──
    sem = asyncio.Semaphore(3)

    async def _evaluate_single_question(question: InterviewQuestion):
        async with sem:
            try:
                feedback = await ai_service.evaluate_answer(
                    question_text=question.question_text,
                    category=question.category,
                    user_answer=question.user_answer,
                    job_title=session.job_title,
                    job_description=session.job_description,
                )
                question.ai_feedback = feedback.get("feedback", "")
                question.score = float(feedback.get("score", 0.0))
                question.strengths = (
                    feedback.get("strengths")
                    if isinstance(feedback.get("strengths"), list)
                    else []
                )
                question.improvements = (
                    feedback.get("improvements")
                    if isinstance(feedback.get("improvements"), list)
                    else []
                )
                question.model_answer_hint = feedback.get("model_answer_hint")
            except Exception as exc:
                logger.error(
                    "AI answer evaluation failed for question %s: %s",
                    question.id,
                    str(exc),
                    exc_info=True,
                )
                question.ai_feedback = "Could not evaluate this answer."
                question.score = None
                question.strengths = []
                question.improvements = []
                question.model_answer_hint = None
            question.answered_at = now

    answered_questions = [
        q for q in questions if q.user_answer and q.user_answer.strip()
    ]
    if answered_questions:
        await asyncio.gather(*(_evaluate_single_question(q) for q in answered_questions))

    await db.flush()

    # ── Step 2: Build QA data for the overall report ──
    qa_data = [
        {
            "question_text": q.question_text,
            "category": q.category,
            "user_answer": q.user_answer or "",
            "score": q.score,
        }
        for q in questions
    ]

    # ── Step 3: Generate the overall session report ──
    try:
        report = await ai_service.generate_interview_report(
            job_title=session.job_title,
            questions_with_answers=qa_data,
        )
    except Exception as exc:
        logger.error(
            "AI interview report generation failed for session %s: %s",
            session.id,
            str(exc),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service is temporarily unavailable. Please try again later.",
        )

    # ── Step 4: Persist final session results ──
    scored = [q.score for q in questions if q.score is not None]
    overall_score = round(sum(scored) / len(scored), 1) if scored else 0.0

    session.overall_score = overall_score
    session.summary_feedback = report.get("summary_feedback", "")
    session.status = "completed"
    session.completed_at = now
    session.top_strengths = (
        report.get("top_strengths")
        if isinstance(report.get("top_strengths"), list)
        else []
    )
    session.top_improvements = (
        report.get("top_improvements")
        if isinstance(report.get("top_improvements"), list)
        else []
    )
    session.answered_questions = len(answered_questions)
    await db.flush()

    return InterviewReportResponse(
        session_id=session.id,
        job_title=session.job_title,
        overall_score=overall_score,
        total_questions=session.total_questions,
        questions=[QuestionResponse.model_validate(q) for q in questions],
        summary_feedback=report.get("summary_feedback", ""),
        category_scores=report.get("category_scores", {}),
        top_strengths=session.top_strengths or [],
        top_improvements=session.top_improvements or [],
    )
