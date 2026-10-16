import pytest
import httpx
from app.services import ai_service


# ─────────────────────────────────────────────────────────────────────────────
# 1. Interview Start (POST /api/interview/start)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_interview_success(client: httpx.AsyncClient, auth_headers: dict):
    """With valid job_title and job_description, returns HTTP 201 Created

    with session details and generated questions list.
    """
    payload = {
        "job_title": "Senior Python Backend Developer",
        "job_description": (
            "We are looking for a Senior Backend Developer proficient in Python, "
            "FastAPI, PostgreSQL, and distributed microservices architecture."
        ),
    }

    response = await client.post(
        "/api/interview/start",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["job_title"] == payload["job_title"]
    assert data["status"] == "active"
    assert data["overall_score"] is None
    assert data["total_questions"] == 8
    assert data["answered_questions"] == 0
    assert data["created_at"] is not None
    assert data["completed_at"] is None
    assert data["summary_feedback"] is None
    assert data["top_strengths"] == []
    assert data["top_improvements"] == []

    questions = data["questions"]
    assert len(questions) == 8

    expected_categories = {"technical", "behavioral", "situational"}
    for idx, q in enumerate(questions, start=1):
        assert q["order_index"] == idx
        assert isinstance(q["question_text"], str) and len(q["question_text"]) > 0
        assert q["category"] in expected_categories
        assert q["user_answer"] is None
        assert q["ai_feedback"] is None
        assert q["score"] is None
        assert q["strengths"] == []
        assert q["improvements"] == []
        assert q["model_answer_hint"] is None


@pytest.mark.asyncio
async def test_start_interview_custom_num_questions(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Verify num_questions parameter controls number of generated questions."""
    payload = {
        "job_title": "DevOps Engineer",
        "job_description": "Kubernetes, CI/CD, Terraform, and cloud operations.",
        "num_questions": 3,
    }

    response = await client.post(
        "/api/interview/start",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["total_questions"] == 3
    assert len(data["questions"]) == 3
    assert [q["order_index"] for q in data["questions"]] == [1, 2, 3]


@pytest.mark.asyncio
async def test_start_interview_validation_job_title_exceeds_max(
    client: httpx.AsyncClient, auth_headers: dict
):
    """job_title > 200 characters returns HTTP 422 Unprocessable Entity."""
    payload = {
        "job_title": "A" * 201,
        "job_description": "Valid job description within character limits.",
    }

    response = await client.post(
        "/api/interview/start",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422
    errors = response.json().get("detail", [])
    assert any("job_title" in str(err.get("loc", [])) for err in errors)


@pytest.mark.asyncio
async def test_start_interview_validation_job_description_exceeds_max(
    client: httpx.AsyncClient, auth_headers: dict
):
    """job_description > 10000 characters returns HTTP 422 Unprocessable Entity."""
    payload = {
        "job_title": "Software Engineer",
        "job_description": "B" * 10001,
    }

    response = await client.post(
        "/api/interview/start",
        json=payload,
        headers=auth_headers,
    )

    assert response.status_code == 422
    errors = response.json().get("detail", [])
    assert any("job_description" in str(err.get("loc", [])) for err in errors)


@pytest.mark.asyncio
async def test_start_interview_validation_empty_bounds(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Empty strings for job_title or job_description return HTTP 422."""
    response1 = await client.post(
        "/api/interview/start",
        json={"job_title": "", "job_description": "Valid description"},
        headers=auth_headers,
    )
    assert response1.status_code == 422

    response2 = await client.post(
        "/api/interview/start",
        json={"job_title": "Valid title", "job_description": ""},
        headers=auth_headers,
    )
    assert response2.status_code == 422


@pytest.mark.asyncio
async def test_start_interview_validation_num_questions_bounds(
    client: httpx.AsyncClient, auth_headers: dict
):
    """num_questions outside 1-20 returns HTTP 422."""
    response_low = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Title",
            "job_description": "Description",
            "num_questions": 0,
        },
        headers=auth_headers,
    )
    assert response_low.status_code == 422

    response_high = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Title",
            "job_description": "Description",
            "num_questions": 21,
        },
        headers=auth_headers,
    )
    assert response_high.status_code == 422


