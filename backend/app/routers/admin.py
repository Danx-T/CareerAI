from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List

from app.db.database import get_db
from app.models.user import User
from app.models.interview import InterviewSession
from app.schemas.user import UserResponse
from app.core.security import get_current_user

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Admin guard ───────────────────────────────────────────────────────────────
async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


# ── Stats ─────────────────────────────────────────────────────────────────────
@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    total_users     = (await db.execute(select(func.count(User.id)))).scalar()
    active_users    = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar()
    admin_users     = (await db.execute(select(func.count(User.id)).where(User.is_admin == True))).scalar()
    total_sessions  = (await db.execute(select(func.count(InterviewSession.id)))).scalar()
    done_sessions   = (await db.execute(
        select(func.count(InterviewSession.id)).where(InterviewSession.status == "completed")
    )).scalar()
    avg_score_row   = (await db.execute(
        select(func.avg(InterviewSession.overall_score)).where(InterviewSession.overall_score.isnot(None))
    )).scalar()

    return {
        "total_users":        total_users,
        "active_users":       active_users,
        "admin_users":        admin_users,
        "total_sessions":     total_sessions,
        "completed_sessions": done_sessions,
        "avg_score":          round(avg_score_row, 1) if avg_score_row else None,
    }


# ── Users ─────────────────────────────────────────────────────────────────────
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return result.scalars().all()


@router.patch("/users/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_user_active(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    user.is_active = not user.is_active
    await db.flush()
    await db.refresh(user)
    return user


@router.patch("/users/{user_id}/toggle-admin", response_model=UserResponse)
async def toggle_user_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own admin status")
    user.is_admin = not user.is_admin
    await db.flush()
    await db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await db.delete(user)


# ── Sessions ──────────────────────────────────────────────────────────────────
@router.get("/sessions")
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(InterviewSession, User.email, User.full_name)
        .join(User, InterviewSession.user_id == User.id)
        .order_by(InterviewSession.created_at.desc())
    )
    rows = result.all()
    return [
        {
            "id":                  row.InterviewSession.id,
            "user_id":             row.InterviewSession.user_id,
            "user_email":          row.email,
            "user_name":           row.full_name,
            "job_title":           row.InterviewSession.job_title,
            "status":              row.InterviewSession.status,
            "overall_score":       row.InterviewSession.overall_score,
            "total_questions":     row.InterviewSession.total_questions,
            "answered_questions":  row.InterviewSession.answered_questions,
            "created_at":          row.InterviewSession.created_at,
            "completed_at":        row.InterviewSession.completed_at,
        }
        for row in rows
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    result = await db.execute(select(InterviewSession).where(InterviewSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await db.delete(session)
