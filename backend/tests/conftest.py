import os

# Set test environment variables BEFORE importing app or settings
os.environ["SECRET_KEY"] = "test-secret-key-for-careerai-automated-testing-1234567890"
os.environ["GROQ_API_KEY"] = "gsk_testdummyapikey1234567890abcdef"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"

import pytest
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import engine, Base, AsyncSessionLocal
from app.main import app
from app.models.user import User
from app.core.security import get_password_hash_async, create_access_token
from app.services import ai_service


@pytest.fixture(autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_db():
    yield
    engine.sync_engine.dispose()
    for db_path in ("test.db", "backend/test.db"):
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass


@pytest.fixture
async def db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()


@pytest.fixture
async def client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


async def _mock_optimize_cv(
    cv_text: str,
    job_title: str,
    job_description: str,
) -> dict:
    return {
        "optimized_text": (
            f"# Senior {job_title}\n\n"
            "## Summary\n"
            f"Experienced {job_title} specializing in high-scale systems, reliability engineering, and cloud infrastructure.\n\n"
            "## Key Achievements\n"
            "- Designed microservices processing 15,000 requests/second with 99.99% availability.\n"
            "- Optimized asynchronous queries reducing p99 latency by 55%.\n\n"
            "## Professional Experience\n"
            f"- Lead Engineer: Successfully architected solutions matching {job_title} requirements."
        ),
        "match_score": 88.5,
        "suggestions": [
            "Quantify project achievements with measurable business impact metrics.",
            "Emphasize experience directly aligned with the core technical stack.",
            "Highlight leadership and cross-functional collaboration examples.",
        ],
        "key_improvements": [
            "Enhanced bullet points with strong action verbs and professional phrasing.",
            "Integrated critical missing keywords naturally into experience descriptions.",
            "Refined summary section to align closely with the target job title.",
        ],
        "missing_keywords": ["FastAPI", "Docker", "Kubernetes", "PostgreSQL"],
    }


async def _mock_generate_interview_questions(
    job_title: str,
    job_description: str,
    num_questions: int = 8,
) -> list:
    base_questions = [
        {
            "order_index": 1,
            "question_text": f"Can you describe your experience designing backend systems for a {job_title} role?",
            "category": "technical",
        },
        {
            "order_index": 2,
            "question_text": "Tell me about a time when you had to resolve a severe technical disagreement within your team.",
            "category": "behavioral",
        },
        {
            "order_index": 3,
            "question_text": "How do you respond when a high-priority production incident occurs with little available documentation?",
            "category": "situational",
        },
        {
            "order_index": 4,
            "question_text": "How do you ensure test coverage and software reliability in fast-paced release cycles?",
            "category": "technical",
        },
        {
            "order_index": 5,
            "question_text": "Describe a project where you had to adapt quickly to changing business requirements.",
            "category": "behavioral",
        },
        {
            "order_index": 6,
            "question_text": "If a critical third-party API begins returning 500 errors during peak traffic, what is your triage plan?",
            "category": "situational",
        },
        {
            "order_index": 7,
            "question_text": "How do you optimize asynchronous database queries under high concurrency?",
            "category": "technical",
        },
        {
            "order_index": 8,
            "question_text": "Tell me about a mentor or leadership experience that significantly shaped your engineering practices.",
            "category": "behavioral",
        },
    ]
    if num_questions <= len(base_questions):
        return base_questions[:num_questions]
    result = list(base_questions)
    for idx in range(len(base_questions) + 1, num_questions + 1):
        cat = "technical" if idx % 3 == 1 else ("behavioral" if idx % 3 == 2 else "situational")
        result.append({
            "order_index": idx,
            "question_text": f"Additional interview question {idx} regarding {job_title} responsibilities?",
            "category": cat,
        })
    return result


async def _mock_evaluate_answer(
    question_text: str,
    category: str,
    user_answer: str,
    job_title: str,
    job_description: str,
) -> dict:
    return {
        "score": 85.0,
        "feedback": f"Strong and comprehensive response demonstrating relevant {category} expertise for a {job_title}.",
        "strengths": [
            "Clear and structured articulation of technical concepts",
            "Demonstrated practical hands-on problem solving",
            "Aligned well with professional software engineering standards",
        ],
        "improvements": [
            "Incorporate specific quantitative metrics to measure end-to-end outcome",
            "Mention contingency planning and edge case considerations",
        ],
        "model_answer_hint": "An exemplary answer highlights root-cause diagnosis, cross-functional communication, and architectural trade-offs.",
    }


async def _mock_generate_interview_report(
    job_title: str,
    questions_with_answers: list,
) -> dict:
    return {
        "summary_feedback": (
            f"The candidate demonstrated strong domain knowledge and effective communication throughout the {job_title} mock interview. "
            "Technical responses showed architectural maturity, while behavioral answers reflected a collaborative and proactive mindset."
        ),
        "category_scores": {
            "technical": 87.5,
            "behavioral": 85.0,
            "situational": 82.5,
        },
        "top_strengths": [
            "Architectural clarity and deep backend systems reasoning",
            "Proactive approach to team alignment and production incidents",
            "Consistent use of structured answers and clear communication",
        ],
        "top_improvements": [
            "Practice quantifying performance improvements with explicit business metrics",
            "Adopt the STAR method more systematically across all behavioral responses",
        ],
    }


@pytest.fixture(autouse=True)
def mock_ai_service(monkeypatch):
    monkeypatch.setattr(ai_service, "optimize_cv", _mock_optimize_cv)
    monkeypatch.setattr(ai_service, "generate_interview_questions", _mock_generate_interview_questions)
    monkeypatch.setattr(ai_service, "evaluate_answer", _mock_evaluate_answer)
    monkeypatch.setattr(ai_service, "generate_interview_report", _mock_generate_interview_report)


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        email="testuser@example.com",
        full_name="Test User",
        hashed_password=await get_password_hash_async("TestPassword123!"),
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin_user(db_session: AsyncSession) -> User:
    user = User(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=await get_password_hash_async("AdminPassword123!"),
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def test_user_token(test_user: User) -> str:
    return create_access_token(data={"sub": str(test_user.id)})


@pytest.fixture
def auth_headers(test_user_token: str) -> dict:
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def admin_auth_headers(test_admin_user: User) -> dict:
    token = create_access_token(data={"sub": str(test_admin_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_factory(db_session: AsyncSession):
    async def _create_user(
        email: str = "otheruser@example.com",
        password: str = "OtherPassword123!",
        full_name: str = "Other User",
        is_active: bool = True,
        is_admin: bool = False,
    ) -> User:
        user = User(
            email=email.strip().lower(),
            full_name=full_name,
            hashed_password=await get_password_hash_async(password),
            is_active=is_active,
            is_admin=is_admin,
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create_user


@pytest.fixture
def auth_headers_for():
    def _make_headers(user: User) -> dict:
        token = create_access_token(data={"sub": str(user.id)})
        return {"Authorization": f"Bearer {token}"}

    return _make_headers