@pytest.mark.asyncio
async def test_start_interview_ai_service_failure_returns_503(
    client: httpx.AsyncClient, auth_headers: dict, monkeypatch
):
    """When the AI service fails during question generation, returns HTTP 503."""
    async def _failing_generate(*args, **kwargs):
        raise RuntimeError("Groq rate limit exceeded")

    monkeypatch.setattr(ai_service, "generate_interview_questions", _failing_generate)

    response = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Backend Engineer",
            "job_description": "Designing scalable distributed systems.",
        },
        headers=auth_headers,
    )

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json().get("detail", "")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Answering Questions (PATCH /api/interview/{id}/answer/{qid})
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_answer_question_updates_counter_and_records_answer(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Submitting an answer updates answered_questions counter and records user_answer."""
    # 1. Start session
    start_resp = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Full Stack Developer",
            "job_description": "React, TypeScript, Python, and SQL.",
            "num_questions": 3,
        },
        headers=auth_headers,
    )
    assert start_resp.status_code == 201
    session_data = start_resp.json()
    session_id = session_data["id"]
    q1 = session_data["questions"][0]
    q1_id = q1["id"]

    # 2. Answer question 1
    answer_text = "I build modular React components and scalable FastAPI endpoints."
    patch_resp = await client.patch(
        f"/api/interview/{session_id}/answer/{q1_id}",
        json={"answer": answer_text},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    patch_data = patch_resp.json()
    assert patch_data["question_id"] == q1_id
    assert patch_data["saved"] is True
    assert patch_data["answered_count"] == 1

    # 3. Verify via GET session details
    get_resp = await client.get(
        f"/api/interview/{session_id}",
        headers=auth_headers,
    )
    assert get_resp.status_code == 200
    details = get_resp.json()
    assert details["answered_questions"] == 1
    retrieved_q1 = next(q for q in details["questions"] if q["id"] == q1_id)
    assert retrieved_q1["user_answer"] == answer_text


@pytest.mark.asyncio
async def test_answer_question_update_existing_does_not_double_count(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Updating an existing answer keeps answered_questions counter unchanged."""
    start_resp = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Backend Developer",
            "job_description": "Distributed systems engineering.",
            "num_questions": 3,
        },
        headers=auth_headers,
    )
    session_data = start_resp.json()
    session_id = session_data["id"]
    q1_id = session_data["questions"][0]["id"]
    q2_id = session_data["questions"][1]["id"]

    # First answer to q1
    resp1 = await client.patch(
        f"/api/interview/{session_id}/answer/{q1_id}",
        json={"answer": "First draft answer"},
        headers=auth_headers,
    )
    assert resp1.status_code == 200
    assert resp1.json()["answered_count"] == 1

    # Updated answer to q1
    resp2 = await client.patch(
        f"/api/interview/{session_id}/answer/{q1_id}",
        json={"answer": "Refined and expanded second draft answer"},
        headers=auth_headers,
    )
    assert resp2.status_code == 200
    assert resp2.json()["answered_count"] == 1

    # Answer to q2
    resp3 = await client.patch(
        f"/api/interview/{session_id}/answer/{q2_id}",
        json={"answer": "Answer to second question"},
        headers=auth_headers,
    )
    assert resp3.status_code == 200
    assert resp3.json()["answered_count"] == 2


