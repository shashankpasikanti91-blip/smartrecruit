"""
JD Intelligence Service — SRP SmartRecruit v4.0
Generates professional JDs and analyses existing JDs
"""

from __future__ import annotations
import json
import logging
import os
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.enterprise import GeneratedJD, JDAnalysisResult
from app.models.user import User

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# System prompts
# ─────────────────────────────────────────────────────────────────────────────

_JD_GENERATOR_PROMPT = """You are a senior recruitment consultant and professional JD writer.

Your task is to write a complete, human-quality Job Description based on the inputs provided.

STRICT RULES:
- Write in clear, professional, human tone
- No robotic AI language
- No exaggerated claims ("world-class", "ninja", "rockstar")
- No fake promises ("exciting opportunity", "competitive salary" without details)
- Be factual and realistic
- Structure must be complete and scannable

JD STRUCTURE (MANDATORY — all sections required):
1. Job Title
2. Role Summary (3-4 sentences about the role purpose)
3. Key Responsibilities (6-10 bullet points)
4. Required Skills (5-8 must-have items)
5. Preferred / Nice-to-Have Skills (3-5 items)
6. Experience Required
7. Education
8. Employment Type (Full-Time / Part-Time / Contract)
9. Location
10. Notice Period Preference (if provided)
11. Compensation (if provided — otherwise omit this section entirely)
12. About the Company (if provided — otherwise omit)

OUTPUT FORMAT:
Return JSON ONLY. No markdown. No extra text.
{
  "job_title": "",
  "role_summary": "",
  "responsibilities": [],
  "required_skills": [],
  "preferred_skills": [],
  "experience": "",
  "education": "",
  "employment_type": "",
  "location": "",
  "notice_period": "",
  "compensation": "",
  "about_company": "",
  "full_jd_text": "Complete formatted JD as a single text block"
}"""


_JD_ANALYZER_PROMPT = """You are a senior recruitment intelligence analyst.

Given a Job Description, extract structured intelligence that helps a recruiter:
1. Understand exactly what is required
2. Build effective boolean search strings
3. Screen candidates faster

ANALYZE AND RETURN:
- must_have_skills: non-negotiable technical and domain skills
- nice_to_have_skills: preferred but optional skills
- alternate_titles: other job titles for this type of role
- skill_clusters: group related skills (e.g. {\"Frontend\": [\"React\",\"JavaScript\"], \"Backend\": [\"Python\",\"FastAPI\"]})
- suggested_questions: 5-8 relevant screening questions
- experience_range: min and max experience
- seniority_level: junior / mid / senior / lead / manager / executive
- key_responsibilities: top 5 responsibilities extracted
- must_exclude: clear disqualifiers mentioned or implied

OUTPUT FORMAT:
Return JSON ONLY. No markdown. No extra text.
{
  "job_title": "",
  "seniority_level": "",
  "experience_range": {"min": 0, "max": 0},
  "must_have_skills": [],
  "nice_to_have_skills": [],
  "alternate_titles": [],
  "skill_clusters": {},
  "key_responsibilities": [],
  "suggested_questions": [],
  "must_exclude": [],
  "domain": "",
  "industry_hints": []
}"""


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_openai_client():
    api_key  = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", None)
    if not api_key:
        return None, None
    from openai import OpenAI
    kwargs: dict[str, Any] = {"api_key": api_key, "timeout": 120.0}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs), os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _parse_json_response(raw: str) -> dict:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class JDService:

    @staticmethod
    def generate_jd(
        db: Session,
        current_user: User,
        params: dict,
    ) -> GeneratedJD:
        """
        Generate a full professional JD from structured input.

        params keys: job_title, skills, experience, education, location,
                     employment_type, salary, industry, company_name,
                     notice_period, responsibilities (optional free-text)
        """
        client, model = _build_openai_client()
        if not client:
            raise RuntimeError("OPENAI_API_KEY not configured")

        user_message = (
            f"Job Title: {params.get('job_title', 'Not specified')}\n"
            f"Skills Required: {', '.join(params.get('skills', [])) or 'Not specified'}\n"
            f"Experience: {params.get('experience', 'Not specified')}\n"
            f"Education: {params.get('education', 'Not specified')}\n"
            f"Location: {params.get('location', 'Not specified')}\n"
            f"Employment Type: {params.get('employment_type', 'Full-Time')}\n"
            f"Salary / Compensation: {params.get('salary', 'Not provided')}\n"
            f"Industry: {params.get('industry', 'Not specified')}\n"
            f"Company Name: {params.get('company_name', 'Not provided')}\n"
            f"Notice Period: {params.get('notice_period', 'Not specified')}\n"
        )

        extra = params.get("additional_notes", "").strip()
        if extra:
            user_message += f"\nAdditional Notes from Recruiter:\n{extra}"

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _JD_GENERATOR_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.4,
            max_tokens=2000,
        )
        raw = response.choices[0].message.content or "{}"
        structured = _parse_json_response(raw)

        record = GeneratedJD(
            user_id         = current_user.id,
            title           = params.get("job_title", "Untitled"),
            input_params    = params,
            full_jd_text    = structured.get("full_jd_text", raw),
            structured_data = structured,
            version         = 1,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info("JD generated id=%s user=%s", record.id, current_user.id)
        return record

    # -------------------------------------------------------------------------

    @staticmethod
    def analyze_jd(
        db: Session,
        current_user: User,
        jd_text: str,
    ) -> JDAnalysisResult:
        """
        Analyse an existing JD to extract intelligence.
        Returns skills, questions, alternate titles, clusters, etc.
        """
        client, model = _build_openai_client()
        if not client:
            raise RuntimeError("OPENAI_API_KEY not configured")

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _JD_ANALYZER_PROMPT},
                {"role": "user",   "content": f"ANALYZE THIS JD:\n\n{jd_text}"},
            ],
            temperature=0.2,
            max_tokens=1500,
        )
        raw = response.choices[0].message.content or "{}"
        structured = _parse_json_response(raw)

        record = JDAnalysisResult(
            user_id             = current_user.id,
            source_jd_text      = jd_text,
            must_have_skills    = structured.get("must_have_skills", []),
            nice_to_have_skills = structured.get("nice_to_have_skills", []),
            alternate_titles    = structured.get("alternate_titles", []),
            skill_clusters      = structured.get("skill_clusters", {}),
            suggested_questions = structured.get("suggested_questions", []),
            screening_criteria  = {
                k: structured.get(k)
                for k in ("seniority_level", "experience_range", "key_responsibilities",
                          "must_exclude", "domain", "industry_hints", "job_title")
            },
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info("JD analysed id=%s user=%s", record.id, current_user.id)
        return record

    # -------------------------------------------------------------------------

    @staticmethod
    def get_jd(db: Session, current_user: User, jd_id: int) -> Optional[GeneratedJD]:
        return (
            db.query(GeneratedJD)
            .filter(GeneratedJD.id == jd_id, GeneratedJD.user_id == current_user.id)
            .first()
        )

    @staticmethod
    def list_jds(db: Session, current_user: User, limit: int = 20) -> list[GeneratedJD]:
        return (
            db.query(GeneratedJD)
            .filter(GeneratedJD.user_id == current_user.id)
            .order_by(GeneratedJD.created_at.desc())
            .limit(limit)
            .all()
        )
