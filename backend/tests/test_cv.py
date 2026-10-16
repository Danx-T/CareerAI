import builtins
import os
import pytest
import pymupdf
import httpx
from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import User
from app.models.cv import CVOptimization
from app.services import ai_service


def _create_sample_pdf_bytes(
    text_content: str = "Jane Doe\nStaff Backend Engineer\nPython FastAPI Microservices",
) -> bytes:
    """Generate a valid PDF entirely in memory using PyMuPDF and return raw bytes."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text_content)
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


# ==============================================================================
# 1. CV Upload & File Validation Tests (POST /api/cv/upload)
# ==============================================================================


@pytest.mark.asyncio
async def test_upload_cv_requires_authentication(client: httpx.AsyncClient):
    """Uploading a CV without an authorization header must be rejected with 401."""
    pdf_bytes = _create_sample_pdf_bytes()
    files = {"file": ("resume.pdf", pdf_bytes, "application/pdf")}
    response = await client.post("/api/cv/upload", files=files)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_upload_cv_rejects_non_pdf_extension(
    client: httpx.AsyncClient,
    auth_headers: dict,
):
    """Uploading files with non-PDF extensions (e.g. .txt, .docx) returns HTTP 400 Bad Request."""
    for invalid_filename in ("resume.txt", "doc.docx", "avatar.png", "archive.zip"):
        files = {"file": (invalid_filename, b"Some arbitrary text content", "application/octet-stream")}
        response = await client.post("/api/cv/upload", files=files, headers=auth_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        detail = response.json().get("detail", "")
        assert "PDF" in detail


@pytest.mark.asyncio
async def test_upload_cv_rejects_invalid_magic_bytes(
    client: httpx.AsyncClient,
    auth_headers: dict,
):
    """Uploading a file named .pdf whose content does not start with %PDF must return HTTP 400."""
    fake_pdf_content = b"This is plain text pretending to be a PDF file."
    files = {"file": ("resume.pdf", fake_pdf_content, "application/pdf")}
    response = await client.post("/api/cv/upload", files=files, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = response.json().get("detail", "")
    assert "Invalid PDF" in detail


@pytest.mark.asyncio
async def test_upload_cv_rejects_empty_file_with_pdf_extension(
    client: httpx.AsyncClient,
    auth_headers: dict,
):
    """Uploading an empty 0-byte file with .pdf extension must return HTTP 400 (magic bytes check)."""
    files = {"file": ("empty.pdf", b"", "application/pdf")}
    response = await client.post("/api/cv/upload", files=files, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid PDF" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_upload_cv_rejects_file_exceeding_max_file_size(
    client: httpx.AsyncClient,
    auth_headers: dict,
):
    """Uploading a file exceeding MAX_FILE_SIZE_MB must return HTTP 400."""
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    oversized_content = b"%PDF-1.4\n" + b"A" * (max_bytes + 1024)

    files = {"file": ("huge_resume.pdf", oversized_content, "application/pdf")}
    response = await client.post("/api/cv/upload", files=files, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    detail = response.json().get("detail", "")
    assert "File too large" in detail


# ==============================================================================
# 2. In-Memory Upload & Zero Retention Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_upload_valid_in_memory_pdf_success_and_zero_disk_retention(
    client: httpx.AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Valid in-memory PDF generated with PyMuPDF extracts text correctly.
    Assert zero files are written to disk during the upload process.
    """
    sample_text = "Jane Doe\nStaff Backend Engineer\nPython FastAPI Microservices"
    pdf_bytes = _create_sample_pdf_bytes(sample_text)

    # Track any file writes to guarantee zero disk persistence
    written_files = []
    real_open = builtins.open

    def guarded_open(file, mode="r", *args, **kwargs):
        if any(flag in mode for flag in ("w", "a", "x")):
            written_files.append(str(file))
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)

    files = {"file": ("jane_doe_cv.pdf", pdf_bytes, "application/pdf")}
    response = await client.post("/api/cv/upload", files=files, headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["filename"] == "jane_doe_cv.pdf"
    extracted_text = data.get("extracted_text") or data.get("text", "")
    assert "Jane Doe" in extracted_text
    assert "Staff Backend Engineer" in extracted_text

    # Assert zero uploaded or temporary files were written to disk
    pdf_writes = [f for f in written_files if f.lower().endswith(".pdf") or "upload" in f.lower()]
    assert len(pdf_writes) == 0
    assert not os.path.exists("backend/uploads")
    assert not os.path.exists("uploads")


@pytest.mark.asyncio
async def test_upload_corrupt_pdf_structure_returns_422(
    client: httpx.AsyncClient,
    auth_headers: dict,
):
    """A file starting with %PDF but having unparseable structure returns HTTP 422."""
    corrupt_content = b"%PDF-1.4\nThis is completely corrupt garbage binary data not a valid PDF."
    files = {"file": ("corrupt.pdf", corrupt_content, "application/pdf")}
    response = await client.post("/api/cv/upload", files=files, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ==============================================================================
# 3. CV Optimization Validation & Execution Tests (POST /api/cv/optimize)
# ==============================================================================


@pytest.mark.asyncio
async def test_optimize_cv_requires_authentication(client: httpx.AsyncClient):
    """Calling /api/cv/optimize without authentication returns HTTP 401."""
    payload = {
        "cv_text": "Experienced software engineer with 5 years in Python.",
        "job_title": "Senior Python Developer",
        "job_description": "We are seeking a senior python engineer.",
    }
    response = await client.post("/api/cv/optimize", json=payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_optimize_cv_empty_cv_text_returns_400(
    client: httpx.AsyncClient,
    auth_headers: dict,
):
    """Whitespace-only cv_text returns HTTP 400 Bad Request."""
    payload = {
        "cv_text": "   \n\t  ",
        "job_title": "Backend Developer",
        "job_description": "We are looking for a backend developer.",
    }
    response = await client.post("/api/cv/optimize", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "CV text cannot be empty" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_optimize_cv_empty_string_cv_text_returns_422(
    client: httpx.AsyncClient,
    auth_headers: dict,
):
    """Empty string cv_text fails schema min_length validation with HTTP 422."""
    payload = {
        "cv_text": "",
        "job_title": "Backend Developer",
        "job_description": "We are looking for a backend developer.",
    }
    response = await client.post("/api/cv/optimize", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_optimize_cv_bounds_cv_text_exceeds_max_returns_422(
    client: httpx.AsyncClient,
    auth_headers: dict,
):
    """cv_text longer than 20,000 characters returns HTTP 422."""
    payload = {
        "cv_text": "A" * 20001,
        "job_title": "Backend Developer",
        "job_description": "We are looking for a backend developer.",
    }
    response = await client.post("/api/cv/optimize", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_optimize_cv_bounds_job_title_exceeds_max_returns_422(
    client: httpx.AsyncClient,
    auth_headers: dict,
):
    """job_title longer than 200 characters returns HTTP 422."""
    payload = {
        "cv_text": "Valid CV text content.",
        "job_title": "T" * 201,
        "job_description": "Valid job description.",
    }
    response = await client.post("/api/cv/optimize", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_optimize_cv_bounds_job_description_exceeds_max_returns_422(
    client: httpx.AsyncClient,
    auth_headers: dict,
):
    """job_description longer than 10,000 characters returns HTTP 422."""
    payload = {
        "cv_text": "Valid CV text content.",
        "job_title": "Valid Job Title",
        "job_description": "D" * 10001,
    }
    response = await client.post("/api/cv/optimize", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_optimize_cv_boundary_lengths_accepted(
    client: httpx.AsyncClient,
    auth_headers: dict,
):
    """Exact upper bound lengths (cv_text=20000, job_title=200, job_description=10000) succeed."""
    payload = {
        "cv_text": "C" * 20000,
        "job_title": "J" * 200,
        "job_description": "D" * 10000,
    }
    response = await client.post("/api/cv/optimize", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_optimize_cv_persists_to_history_and_returns_structured_result(
    client: httpx.AsyncClient,
    auth_headers: dict,
    test_user: User,
    db_session: AsyncSession,
):
    """
    With valid cv_text, job_title, and job_description:
    1. Returns HTTP 200 with structured optimization result
       (match_score, optimized_text, suggestions, key_improvements, missing_keywords).
    2. Persists the record to database history.
    3. Exposes the saved item via GET /api/cv/history.
    """
    payload = {
        "cv_text": "Experienced Python developer with 4 years building APIs using FastAPI and PostgreSQL.",
        "job_title": "Senior Cloud Engineer",
        "job_description": "Looking for a cloud engineer experienced in high-scale microservices, Docker, Kubernetes.",
    }
    response = await client.post("/api/cv/optimize", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data["match_score"], (int, float))
    assert data["match_score"] > 0
    assert "optimized_text" in data and len(data["optimized_text"]) > 0
    assert isinstance(data["suggestions"], list) and len(data["suggestions"]) > 0
    assert isinstance(data["key_improvements"], list) and len(data["key_improvements"]) > 0
    assert isinstance(data["missing_keywords"], list)

    # Verify persistence in database directly
    result = await db_session.execute(
        select(CVOptimization)
        .where(CVOptimization.user_id == test_user.id)
        .order_by(CVOptimization.created_at.desc())
    )
    db_record = result.scalars().first()
    assert db_record is not None
    assert db_record.job_title == "Senior Cloud Engineer"
    assert db_record.match_score == data["match_score"]
    assert db_record.optimized_text == data["optimized_text"]
    assert db_record.suggestions == data["suggestions"]
    assert db_record.key_improvements == data["key_improvements"]
    assert db_record.missing_keywords == data["missing_keywords"]

    # Verify item is returned via GET /api/cv/history
    history_res = await client.get("/api/cv/history", headers=auth_headers)
    assert history_res.status_code == status.HTTP_200_OK
    history_items = history_res.json()
    assert len(history_items) >= 1
    latest = history_items[0]
    assert latest["id"] == db_record.id
    assert latest["job_title"] == "Senior Cloud Engineer"
    assert latest["match_score"] == data["match_score"]
    assert latest["optimized_text"] == data["optimized_text"]
    assert latest["suggestions"] == data["suggestions"]
    assert latest["key_improvements"] == data["key_improvements"]
    assert latest["missing_keywords"] == data["missing_keywords"]


@pytest.mark.asyncio
async def test_optimize_cv_handles_ai_service_outage_gracefully(
    client: httpx.AsyncClient,
    auth_headers: dict,
    monkeypatch: pytest.MonkeyPatch,
):
    """When the underlying AI service fails, return HTTP 503 Service Unavailable."""
    async def _failing_optimize(*args, **kwargs):
        raise RuntimeError("Groq API connection timeout")

    monkeypatch.setattr(ai_service, "optimize_cv", _failing_optimize)

    payload = {
        "cv_text": "Experienced Python backend engineer.",
        "job_title": "Backend Engineer",
        "job_description": "We need an engineer.",
    }
    response = await client.post("/api/cv/optimize", json=payload, headers=auth_headers)
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "AI service is temporarily unavailable" in response.json().get("detail", "")


# ==============================================================================
# 4. Data Isolation Tests (Cross-User Access)
# ==============================================================================


@pytest.mark.asyncio
async def test_cv_data_isolation_between_users(
    client: httpx.AsyncClient,
    auth_headers: dict,
    test_user: User,
    user_factory,
    auth_headers_for,
    db_session: AsyncSession,
):
    """
    Data isolation verification:
    - User A creates a CV optimization.
    - User B attempting to view GET /api/cv/history/{id} is denied (404/405).
    - User B attempting to delete DELETE /api/cv/history/{id} returns HTTP 404 Not Found.
    - User A calling GET /api/cv/history only sees their own optimizations.
    - User B calling GET /api/cv/history cannot see User A's optimizations.
    """
    # 1. User A creates CV optimization
    payload_a = {
        "cv_text": "User A professional background in distributed systems.",
        "job_title": "Principal Architect",
        "job_description": "Lead architecture for enterprise cloud platforms.",
    }
    opt_res_a = await client.post("/api/cv/optimize", json=payload_a, headers=auth_headers)
    assert opt_res_a.status_code == status.HTTP_200_OK

    # Fetch User A's history record
    hist_res_a = await client.get("/api/cv/history", headers=auth_headers)
    assert hist_res_a.status_code == status.HTTP_200_OK
    user_a_history = hist_res_a.json()
    assert len(user_a_history) >= 1
    user_a_record_id = user_a_history[0]["id"]

    # 2. Create User B
    user_b = await user_factory(
        email="user_b@isolation.test",
        password="UserBPassword123!",
        full_name="User B",
    )
    user_b_headers = auth_headers_for(user_b)

    # 3. User B attempting to view User A's optimization directly returns 404 (or 405 Method Not Allowed)
    view_res = await client.get(f"/api/cv/history/{user_a_record_id}", headers=user_b_headers)
    assert view_res.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED)

    # 4. User B attempting to delete User A's optimization returns HTTP 404 Not Found
    del_res = await client.delete(f"/api/cv/history/{user_a_record_id}", headers=user_b_headers)
    assert del_res.status_code == status.HTTP_404_NOT_FOUND
    assert "Record not found" in del_res.json().get("detail", "")

    # 5. User B querying history only sees their own (currently empty)
    user_b_hist = await client.get("/api/cv/history", headers=user_b_headers)
    assert user_b_hist.status_code == status.HTTP_200_OK
    user_b_items = user_b_hist.json()
    assert len(user_b_items) == 0

    # 6. User B creates their own optimization
    payload_b = {
        "cv_text": "User B experience with frontend React and Vite applications.",
        "job_title": "Senior Frontend Developer",
        "job_description": "Expert in React and modern CSS.",
    }
    opt_res_b = await client.post("/api/cv/optimize", json=payload_b, headers=user_b_headers)
    assert opt_res_b.status_code == status.HTTP_200_OK

    # 7. Check mutual isolation on GET /api/cv/history
    user_b_check = await client.get("/api/cv/history", headers=user_b_headers)
    user_b_ids = [item["id"] for item in user_b_check.json()]
    assert user_a_record_id not in user_b_ids
    assert len(user_b_ids) == 1

    user_a_check = await client.get("/api/cv/history", headers=auth_headers)
    user_a_ids = [item["id"] for item in user_a_check.json()]
    assert user_a_record_id in user_a_ids
    assert user_b_ids[0] not in user_a_ids


@pytest.mark.asyncio
async def test_cv_history_user_can_delete_own_record(
    client: httpx.AsyncClient,
    auth_headers: dict,
    test_user: User,
    db_session: AsyncSession,
):
    """A user can successfully delete their own history record with HTTP 204."""
    # Seed a record
    record = CVOptimization(
        user_id=test_user.id,
        job_title="DevOps Specialist",
        match_score=92.0,
        optimized_text="Optimized CV content.",
        suggestions=["Add certs"],
        key_improvements=["Action verbs"],
        missing_keywords=["Terraform"],
    )
    db_session.add(record)
    await db_session.commit()
    await db_session.refresh(record)

    rec_id = record.id

    # Delete own record
    del_res = await client.delete(f"/api/cv/history/{rec_id}", headers=auth_headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify record is gone from history
    hist_res = await client.get("/api/cv/history", headers=auth_headers)
    remaining_ids = [item["id"] for item in hist_res.json()]
    assert rec_id not in remaining_ids

    # Subsequent deletion of same record returns 404
    del_again = await client.delete(f"/api/cv/history/{rec_id}", headers=auth_headers)
    assert del_again.status_code == status.HTTP_404_NOT_FOUND


# ==============================================================================
# 5. Cascade Deletion Tests (SQLite Foreign Keys & ORM Cascades)
# ==============================================================================


@pytest.mark.asyncio
async def test_cascade_deletion_via_admin_api(
    client: httpx.AsyncClient,
    admin_auth_headers: dict,
    user_factory,
    db_session: AsyncSession,
):
    """
    When an admin deletes a user via DELETE /api/admin/users/{user_id},
    all associated CVOptimization records are completely cascade-deleted.
    """
    # Create target user
    user = await user_factory(
        email="cascade_target_admin@test.com",
        password="CascadePassword123!",
        full_name="Cascade Target User",
    )

    # Create associated CV optimizations for this user
    cv1 = CVOptimization(
        user_id=user.id,
        job_title="Software Architect",
        match_score=85.0,
        optimized_text="Architect CV",
        suggestions=[],
        key_improvements=[],
        missing_keywords=[],
    )
    cv2 = CVOptimization(
        user_id=user.id,
        job_title="Site Reliability Engineer",
        match_score=90.0,
        optimized_text="SRE CV",
        suggestions=[],
        key_improvements=[],
        missing_keywords=[],
    )
    db_session.add_all([cv1, cv2])
    await db_session.commit()

    user_id = user.id

    # Verify records exist in database
    pre_query = await db_session.execute(
        select(CVOptimization).where(CVOptimization.user_id == user_id)
    )
    assert len(pre_query.scalars().all()) == 2

    # Admin deletes target user
    del_res = await client.delete(f"/api/admin/users/{user_id}", headers=admin_auth_headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # Verify all CV optimizations for deleted user are completely removed
    post_query = await db_session.execute(
        select(CVOptimization).where(CVOptimization.user_id == user_id)
    )
    assert len(post_query.scalars().all()) == 0


@pytest.mark.asyncio
async def test_cascade_deletion_via_direct_db_session(
    user_factory,
    db_session: AsyncSession,
):
    """
    When a user is deleted directly via SQLAlchemy session,
    database-level ON DELETE CASCADE completely deletes all CVOptimization records.
    """
    # Create user
    user = await user_factory(
        email="cascade_target_db@test.com",
        password="CascadeDbPassword123!",
        full_name="Cascade DB Target",
    )

    cv = CVOptimization(
        user_id=user.id,
        job_title="Data Engineer",
        match_score=88.0,
        optimized_text="Data Engineer CV",
        suggestions=["Add Spark"],
        key_improvements=["Emphasize ETL"],
        missing_keywords=["Airflow"],
    )
    db_session.add(cv)
    await db_session.commit()

    user_id = user.id

    # Delete user directly in session
    await db_session.delete(user)
    await db_session.commit()

    # Verify CVOptimization record is gone
    post_query = await db_session.execute(
        select(CVOptimization).where(CVOptimization.user_id == user_id)
    )
    assert len(post_query.scalars().all()) == 0