@pytest.mark.asyncio
async def test_clear_answer_decrements_and_maintains_counter(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Submitting empty or whitespace string properly clears the answer

    and decrements/maintains answered_questions counter.
    """
    start_resp = await client.post(
        "/api/interview/start",
        json={
            "job_title": "QA Engineer",
            "job_description": "Automated testing and QA pipelines.",
            "num_questions": 3,
        },
        headers=auth_headers,
    )
    session_data = start_resp.json()
    session_id = session_data["id"]
    q1_id = session_data["questions"][0]["id"]

    # 1. Answer q1
    await client.patch(
        f"/api/interview/{session_id}/answer/{q1_id}",
        json={"answer": "I write comprehensive pytest test suites."},
        headers=auth_headers,
    )

    # 2. Clear q1 with empty string
    clear_resp1 = await client.patch(
        f"/api/interview/{session_id}/answer/{q1_id}",
        json={"answer": ""},
        headers=auth_headers,
    )
    assert clear_resp1.status_code == 200
    assert clear_resp1.json()["answered_count"] == 0

    get_resp1 = await client.get(f"/api/interview/{session_id}", headers=auth_headers)
    assert get_resp1.json()["answered_questions"] == 0
    q1_state = next(q for q in get_resp1.json()["questions"] if q["id"] == q1_id)
    assert q1_state["user_answer"] is None

    # 3. Answer q1 again
    await client.patch(
        f"/api/interview/{session_id}/answer/{q1_id}",
        json={"answer": "Re-added answer."},
        headers=auth_headers,
    )

    # 4. Clear q1 with whitespace-only string
    clear_resp2 = await client.patch(
        f"/api/interview/{session_id}/answer/{q1_id}",
        json={"answer": "   \n\t   "},
        headers=auth_headers,
    )
    assert clear_resp2.status_code == 200
    assert clear_resp2.json()["answered_count"] == 0

    get_resp2 = await client.get(f"/api/interview/{session_id}", headers=auth_headers)
    assert get_resp2.json()["answered_questions"] == 0
    q1_state2 = next(q for q in get_resp2.json()["questions"] if q["id"] == q1_id)
    assert q1_state2["user_answer"] is None

    # 5. Clearing an already unanswered question maintains counter at 0 (never negative)
    clear_resp3 = await client.patch(
        f"/api/interview/{session_id}/answer/{q1_id}",
        json={"answer": ""},
        headers=auth_headers,
    )
    assert clear_resp3.status_code == 200
    assert clear_resp3.json()["answered_count"] == 0


@pytest.mark.asyncio
async def test_answer_invalid_question_id_returns_404(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Submitting an answer for a non-existent question ID returns HTTP 404."""
    start_resp = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Site Reliability Engineer",
            "job_description": "Monitoring, alerts, incident management.",
            "num_questions": 2,
        },
        headers=auth_headers,
    )
    session_id = start_resp.json()["id"]

    response = await client.patch(
        f"/api/interview/{session_id}/answer/999999",
        json={"answer": "Some valid answer text."},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Question not found"


@pytest.mark.asyncio
async def test_answer_nonexistent_session_id_returns_404(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Submitting an answer for a non-existent session ID returns HTTP 404."""
    response = await client.patch(
        "/api/interview/999999/answer/1",
        json={"answer": "Some answer text."},
        headers=auth_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


@pytest.mark.asyncio
async def test_answer_question_from_different_session_returns_404(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Attempting to answer session A using question ID from session B returns HTTP 404."""
    # Create session 1
    resp1 = await client.post(
        "/api/interview/start",
        json={"job_title": "Role 1", "job_description": "Description 1", "num_questions": 2},
        headers=auth_headers,
    )
    session1_id = resp1.json()["id"]

    # Create session 2
    resp2 = await client.post(
        "/api/interview/start",
        json={"job_title": "Role 2", "job_description": "Description 2", "num_questions": 2},
        headers=auth_headers,
    )
    session2_q1_id = resp2.json()["questions"][0]["id"]

    # Attempt to answer session 1 with session 2's question ID
    patch_resp = await client.patch(
        f"/api/interview/{session1_id}/answer/{session2_q1_id}",
        json={"answer": "Cross session answer attempt."},
        headers=auth_headers,
    )

    assert patch_resp.status_code == 404
    assert patch_resp.json()["detail"] == "Question not found"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Interview Completion (POST /api/interview/{id}/complete)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_complete_interview_triggers_concurrent_evaluation_and_report(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Triggers concurrent answer evaluation (mocked via mock_ai_service).

    Calculates overall_score without corruption from unscored questions.
    Sets status to 'completed' and sets completed_at.
    Returns structured report with summary_feedback, overall_score,
    top_strengths, top_improvements, and question feedback.
    """
    # 1. Start session with 4 questions
    start_resp = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Cloud Architect",
            "job_description": "Architecting resilient multi-region infrastructure on AWS and GCP.",
            "num_questions": 4,
        },
        headers=auth_headers,
    )
    session_data = start_resp.json()
    session_id = session_data["id"]
    questions = session_data["questions"]

    # 2. Answer question 1 and question 2 (leave q3 and q4 unanswered)
    await client.patch(
        f"/api/interview/{session_id}/answer/{questions[0]['id']}",
        json={"answer": "I use Terraform for IaC and design active-active multi-region clusters."},
        headers=auth_headers,
    )
    await client.patch(
        f"/api/interview/{session_id}/answer/{questions[1]['id']}",
        json={"answer": "I resolve team disagreements through data-driven architectural benchmarks."},
        headers=auth_headers,
    )

    # 3. Complete interview session
    complete_resp = await client.post(
        f"/api/interview/{session_id}/complete",
        headers=auth_headers,
    )

    assert complete_resp.status_code == 200
    report = complete_resp.json()

    # Verify structured report contents
    assert report["session_id"] == session_id
    assert report["job_title"] == "Cloud Architect"
    assert report["total_questions"] == 4
    assert isinstance(report["summary_feedback"], str) and len(report["summary_feedback"]) > 0
    assert isinstance(report["category_scores"], dict)
    assert isinstance(report["top_strengths"], list) and len(report["top_strengths"]) > 0
    assert isinstance(report["top_improvements"], list) and len(report["top_improvements"]) > 0

    # Overall score calculation verification:
    # mock_ai_service returns score=85.0 for each evaluated question.
    # Unscored questions (q3 and q4) must not corrupt the average (must NOT count as 0.0).
    # Since 2 questions scored 85.0, overall_score should be 85.0.
    assert report["overall_score"] == 85.0

    # Verify question-level feedback
    q_reports = report["questions"]
    assert len(q_reports) == 4

    # Answered questions have evaluation data
    for q in q_reports[:2]:
        assert q["user_answer"] is not None
        assert q["score"] == 85.0
        assert q["ai_feedback"] is not None
        assert isinstance(q["strengths"], list) and len(q["strengths"]) > 0
        assert isinstance(q["improvements"], list) and len(q["improvements"]) > 0
        assert q["model_answer_hint"] is not None

    # Unanswered questions have None score and are unscored
    for q in q_reports[2:]:
        assert q["user_answer"] is None
        assert q["score"] is None
        assert q["ai_feedback"] is None

    # 4. Verify persisted state via GET /api/interview/{id}
    get_resp = await client.get(
        f"/api/interview/{session_id}",
        headers=auth_headers,
    )
    assert get_resp.status_code == 200
    saved_session = get_resp.json()
    assert saved_session["status"] == "completed"
    assert saved_session["completed_at"] is not None
    assert saved_session["overall_score"] == 85.0
    assert saved_session["answered_questions"] == 2
    assert saved_session["summary_feedback"] == report["summary_feedback"]
    assert saved_session["top_strengths"] == report["top_strengths"]
    assert saved_session["top_improvements"] == report["top_improvements"]


@pytest.mark.asyncio
async def test_complete_interview_with_zero_answered_questions(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Completing an interview with zero answered questions completes cleanly

    with overall_score=0.0 and status='completed'.
    """
    start_resp = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Data Scientist",
            "job_description": "Machine learning, statistical modeling, PyTorch.",
            "num_questions": 3,
        },
        headers=auth_headers,
    )
    session_id = start_resp.json()["id"]

    complete_resp = await client.post(
        f"/api/interview/{session_id}/complete",
        headers=auth_headers,
    )

    assert complete_resp.status_code == 200
    report = complete_resp.json()
    assert report["overall_score"] == 0.0
    assert report["total_questions"] == 3

    # Check persisted session
    get_resp = await client.get(f"/api/interview/{session_id}", headers=auth_headers)
    saved = get_resp.json()
    assert saved["status"] == "completed"
    assert saved["completed_at"] is not None
    assert saved["overall_score"] == 0.0
    assert saved["answered_questions"] == 0


@pytest.mark.asyncio
async def test_complete_interview_graceful_degradation_on_partial_eval_failure(
    client: httpx.AsyncClient, auth_headers: dict, monkeypatch
):
    """If one question evaluation fails, the system records placeholder feedback

    and computes overall_score from the successfully scored questions.
    """
    start_resp = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Security Engineer",
            "job_description": "Vulnerability management and application security.",
            "num_questions": 2,
        },
        headers=auth_headers,
    )
    session_id = start_resp.json()["id"]
    q1_id = start_resp.json()["questions"][0]["id"]
    q2_id = start_resp.json()["questions"][1]["id"]

    await client.patch(
        f"/api/interview/{session_id}/answer/{q1_id}",
        json={"answer": "I conduct static code analysis and threat modeling."},
        headers=auth_headers,
    )
    await client.patch(
        f"/api/interview/{session_id}/answer/{q2_id}",
        json={"answer": "I configure Web Application Firewalls and rate limiting."},
        headers=auth_headers,
    )

    # Monkeypatch evaluate_answer to fail for q2
    original_evaluate = ai_service.evaluate_answer

    async def _partial_fail_evaluate(**kwargs):
        if "Firewalls" in kwargs.get("user_answer", ""):
            raise RuntimeError("Evaluation model timeout")
        return await original_evaluate(**kwargs)

    monkeypatch.setattr(ai_service, "evaluate_answer", _partial_fail_evaluate)

    complete_resp = await client.post(
        f"/api/interview/{session_id}/complete",
        headers=auth_headers,
    )

    assert complete_resp.status_code == 200
    report = complete_resp.json()

    # q1 got 85.0, q2 failed (score is None). Overall score should be 85.0
    assert report["overall_score"] == 85.0

    questions_by_id = {q["id"]: q for q in report["questions"]}
    assert questions_by_id[q1_id]["score"] == 85.0
    assert questions_by_id[q2_id]["score"] is None
    assert "Could not evaluate this answer" in questions_by_id[q2_id]["ai_feedback"]


