"""
AI Integration for SRP SmartRecruit v3.2
Simple AI helpers (pydantic-ai optional)
"""

from pydantic import BaseModel
from typing import Optional
import random


class ResumeAnalysis(BaseModel):
    """Resume analysis result schema"""
    candidate_name: str
    email: Optional[str] = None
    years_experience: int
    key_skills: list[str]
    education: str
    summary: str
    match_score: float  # 0-100


class JobMatchResult(BaseModel):
    """Job matching result schema"""
    is_suitable: bool
    score: float
    strengths: list[str]
    concerns: list[str]
    recommendation: str


class WritingAssistance(BaseModel):
    """AI writing assistance result"""
    improved_text: str
    suggestions: list[str]
    tone: str


async def analyze_resume(resume_text: str) -> ResumeAnalysis:
    """
    Analyze resume using AI
    
    TODO: Integrate with OpenAI/Anthropic/Gemini using pydantic-ai
    For now, returns mock data - add your API key in .env
    """
    # Mock implementation - replace with actual AI
    return ResumeAnalysis(
        candidate_name="Sample Candidate",
        email="candidate@example.com",
        years_experience=5,
        key_skills=["Python", "FastAPI", "SQL", "React"],
        education="Bachelor's in Computer Science",
        summary="Experienced software engineer with strong backend skills",
        match_score=75.0
    )


async def match_candidate_to_job(
    resume_text: str, 
    job_description: str
) -> JobMatchResult:
    """
    Match candidate profile to job requirements
    
    TODO: Integrate with actual AI API
    For now, uses simple keyword matching + mock scoring
    """
    # Simple keyword-based scoring for demo
    job_keywords = set(job_description.lower().split())
    resume_keywords = set(resume_text.lower().split())
    
    common_keywords = job_keywords & resume_keywords
    score = min(100.0, (len(common_keywords) / len(job_keywords)) * 100 + random.uniform(10, 30))
    
    strengths = [
        "Relevant technical experience",
        "Strong communication skills",
        "Good cultural fit indicators"
    ]
    
    concerns = [
        "May need training in specific tools",
        "Location preferences to be clarified"
    ]
    
    if score >= 75:
        recommendation = "interview"
    elif score >= 50:
        recommendation = "review"
    else:
        recommendation = "reject"
    
    return JobMatchResult(
        is_suitable=(score >= 50),
        score=score,
        strengths=strengths[:2],
        concerns=concerns[:1] if score < 75 else [],
        recommendation=recommendation
    )


async def improve_writing(text: str, context: str = "job description") -> WritingAssistance:
    """
    Improve text using AI writing assistant with OpenAI API
    """
    import openai
    import os
    
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            # Fallback to mock if no API key
            return _mock_improve_writing(text, context)
        
        openai.api_key = api_key
        
        system_prompt = f"""You are a professional recruitment communication expert.
Your task is to improve the provided text for {context}.

Requirements:
1. Maintain the original meaning and intent
2. Improve clarity, professionalism, and impact
3. Fix grammar and spelling errors
4. Enhance tone appropriately

Respond with ONLY valid JSON in this format:
{{
  "improved_text": "The improved version of the text here",
  "suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"],
  "tone": "professional|friendly|formal|casual"
}}

Do not include any explanations outside the JSON."""
        
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please improve this text:\n\n{text}"}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        import json
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()
        
        result_data = json.loads(result_text)
        
        return WritingAssistance(
            improved_text=result_data.get("improved_text", text),
            suggestions=result_data.get("suggestions", []),
            tone=result_data.get("tone", "professional")
        )
    
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        # Fallback to mock
        return _mock_improve_writing(text, context)


def _mock_improve_writing(text: str, context: str = "job description") -> WritingAssistance:
    """Fallback mock improvement when API fails"""
    improved = text.strip()
    if not improved.endswith("."):
        improved += "."
    
    improved = improved[0].upper() + improved[1:] if len(improved) > 1 else improved.upper()
    
    suggestions = [
        "Consider adding more specific details about requirements",
        "Use active voice to strengthen the message",
        f"Add concrete examples relevant to {context}"
    ]
    
    return WritingAssistance(
        improved_text=improved,
        suggestions=suggestions,
        tone="professional"
    )
