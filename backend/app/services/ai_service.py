import json
import asyncio
import re
import httpx
from typing import List, Dict, Any

from app.core.config import settings

# Shared async HTTP client — reuses connection pool across all AI calls
_http_client = httpx.AsyncClient(timeout=120.0)


# ─── Groq Cloud API Client ───────────────────────────────────────────────────

async def _groq_generate(prompt: str, temperature: float = 0.7, max_retries: int = 2) -> str:
    """Send a prompt to Groq's OpenAI-compatible API and return the generated text."""
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set in environment variables.")

    url = f"{settings.GROQ_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 4096,
    }

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = await _http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                await asyncio.sleep(1)

    raise RuntimeError(f"Groq request failed after {max_retries + 1} attempts: {last_error}")


def _parse_json_response(text: str) -> Any:
    """Extract JSON from model response."""
    text = text.strip()

    # Strip markdown code fences
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    # Strategy 1: Direct parse
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # Strategy 2: Find a JSON object { ... }
    obj_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if obj_match:
        try:
            return json.loads(obj_match.group(1))
        except (json.JSONDecodeError, ValueError):
            pass

    # Strategy 3: Find a JSON array [ ... ]
    arr_match = re.search(r"(\[.*\])", text, re.DOTALL)
    if arr_match:
        try:
            result = json.loads(arr_match.group(1))
            if isinstance(result, list) and result and isinstance(result[0], list):
                return [item for sublist in result for item in sublist]
            return result
        except (json.JSONDecodeError, ValueError):
            pass

    raise ValueError(f"Could not extract JSON from response: {text[:300]}")


async def _generate_json(prompt: str, temperature: float = 0.4) -> Any:
    """Generate a response and parse it as JSON, with one retry on parse failure."""
    for attempt in range(2):
        raw = await _groq_generate(prompt, temperature=temperature)
        try:
            return _parse_json_response(raw)
        except (json.JSONDecodeError, ValueError):
            if attempt == 0:
                # Retry with a stricter prompt addition
                prompt = prompt + "\n\nIMPORTANT: You MUST return ONLY valid JSON. No extra text."
            else:
                raise ValueError(
                    f"Failed to parse JSON from model response after 2 attempts. Raw: {raw[:500]}"
                )


# ─── CV Optimization — 2 calls total ───────────────────────────────────────

async def _analyze_cv_in_one_shot(
    cv_text: str, job_title: str, job_description: str
) -> Dict[str, Any]:
    """Single call: extract keywords, score match, and generate suggestions all at once."""
    prompt = f"""You are a professional CV reviewer and career coach.

Analyze the CV below for the given job and return ONLY valid JSON with this exact structure:
{{
  "match_score": <number 0-100>,
  "job_keywords": ["keyword1", "keyword2"],
  "missing_keywords": ["missing1", "missing2"],
  "suggestions": ["suggestion1", "suggestion2", "suggestion3", "suggestion4"]
}}

Job Title: {job_title}
Job Description (first 1000 chars): {job_description[:1000]}

CV (first 1500 chars):
{cv_text[:1500]}"""

    return await _generate_json(prompt)


async def _rewrite_cv(
    cv_text: str, suggestions: List[str], job_title: str, missing_keywords: List[str]
) -> str:
    """Single call: rewrite the CV based on analysis results."""
    suggestions_str = "\n".join(f"- {s}" for s in suggestions[:4])
    keywords_str = ", ".join(missing_keywords[:8]) if missing_keywords else "none"

    prompt = f"""You are a professional CV writer. Rewrite this CV to be better optimized for a {job_title} position.

Rules:
- Keep all information truthful, only improve phrasing, structure, and emphasis
- Naturally incorporate these missing keywords where honest: {keywords_str}
- Apply these improvements:
{suggestions_str}

Return ONLY the rewritten CV text. No JSON, no markdown fences, just the CV text.

Original CV:
{cv_text[:2500]}"""

    return await _groq_generate(prompt, temperature=0.6)


async def optimize_cv(cv_text: str, job_title: str, job_description: str) -> Dict[str, Any]:
    """
    Optimize CV using 2 API calls (was 4):
    Call 1: analyze + score + keywords + suggestions
    Call 2: rewrite based on analysis
    """
    # Call 1: Analysis
    analysis = await _analyze_cv_in_one_shot(cv_text, job_title, job_description)

    match_score = analysis.get("match_score", 50)
    missing_keywords = analysis.get("missing_keywords", [])
    suggestions = analysis.get("suggestions", [])

    # Call 2: Rewrite
    optimized_text = await _rewrite_cv(cv_text, suggestions, job_title, missing_keywords)

    key_improvements = suggestions[:4] if suggestions else ["Improved keyword alignment"]

    return {
        "optimized_text": optimized_text.strip(),
        "match_score": match_score,
        "suggestions": suggestions,
        "key_improvements": key_improvements,
        "missing_keywords": missing_keywords,
    }