@pytest.mark.asyncio
async def test_complete_interview_ai_report_failure_returns_503(
    client: httpx.AsyncClient, auth_headers: dict, monkeypatch
):
    """When report generation fails, returns HTTP 503 while preserving evaluated question scores."""
    start_resp = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Product Manager",
            "job_description": "Roadmap planning, backlog prioritization.",
            "num_questions": 2,
        },
        headers=auth_headers,
    )
    session_data = start_resp.json()
    session_id = session_data["id"]
    q1_id = session_data["questions"][0]["id"]

    await client.patch(
        f"/api/interview/{session_id}/answer/{q1_id}",
        json={"answer": "I prioritize features using RICE scoring and customer discovery."},
        headers=auth_headers,
    )

    eval_call_count = 0
    original_eval = ai_service.evaluate_answer

    async def _counting_eval(*args, **kwargs):
        nonlocal eval_call_count
        eval_call_count += 1
        return await original_eval(*args, **kwargs)

    monkeypatch.setattr(ai_service, "evaluate_answer", _counting_eval)

    original_report = ai_service.generate_interview_report

    async def _failing_report(*args, **kwargs):
        raise RuntimeError("Report generation service down")

    monkeypatch.setattr(ai_service, "generate_interview_report", _failing_report)

    complete_resp = await client.post(
        f"/api/interview/{session_id}/complete",
        headers=auth_headers,
    )

    assert complete_resp.status_code == 503
    assert "temporarily unavailable" in complete_resp.json().get("detail", "")
    assert eval_call_count == 1

    # Verify question evaluation was persisted and not rolled back
    get_resp = await client.get(f"/api/interview/{session_id}", headers=auth_headers)
    q1_after_fail = next(q for q in get_resp.json()["questions"] if q["id"] == q1_id)
    assert q1_after_fail["score"] == 85.0

    # Restore report service and retry /complete: already-scored question must not be re-evaluated
    monkeypatch.setattr(ai_service, "generate_interview_report", original_report)
    retry_resp = await client.post(
        f"/api/interview/{session_id}/complete",
        headers=auth_headers,
    )
    assert retry_resp.status_code == 200
    assert eval_call_count == 1


