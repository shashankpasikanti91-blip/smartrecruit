"""
Boolean Search Service — SRP SmartRecruit v4.0
Generates recruiter-ready boolean search strings from JD or job title + skills
"""

from __future__ import annotations
import json
import logging
import os
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.enterprise import GeneratedBooleanSearch
from app.models.user import User

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# System prompt
# ─────────────────────────────────────────────────────────────────────────────

_BOOLEAN_SEARCH_PROMPT = """You are an expert Boolean Search Engineer for recruitment.

Your task is to read the provided job input (JD, title, or skill list) and generate professional,
recruiter-optimized Boolean search strings for LinkedIn, Naukri, and Indeed.

RULES:
- Extract must-have and nice-to-have keywords accurately
- Short boolean: compact string for quick searches (< 120 chars target)
- Advanced boolean: detailed with AND/OR/NOT logic, parentheses grouping
- Alternate boolean: variant using synonym and alternate role titles
- LinkedIn format: uses LinkedIn X-Ray or Recruiter syntax
- Naukri format: Naukri-compatible search query
- Include suggested exclude keywords (competitors, irrelevant roles)

OUTPUT FORMAT:
Return JSON ONLY. No markdown. No extra text.

{
  "job_title": "",
  "must_have_keywords": [],
  "nice_to_have_keywords": [],
  "exclude_keywords": [],
  "alternate_titles": [],
  "short_boolean": "",
  "advanced_boolean": "",
  "alternate_boolean": "",
  "linkedin_search": "",
  "naukri_search": "",
  "indeed_search": "",
  "notes": ""
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
    kwargs: dict[str, Any] = {"api_key": api_key, "timeout": 90.0}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs), os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _parse_json(raw: str) -> dict:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return json.loads(text)


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class BooleanSearchService:

    @staticmethod
    def generate(
        db: Session,
        current_user: User,
        params: dict,
    ) -> GeneratedBooleanSearch:
        """
        Generate boolean search strings.

        params keys: job_title (required), skills (list), experience,
                     jd_text (optional full JD text), location,
                     source_jd_id (optional int)
        """
        client, model = _build_openai_client()
        if not client:
            raise RuntimeError("OPENAI_API_KEY not configured")

        job_title = params.get("job_title", "")
        skills    = params.get("skills", [])
        jd_text   = params.get("jd_text", "")
        experience = params.get("experience", "")

        if jd_text:
            user_message = (
                f"Job Title: {job_title}\n\n"
                f"FULL JD:\n{jd_text}"
            )
            input_text = jd_text
        else:
            user_message = (
                f"Job Title: {job_title}\n"
                f"Required Skills: {', '.join(skills)}\n"
                f"Experience: {experience}\n"
                f"Location: {params.get('location', '')}"
            )
            input_text = user_message

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _BOOLEAN_SEARCH_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.2,
            max_tokens=1200,
        )
        raw = response.choices[0].message.content or "{}"
        structured = _parse_json(raw)

        record = GeneratedBooleanSearch(
            user_id          = current_user.id,
            source_jd_id     = params.get("source_jd_id"),
            job_title        = job_title or structured.get("job_title", ""),
            input_text       = input_text,
            must_have        = structured.get("must_have_keywords", skills),
            nice_to_have     = structured.get("nice_to_have_keywords", []),
            exclude_keywords = structured.get("exclude_keywords", []),
            short_boolean    = structured.get("short_boolean", ""),
            advanced_boolean = structured.get("advanced_boolean", ""),
            alternate_boolean = structured.get("alternate_boolean", ""),
            linkedin_search  = structured.get("linkedin_search", ""),
            naukri_search    = structured.get("naukri_search", ""),
            indeed_search    = structured.get("indeed_search", ""),
            structured_data  = structured,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info("Boolean search generated id=%s user=%s", record.id, current_user.id)
        return record

    # -------------------------------------------------------------------------

    @staticmethod
    def get(
        db: Session,
        current_user: User,
        search_id: int,
    ) -> Optional[GeneratedBooleanSearch]:
        return (
            db.query(GeneratedBooleanSearch)
            .filter(
                GeneratedBooleanSearch.id == search_id,
                GeneratedBooleanSearch.user_id == current_user.id,
            )
            .first()
        )

    @staticmethod
    def list(
        db: Session,
        current_user: User,
        limit: int = 20,
    ) -> list[GeneratedBooleanSearch]:
        return (
            db.query(GeneratedBooleanSearch)
            .filter(GeneratedBooleanSearch.user_id == current_user.id)
            .order_by(GeneratedBooleanSearch.created_at.desc())
            .limit(limit)
            .all()
        )