# ─── Interview Question Generation — 1 call total ───────────────────────────

async def generate_interview_questions(
    job_title: str,
    job_description: str,
    num_questions: int = 8,
) -> List[Dict[str, Any]]:
    """
    Generate categorised interview questions in a single API call.
    Each question has: question_text, category, order_index
    """
    behavioral_count = max(1, num_questions // 3)
    technical_count = max(1, num_questions // 3)
    situational_count = max(1, num_questions - behavioral_count - technical_count)

    prompt = f"""You are an interview coach. Generate exactly {num_questions} interview questions for a {job_title} position.
Job context: {job_description[:700]}

Return ONLY a JSON array with exactly {num_questions} questions:
[
  {{"question_text": "Your question?", "category": "behavioral|technical|situational"}}
]

Include:
- {behavioral_count} behavioral questions
- {technical_count} technical questions
- {situational_count} situational questions"""

    result = await _generate_json(prompt)
    questions = result if isinstance(result, list) else []

    all_questions = []
    for i, q in enumerate(questions):
        all_questions.append({
            "order_index": i + 1,
            "question_text": q.get("question_text", "Tell me about yourself."),
            "category": q.get("category", "behavioral"),
        })

    if not all_questions:
        all_questions.append({
            "order_index": 1,
            "question_text": f"Tell me about your experience relevant to the {job_title} role.",
            "category": "behavioral",
        })

    return all_questions


# ─── Answer Evaluation (focused single-task prompt) ──────────────────────────

async def evaluate_answer(
    question_text: str,
    category: str,
    user_answer: str,
    job_title: str,
    job_description: str,
) -> Dict[str, Any]:
    """
    Evaluate a candidate's answer with a focused prompt.
    Returns: score, feedback, strengths, improvements, model_answer_hint
    """
    prompt = f"""You are an interview coach. Evaluate the candidate's answer to this {category} question for a {job_title} role.

Question: {question_text}
Answer: {user_answer}

Score from 0-100 and give feedback.

Return ONLY valid JSON:
{{
  "score": <number 0-100>,
  "feedback": "2-3 sentence feedback",
  "strengths": ["strength 1", "strength 2"],
  "improvements": ["improvement 1", "improvement 2"],
  "model_answer_hint": "brief hint about what an ideal answer includes"
}}"""

    return await _generate_json(prompt)


# ─── Session Report — 1 call total ──────────────────────────────────────────

async def generate_interview_report(
    job_title: str,
    questions_with_answers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generate performance report in a single API call (was 2).
    Returns: summary_feedback, category_scores, top_strengths, top_improvements
    """
    # Calculate category scores directly (no LLM needed)
    category_scores = {"behavioral": None, "technical": None, "situational": None}
    for cat in category_scores:
        cat_scores = [
            q.get("score", 0) for q in questions_with_answers
            if q.get("category") == cat and q.get("score") is not None
        ]
        if cat_scores:
            category_scores[cat] = round(sum(cat_scores) / len(cat_scores), 1)

    # Build compact QA summary (limit tokens)
    qa_text = "\n".join(
        f"Q{i+1}[{q['category']}]: {q['question_text'][:100]} | Score:{q.get('score',0)}/100"
        for i, q in enumerate(questions_with_answers)
    )

    prompt = f"""You are an interview coach reviewing a {job_title} mock interview.

{qa_text}

Return ONLY valid JSON:
{{
  "summary_feedback": "3-4 sentence overall performance summary",
  "top_strengths": ["strength 1", "strength 2", "strength 3"],
  "top_improvements": ["improvement 1", "improvement 2", "improvement 3"]
}}"""

    result = await _generate_json(prompt)

    if not isinstance(result, dict):
        result = {
            "summary_feedback": "Interview session completed. Review your individual question scores for detailed feedback.",
            "top_strengths": ["Completed the interview session"],
            "top_improvements": ["Practice more with mock interviews"],
        }

    return {
        "summary_feedback": result.get("summary_feedback", "Session complete."),
        "category_scores": category_scores,
        "top_strengths": result.get("top_strengths", []),
        "top_improvements": result.get("top_improvements", []),
    }
