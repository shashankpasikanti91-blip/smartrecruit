"""
Screening Agent for Resume-to-JD Matching
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from openai import OpenAI
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class ScreeningAgent:
    """AI agent for screening candidates against job descriptions"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-mini"):
        """Initialize screening agent"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        logger.info(f"Screening agent initialized with model: {model}")
    
    def _build_screening_prompt(self, resume_text: str, jd_text: str) -> str:
        """Build screening prompt for Claude"""
        return f"""You are an expert recruiter with years of experience in candidate evaluation.

Analyze the following resume against the job description and provide a comprehensive screening evaluation.

=== JOB DESCRIPTION ===
{jd_text}

=== RESUME ===
{resume_text}

=== EVALUATION CRITERIA ===

Analyze and score on these dimensions (0-1 scale):
1. Experience Match: Does candidate have required years of experience?
2. Skills Match: How many required skills does candidate possess?
3. Education Match: Does candidate meet education requirements?
4. Cultural Fit: Does candidate's background align with role?
5. Growth Potential: Can candidate grow into this role?

=== RESPONSE FORMAT ===

Provide your response as a JSON object with the following structure:
{{
    "overall_score": 0.85,
    "recommendation": "strong_match",
    "required_skills_match": 0.9,
    "optional_skills_match": 0.7,
    "experience_score": 0.8,
    "education_match": 0.95,
    "cultural_fit_score": 0.8,
    "growth_potential": 0.75,
    "score_breakdown": {{
        "experience": 0.8,
        "skills": 0.85,
        "education": 0.95,
        "soft_skills": 0.75,
        "culture_fit": 0.8
    }},
    "matched_required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "missing_required_skills": ["Kubernetes"],
    "matched_preferred_skills": ["Docker", "Redis"],
    "strengths": [
        "5+ years of Python development experience",
        "Strong backend system design",
        "Leadership experience with junior developers"
    ],
    "weaknesses": [
        "Limited cloud infrastructure experience",
        "No FastAPI specific experience but has Django background"
    ],
    "gaps": [
        "Kubernetes orchestration",
        "Microservices architecture (some experience but not deep)"
    ],
    "summary": "Strong candidate with relevant experience. Main gap is Kubernetes which can be learned quickly.",
    "recommended_action": "proceed",
    "recommended_questions": [
        "Tell us about your experience with Kubernetes",
        "How would you design a scalable microservices architecture?",
        "Describe your leadership approach with junior developers"
    ],
    "confidence_score": 0.85,
    "notes": "Candidate has strong fundamentals. Recommend technical round."
}}

Important:
- Provide only valid JSON
- Be objective and data-driven
- Focus on job requirements
- No explanatory text outside the JSON
"""
    
    def screen_candidate(
        self,
        resume_text: str,
        jd_text: str,
        candidate_id: Optional[str] = None,
        jd_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Screen candidate against job description"""
        try:
            if not resume_text or not jd_text:
                raise ValueError("Resume and JD text must be provided")
            
            # Build prompt
            prompt = self._build_screening_prompt(resume_text, jd_text)
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Low temperature for consistency
                timeout=30
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            # Handle markdown code blocks
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            result = json.loads(response_text.strip())
            
            # Add metadata
            result["id"] = candidate_id or str(uuid.uuid4())
            result["candidate_id"] = candidate_id
            result["jd_id"] = jd_id
            result["screening_method"] = "ai"
            result["screened_by"] = self.model
            result["created_at"] = datetime.utcnow().isoformat()
            result["processing_time_seconds"] = response.usage.prompt_tokens / 100  # Rough estimate
            
            logger.info(f"Screened candidate {candidate_id} with score {result.get('overall_score', 0)}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            raise ValueError(f"AI response was not valid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error screening candidate: {str(e)}")
            raise
    
    def batch_screen(
        self,
        candidates: List[Dict[str, str]],
        jd_text: str
    ) -> List[Dict[str, Any]]:
        """Screen multiple candidates against same JD"""
        results = []
        
        for candidate in candidates:
            try:
                result = self.screen_candidate(
                    resume_text=candidate.get("resume_text", ""),
                    jd_text=jd_text,
                    candidate_id=candidate.get("id"),
                    jd_id=candidate.get("jd_id")
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error screening candidate {candidate.get('id')}: {str(e)}")
                results.append({
                    "id": candidate.get("id"),
                    "error": str(e),
                    "overall_score": 0,
                    "recommendation": "error"
                })
        
        logger.info(f"Batch screened {len(candidates)} candidates")
        return results