# ─────────────────────────────────────────────────────────────────────────────
# 4. Conflict Protection (HTTP 409)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_conflict_protection_answer_after_completion(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Attempting PATCH answer on an already completed session

    returns HTTP 409 Conflict ('Session already completed').
    """
    # 1. Start and complete a session
    start_resp = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Database Administrator",
            "job_description": "PostgreSQL replication, backup, query tuning.",
            "num_questions": 2,
        },
        headers=auth_headers,
    )
    session_data = start_resp.json()
    session_id = session_data["id"]
    q1_id = session_data["questions"][0]["id"]

    comp_resp = await client.post(
        f"/api/interview/{session_id}/complete",
        headers=auth_headers,
    )
    assert comp_resp.status_code == 200

    # 2. Attempt to submit an answer after completion
    late_answer_resp = await client.patch(
        f"/api/interview/{session_id}/answer/{q1_id}",
        json={"answer": "This is a late answer attempting to modify a completed session."},
        headers=auth_headers,
    )

    assert late_answer_resp.status_code == 409
    assert late_answer_resp.json()["detail"] == "Session already completed"


@pytest.mark.asyncio
async def test_conflict_protection_complete_after_completion(
    client: httpx.AsyncClient, auth_headers: dict
):
    """Attempting POST complete on an already completed session

    returns HTTP 409 Conflict ('Session already completed').
    """
    # 1. Start and complete a session
    start_resp = await client.post(
        "/api/interview/start",
        json={
            "job_title": "Network Engineer",
            "job_description": "BGP, OSPF, VPN, routing protocols.",
            "num_questions": 2,
        },
        headers=auth_headers,
    )
    session_id = start_resp.json()["id"]

    first_complete = await client.post(
        f"/api/interview/{session_id}/complete",
        headers=auth_headers,
    )
    assert first_complete.status_code == 200

    # 2. Attempt to complete again
    second_complete = await client.post(
        f"/api/interview/{session_id}/complete",
        headers=auth_headers,
    )

    assert second_complete.status_code == 409
    assert second_complete.json()["detail"] == "Session already completed"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Session Isolation
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_session_isolation_get_patch_complete(
    client: httpx.AsyncClient,
    auth_headers: dict,
    auth_headers_for,
    user_factory,
):
    """User B attempting GET, PATCH answer, or POST complete on User A's session

    returns HTTP 404 Not Found.
    """
    # 1. User A creates session
    user_a_resp = await client.post(
        "/api/interview/start",
        json={
            "job_title": "User A Private Role",
            "job_description": "User A proprietary project details.",
            "num_questions": 2,
        },
        headers=auth_headers,
    )
    session_a = user_a_resp.json()
    session_a_id = session_a["id"]
    question_a_id = session_a["questions"][0]["id"]

    # 2. Create User B
    user_b = await user_factory(
        email="user_b_isolation@example.com",
        password="UserBPassword123!",
        full_name="User B",
    )
    headers_b = auth_headers_for(user_b)

    # 3. User B attempts GET User A's session
    get_resp = await client.get(
        f"/api/interview/{session_a_id}",
        headers=headers_b,
    )
    assert get_resp.status_code == 404
    assert get_resp.json()["detail"] == "Session not found"

    # 4. User B attempts PATCH answer on User A's session
    patch_resp = await client.patch(
        f"/api/interview/{session_a_id}/answer/{question_a_id}",
        json={"answer": "User B unauthorized response."},
        headers=headers_b,
    )
    assert patch_resp.status_code == 404
    assert patch_resp.json()["detail"] == "Session not found"

    # 5. User B attempts POST complete on User A's session
    complete_resp = await client.post(
        f"/api/interview/{session_a_id}/complete",
        headers=headers_b,
    )
    assert complete_resp.status_code == 404
    assert complete_resp.json()["detail"] == "Session not found"


@pytest.mark.asyncio
async def test_session_isolation_list_sessions_only_returns_own(
    client: httpx.AsyncClient,
    auth_headers: dict,
    auth_headers_for,
    user_factory,
):
    """User calling GET /api/interview/sessions only lists their own sessions."""
    # User A creates 2 sessions
    await client.post(
        "/api/interview/start",
        json={"job_title": "Role A1", "job_description": "Desc A1", "num_questions": 2},
        headers=auth_headers,
    )
    await client.post(
        "/api/interview/start",
        json={"job_title": "Role A2", "job_description": "Desc A2", "num_questions": 2},
        headers=auth_headers,
    )

    # User B creates 1 session
    user_b = await user_factory(
        email="user_b_listing@example.com",
        password="UserBPassword123!",
        full_name="User B Listing",
    )
    headers_b = auth_headers_for(user_b)

    await client.post(
        "/api/interview/start",
        json={"job_title": "Role B1", "job_description": "Desc B1", "num_questions": 2},
        headers=headers_b,
    )

    # User A checks their sessions
    list_a_resp = await client.get("/api/interview/sessions", headers=auth_headers)
    assert list_a_resp.status_code == 200
    sessions_a = list_a_resp.json()
    assert len(sessions_a) == 2
    titles_a = {s["job_title"] for s in sessions_a}
    assert titles_a == {"Role A1", "Role A2"}

    # User B checks their sessions
    list_b_resp = await client.get("/api/interview/sessions", headers=headers_b)
    assert list_b_resp.status_code == 200
    sessions_b = list_b_resp.json()
    assert len(sessions_b) == 1
    assert sessions_b[0]["job_title"] == "Role B1"


@pytest.mark.asyncio
async def test_unauthenticated_requests_return_401(client: httpx.AsyncClient):
    """All interview endpoints require authentication and reject unauthenticated requests with HTTP 401."""
    resp1 = await client.post(
        "/api/interview/start",
        json={"job_title": "Title", "job_description": "Desc"},
    )
    assert resp1.status_code == 401

    resp2 = await client.get("/api/interview/sessions")
    assert resp2.status_code == 401

    resp3 = await client.get("/api/interview/1")
    assert resp3.status_code == 401

    resp4 = await client.patch("/api/interview/1/answer/1", json={"answer": "Ans"})
    assert resp4.status_code == 401

    resp5 = await client.post("/api/interview/1/complete")
    assert resp5.status_code == 401
