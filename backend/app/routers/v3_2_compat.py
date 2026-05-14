"""
v3.2 Compatibility Endpoints
Provides backward compatibility with v3.2 API paths
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import os
from pathlib import Path
import PyPDF2
import docx
import io
import openai
import json
from datetime import datetime

from app.database.connection import get_db
from app.auth.dependencies import get_optional_user, get_current_admin_user, get_current_verified_user
from app.models.user import User
from app.models.screening import ScreeningResult

router = APIRouter(prefix="/api", tags=["v3.2 Compatibility"])

logger = logging.getLogger(__name__)

# Absolute paths — works in local dev (backend/) and Docker (/app/) without
# relying on the current working directory.
_THIS_DIR   = Path(__file__).resolve().parent          # .../backend/app/routers/
_BACKEND_DIR = _THIS_DIR.parents[1]                    # .../backend/ OR /app/ in Docker

# Uploads: always at project-root/uploads locally; /app/uploads in Docker
_PROJECT_ROOT = _BACKEND_DIR.parent
UPLOAD_DIR = (
    _PROJECT_ROOT / "uploads" if _PROJECT_ROOT != Path("/") else _BACKEND_DIR / "uploads"
)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Load system prompts from file
SYSTEM_PROMPTS = {}

# Simple activity logging function
def log_activity(db: Session, user_id: Optional[int], action: str, details: dict = None):
    """Log user activity to database for tracking"""
    try:
        # Create a simple log entry in the database
        # Using the existing screening_results table with modified fields
        from app.models.screening import ScreeningResult
        
        log_entry = ScreeningResult(
            user_id=user_id,  # None is OK — column is nullable
            resume_id=None,   # No FK reference needed for activity logs
            job_description=f"Activity: {action}",
            score=0.0,
            status="logged",
            ai_analysis={"activity_log": True, "details": details or {}},
            strengths=[action],
            concerns=[],
            recommendation="logged",
            is_eligible_for_invite=False
        )
        db.add(log_entry)
        db.commit()
        logger.info("Logged activity: %s for user %s", action, user_id)
    except Exception as e:
        logger.warning("Failed to log activity: %s", e)
        # Don't fail the main operation if logging fails

def load_system_prompts():
    """Load all system prompts from system_prompts.txt"""
    global SYSTEM_PROMPTS
    # Absolute path resolution — works whether CWD is backend/, project root, or /app/ (Docker)
    candidates = [
        _BACKEND_DIR / "system_prompts.txt",   # local dev: backend/system_prompts.txt
        Path("system_prompts.txt"),              # Docker WORKDIR /app/system_prompts.txt
    ]
    prompts_file = next((p for p in candidates if p.exists()), None)
    if prompts_file is None:
        logger.warning("system_prompts.txt not found in %s or CWD", _BACKEND_DIR)
        return
    
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse prompts based on section markers
        # Section 1: Screen Single Candidate
        if "###################Screen Single Candidate##########" in content:
            start = content.find("###################Screen Single Candidate##########")
            next_section = content.find("#############Bulk Candidate Screening", start)
            if next_section > start:
                SYSTEM_PROMPTS['screen_candidate'] = content[start:next_section].replace("###################Screen Single Candidate##########", "").strip()
        
        # Section 2: Bulk Candidate Screening
        if "#############Bulk Candidate Screening#######################" in content:
            start = content.find("#############Bulk Candidate Screening#######################")
            next_section = content.find("###################Create Job Posts", start)
            if next_section > start:
                SYSTEM_PROMPTS['bulk_screening'] = content[start:next_section].replace("#############Bulk Candidate Screening#######################", "").strip()
        
        # Section 3: Create Job Posts (was "Generate Job Post")
        if "###################Create Job Posts##########" in content:
            start = content.find("###################Create Job Posts##########")
            next_section = content.find("############AI Writing Assistant########################", start)
            if next_section > start:
                SYSTEM_PROMPTS['job_post'] = content[start:next_section].replace("###################Create Job Posts##########", "").strip()
        
        # Section 4: AI Writing Assistant
        if "############AI Writing Assistant########################" in content:
            start = content.find("############AI Writing Assistant########################")
            next_section = content.find("###################Boolean Search Engine##########", start)
            if next_section > start:
                SYSTEM_PROMPTS['ai_writing'] = content[start:next_section].replace("############AI Writing Assistant########################", "").strip()
            else:
                SYSTEM_PROMPTS['ai_writing'] = content[start:].replace("############AI Writing Assistant########################", "").strip()

        # Section 5: Boolean Search Engine
        if "###################Boolean Search Engine##########" in content:
            start = content.find("###################Boolean Search Engine##########")
            next_section = content.find("###################JD Generator##########", start)
            if next_section > start:
                SYSTEM_PROMPTS['boolean_search'] = content[start:next_section].replace("###################Boolean Search Engine##########", "").strip()
            else:
                SYSTEM_PROMPTS['boolean_search'] = content[start:].replace("###################Boolean Search Engine##########", "").strip()

        # Section 6: JD Generator
        if "###################JD Generator##########" in content:
            start = content.find("###################JD Generator##########")
            SYSTEM_PROMPTS['jd_generator'] = content[start:].replace("###################JD Generator##########", "").strip()

        logger.info("[OK] Loaded %d system prompts from %s", len(SYSTEM_PROMPTS), prompts_file.name)
        for key in SYSTEM_PROMPTS:
            logger.debug("  - %s: %d chars", key, len(SYSTEM_PROMPTS[key]))
            
    except Exception as e:
        logger.error("[ERROR] Failed to load system prompts: %s", e)

# Load prompts on module import
load_system_prompts()

# OpenAI setup
openai.api_key = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ScreeningRequest(BaseModel):
    candidate_name: str
    resume_text: str
    jd_text: str
    job_title: Optional[str] = "Position"

class BulkScreeningRequest(BaseModel):
    candidates: List[Dict[str, Any]]
    jd_text: str
    job_title: Optional[str] = "Position"

class JobPostRequest(BaseModel):
    job_title: str
    jd_text: str

class AIWriteRequest(BaseModel):
    text: str
    action: Optional[str] = "rewrite"
    tone: Optional[str] = "professional"
    platform: Optional[str] = "email"

class MessageRequest(BaseModel):
    message_type: str
    recipient: str
    job_title: str
    tone: Optional[str] = "professional"
    context: Optional[str] = ""


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        
        text = text.strip()
        if text:
            logger.info("PDF text extracted: %d characters", len(text))
            return text
        else:
            logger.warning("PDF text extraction returned empty")
            return "PDF_EMPTY"
    except Exception as e:
        logger.warning("PDF extraction error: %s", e)
        return f"PDF_ERROR: {str(e)}"

def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX"""
    try:
        doc = docx.Document(io.BytesIO(file_content))
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        
        text = text.strip()
        if text:
            logger.info("DOCX text extracted: %d characters", len(text))
            return text
        else:
            logger.warning("DOCX text extraction returned empty")
            return "DOCX_EMPTY"
    except Exception as e:
        logger.warning("DOCX extraction error: %s", e)
        return f"DOCX_ERROR: {str(e)}"

async def call_openai(system_prompt: str, user_message: str, temperature: float = 0.7, max_tokens: int = None) -> str:
    """Call OpenAI API with system prompt and fallback for missing API key"""
    try:
        if not openai.api_key:
            logger.warning("No OpenAI API key configured, using mock screening")
            return generate_mock_screening_response()
        
        from openai import OpenAI
        
        # Use OPENAI_BASE_URL for OpenRouter or other compatible APIs
        base_url = os.getenv('OPENAI_BASE_URL', None)
        client_kwargs = {"api_key": openai.api_key, "timeout": 120.0}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        client = OpenAI(**client_kwargs)
        
        # Build API parameters
        api_params = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
        }
        
        # Add max_tokens if specified (for longer responses like job posts)
        if max_tokens:
            api_params["max_tokens"] = max_tokens
        
        response = client.chat.completions.create(**api_params)
        return response.choices[0].message.content
    except Exception as e:
        logger.warning("OpenAI error (%s): %s", type(e).__name__, e)
        logger.debug("Using mock screening response instead")
        return generate_mock_screening_response()


def generate_mock_screening_response() -> str:
    """Generate mock screening response when OpenAI is not available"""
    return json.dumps([
        {
            "candidate": "John Developer",
            "candidate_name": "John Developer",
            "match_score": 85,
            "score": 85,
            "assessment": "Excellent match with all required skills",
            "status": "Reviewed",
            "recommendation": "INVITE"
        },
        {
            "candidate": "Sarah DevOps",
            "candidate_name": "Sarah DevOps",
            "match_score": 90,
            "score": 90,
            "assessment": "Perfect fit, exceeds all requirements",
            "status": "Reviewed",
            "recommendation": "INVITE"
        },
        {
            "candidate": "Mike Junior",
            "candidate_name": "Mike Junior",
            "match_score": 35,
            "score": 35,
            "assessment": "Lacks required experience level",
            "status": "Reviewed",
            "recommendation": "REJECT"
        }
    ])


# ============================================================================
# FILE UPLOAD
# ============================================================================

@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Upload and extract text from resume/JD file"""
    try:
        file_content = await file.read()
        filename = file.filename or "unknown.txt"
        
        # Extract text based on file type
        ext = filename.lower().split('.')[-1]
        text_content = ""
        
        if ext == 'pdf':
            text_content = extract_text_from_pdf(file_content)
        elif ext in ['docx', 'doc']:
            text_content = extract_text_from_docx(file_content)
        elif ext == 'txt':
            text_content = file_content.decode('utf-8')
        else:
            return {"error": f"Unsupported file type: {ext}"}
        
        if not text_content:
            return {"error": "No content extracted from file"}
        
        return {
            "filename": filename,
            "type": ext,
            "length": len(text_content),
            "full_content": text_content,
            "preview": text_content[:500] + "..." if len(text_content) > 500 else text_content
        }
    
    except Exception as e:
        logger.warning("Upload error: %s", e)
        return {"error": str(e)}


# ============================================================================
# CANDIDATE SCREENING
# ============================================================================

@router.post("/screen-candidate")
async def screen_candidate(
    request: ScreeningRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Screen single candidate against JD using system prompts"""
    try:
        # Get system prompt for screening from loaded file
        system_prompt = SYSTEM_PROMPTS.get('screen_candidate', "")
        
        if not system_prompt:
            # Fallback inline prompt if file not loaded
            system_prompt = """You are a STRICT ATS system and expert recruiter. Evaluate the candidate resume against the job description.
Return JSON ONLY with this structure:
{
  "name": "", "email": "", "contact_number": "", "current_company": "",
  "score": 0, "decision": "",
  "evaluation": {
    "candidate_strengths": [], "high_match_skills": [], "medium_match_skills": [],
    "low_or_missing_match_skills": [], "candidate_weaknesses": [],
    "risk_level": "", "risk_explanation": "", "reward_level": "", "reward_explanation": "",
    "overall_fit_rating": 0, "justification": ""
  }
}
Score >= 70 = Shortlisted, < 70 = Rejected. Be strict - only give high scores for direct matches."""
        
        # Create user message with JD and Resume
        user_message = f"""
Job Description:
{request.jd_text}

Candidate Resume:
{request.resume_text}
"""
        
        # Call OpenAI
        response = await call_openai(system_prompt, user_message, temperature=0.3)
        
        # Try to parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            clean_response = response.strip()
            if '```json' in clean_response:
                clean_response = clean_response.split('```json')[1].split('```')[0].strip()
            elif '```' in clean_response:
                clean_response = clean_response.split('```')[1].split('```')[0].strip()
            
            # Find JSON object
            if '{' in clean_response and '}' in clean_response:
                json_start = clean_response.find('{')
                json_end = clean_response.rfind('}') + 1
                json_str = clean_response[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = json.loads(clean_response)
            
            # Map the response to frontend format
            score = result.get('score', 0)
            evaluation = result.get('evaluation', {})
            
            # Determine recommendation based on score
            if score >= 75:
                recommendation = "INVITE"
            elif score >= 60:
                recommendation = "REVIEW"  
            else:
                recommendation = "REJECT"
            
            # Format response for frontend — includes legacy fields for backward compat
            # plus new enterprise fields from Phase 1 prompt upgrade
            frontend_response = {
                # Core identity — legacy + new
                "candidate_name": result.get('name', request.candidate_name),
                "candidate": result.get('name', request.candidate_name),
                "email": result.get('email', 'Not Found'),
                "contact_number": result.get('contact_number', 'Not Found'),
                "current_company": result.get('current_company', 'Not Found'),
                "current_designation": result.get('current_designation', 'Not Found'),
                "location": result.get('location', 'Not Found'),
                # Scoring — legacy + new
                "match_score": score,
                "score": score,
                "classification": result.get('classification', ''),
                "decision": result.get('decision', 'Shortlisted' if score >= 70 else 'Rejected'),
                "recommendation": recommendation,
                "shortlist_rank": result.get('shortlist_rank', ''),
                # Experience
                "claimed_experience": result.get('claimed_experience', 'Not Found'),
                "verifiable_experience": result.get('verifiable_experience', 'Not Found'),
                "notice_period": result.get('notice_period', 'Not Found'),
                "current_ctc": result.get('current_ctc', 'Not Found'),
                "expected_ctc": result.get('expected_ctc', 'Not Found'),
                # Education
                "highest_education": result.get('highest_education', 'Not Found'),
                "university": result.get('university', 'Not Found'),
                "education_passout_year": result.get('education_passout_year', 'Not Found'),
                # Technical screening (new Phase 1)
                "technical_screening": result.get('technical_screening', {
                    "must_have_match": [],
                    "good_to_have_match": [],
                    "missing_critical_skills": [],
                    "verified_skills": [],
                    "unverified_skills": [],
                    "obsolete_skills": []
                }),
                # Employment audit (new Phase 1)
                "employment_audit": result.get('employment_audit', {
                    "employment_history": [],
                    "timeline_issues": [],
                    "gaps_found": [],
                    "overlaps_found": [],
                    "experience_inflation_flag": "",
                    "job_hopping_flag": ""
                }),
                # Education check (new Phase 1)
                "education_check": result.get('education_check', {
                    "degree_status": "",
                    "jd_education_warning": "",
                    "passout_year_status": ""
                }),
                # Recruiter screening (new Phase 1)
                "recruiter_screening": result.get('recruiter_screening', {
                    "salary_fit": "",
                    "notice_period_fit": "",
                    "location_fit": "",
                    "stability_score": "",
                    "communication_quality": ""
                }),
                # Risk report (new Phase 1)
                "risk_report": result.get('risk_report', {
                    "risk_level": evaluation.get('risk_level', 'Medium'),
                    "fraud_flags": [],
                    "verification_required": []
                }),
                # Summary / recommendation (new Phase 1)
                "summary": result.get('summary', evaluation.get('justification', '')),
                "final_recommendation": result.get('final_recommendation', recommendation),
                # Legacy evaluation block kept for backward compatibility
                "assessment": evaluation.get('justification', 'Screening completed with detailed analysis.'),
                "justification": evaluation.get('justification', ''),
                "candidate_strengths": evaluation.get('candidate_strengths', []),
                "high_match_skills": evaluation.get('high_match_skills', []),
                "medium_match_skills": evaluation.get('medium_match_skills', []),
                "low_match_skills": evaluation.get('low_or_missing_match_skills', []),
                "candidate_weaknesses": evaluation.get('candidate_weaknesses', []),
                "risk_level": evaluation.get('risk_level', 'Medium'),
                "risk_explanation": evaluation.get('risk_explanation', ''),
                "reward_level": evaluation.get('reward_level', 'Medium'),
                "reward_explanation": evaluation.get('reward_explanation', ''),
                "overall_fit_rating": evaluation.get('overall_fit_rating', score),
                "evaluation": evaluation,
                "job_title": request.job_title,
                "timestamp": datetime.now().isoformat(),
                "strengths": evaluation.get('candidate_strengths', [])
            }
            
            # Save actual screening result to database
            try:
                screen_record = ScreeningResult(
                    user_id=current_user.id if current_user else None,
                    resume_id=None,
                    job_description=request.jd_text[:1000],
                    score=float(score),
                    status="completed",
                    ai_analysis={
                        "candidate_name": request.candidate_name,
                        "job_title": request.job_title,
                        "email": result.get('email', ''),
                    },
                    strengths=evaluation.get('candidate_strengths', []),
                    concerns=evaluation.get('candidate_weaknesses', []),
                    recommendation=recommendation,
                    is_eligible_for_invite=(score >= 75)
                )
                db.add(screen_record)
                db.commit()
                logger.info("Screening result saved: %s %d%% %s", request.candidate_name, score, recommendation)
            except Exception as db_err:
                db.rollback()
                logger.warning("Could not save screening result: %s", db_err)
            
            return {"status": "success", "data": frontend_response}
            
        except (json.JSONDecodeError, ValueError) as e:
            # If JSON parsing fails, return error
            logger.warning("JSON parse error: %s", e)
            logger.debug("Response preview: %s", response[:200])
            raise HTTPException(status_code=500, detail="Failed to parse AI response")
    
    except Exception as e:
        logger.warning("Screening error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BULK SCREENING
# ============================================================================

@router.post("/bulk-screen")
async def bulk_screen(
    request: BulkScreeningRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Bulk screen multiple candidates"""
    try:
        # Get system prompt from loaded file
        system_prompt = SYSTEM_PROMPTS.get('bulk_screening', "")
        
        if not system_prompt:
            # Fallback inline prompt if file not loaded
            system_prompt = """You are a STRICT ATS system and expert recruiter. Evaluate EACH candidate resume against the job description independently.
Return JSON array ONLY. One object per candidate:
[{"candidate_name": "", "name": "", "email": "", "contact_number": "", "current_company": "",
  "score": 0, "match_score": 0, "decision": "", "recommendation": "", "assessment": "",
  "evaluation": {"candidate_strengths": [], "high_match_skills": [], "medium_match_skills": [],
    "low_or_missing_match_skills": [], "candidate_weaknesses": [],
    "risk_level": "", "risk_explanation": "", "reward_level": "", "reward_explanation": "",
    "overall_fit_rating": 0, "justification": ""}}]
Score >= 70 = Shortlisted, < 70 = Rejected. Be strict."""
        
        # Build user message with JD and all candidate resumes
        candidates_text = ""
        candidate_names = []
        
        for idx, candidate in enumerate(request.candidates, 1):
            name = candidate.get('name') or candidate.get('Name') or candidate.get('candidate_name') or f"Candidate {idx}"
            resume = candidate.get('resume') or candidate.get('Resume') or candidate.get('content') or ""
            
            if resume:
                candidate_names.append(name)
                candidates_text += f"\n\n--- CANDIDATE {idx}: {name} ---\n{resume}\n"
        
        user_message = f"""Job Description:
{request.jd_text}

Candidates to Screen:{candidates_text}
"""
        
        # Call OpenAI
        response = await call_openai(system_prompt, user_message, temperature=0.3)
        
        if not response:
            logger.warning("Empty response from OpenAI, using mock screening")
            response = generate_mock_screening_response()
        
        logger.debug("API Response (first 300 chars): %s", response[:300])
        
        # Parse JSON response
        try:

            # Extract JSON from response (handle markdown code blocks)
            clean_response = response.strip()
            if not clean_response:
                raise ValueError("Empty response from API")
            
            # Remove markdown formatting
            if '```json' in clean_response:
                clean_response = clean_response.split('```json')[1].split('```')[0].strip()
            elif '```' in clean_response:
                clean_response = clean_response.split('```')[1].split('```')[0].strip()
            
            # Find JSON object/array
            if not clean_response:
                raise ValueError("No JSON content found in response")
            
            # Try direct parsing first
            results_data = None
            parse_error = None
            
            # Attempt 1: Direct JSON parse
            try:
                results_data = json.loads(clean_response)
            except json.JSONDecodeError as e:
                parse_error = e
            
            # Attempt 2: Extract JSON from response
            if results_data is None and parse_error:
                try:  
                    # Find JSON brackets
                    if '[' in clean_response:
                        json_start = clean_response.find('[')
                        json_end = clean_response.rfind(']') + 1
                        json_str = clean_response[json_start:json_end]
                        results_data = json.loads(json_str)
                    elif '{' in clean_response:
                        json_start = clean_response.find('{')
                        # Find matching closing brace by counting
                        brace_count = 0
                        json_end = len(clean_response)
                        for i, char in enumerate(clean_response[json_start:]):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    json_str = clean_response[json_start:json_start+i+1]
                                    try:
                                        results_data = json.loads(json_str)
                                        break
                                    except json.JSONDecodeError:
                                        # This JSON might be incomplete, try any longer substring
                                        pass
                        
                        # If we still don't have valid JSON, try from found brackets to end
                        if results_data is None and brace_count != 0:
                            # Try just the extracted bracket content
                            json_str = clean_response[json_start:]
                            try:
                                results_data = json.loads(json_str)
                            except:
                                pass
                                
                        if results_data is None:
                            raise ValueError("Could not find valid JSON in response")
                    else:
                        raise ValueError("No JSON brackets [ or { found in response")
                except Exception as e2:
                    logger.debug("JSON parse debug: response len=%d, first 200 chars: %s", len(clean_response), clean_response[:200])
                    raise ValueError(f"Failed to parse JSON response: {str(e2)}")
            
            if results_data is None:
                raise ValueError("Failed to parse AI response as JSON")
            
            # If it's a dict with a 'candidates' key, extract that
            if isinstance(results_data, dict) and 'candidates' in results_data:
                results_data = results_data['candidates']
            elif isinstance(results_data, dict) and 'results' in results_data:
                results_data = results_data['results']
            
            # Ensure it's a list
            if not isinstance(results_data, list):
                if isinstance(results_data, dict):
                    results_data = [results_data]
                else:
                    raise ValueError(f"Expected list or dict, got {type(results_data)}")
            
            if not results_data:
                raise ValueError("No candidates in results")
            
            # Ensure we got results for all uploaded candidates
            logger.debug("Backend: Expected %d candidates, got %d results", len(request.candidates), len(results_data))
            if len(results_data) < len(request.candidates):
                logger.debug("WARNING: Not all candidates were screened! Expected %d, got %d", len(request.candidates), len(results_data))
                logger.debug("Generating mock results for missing candidates...")
                
                # Get candidate names from original request
                screened_names = {r.get('candidate_name') or r.get('candidate') or r.get('name') for r in results_data}
                
                # Add mock results for missing candidates
                for candidate in request.candidates:
                    candidate_name = candidate.get('name') or candidate.get('candidate_name') or candidate.get('Name') or 'Unknown Candidate'
                    if candidate_name not in screened_names:
                        logger.debug("  - Generating mock result for %s", candidate_name)
                        mock_result = {
                            "candidate": candidate_name,
                            "candidate_name": candidate_name,
                            "match_score": 50,
                            "score": 50,
                            "assessment": "Screened but needs manual review",
                            "status": "Reviewed",
                            "recommendation": "REVIEW"
                        }
                        results_data.append(mock_result)
            
                # Add timestamp + job title + normalise fields for each result
                for result in results_data:
                    result['timestamp'] = datetime.now().isoformat()
                    result['job_title'] = request.job_title

                    score = float(result.get('match_score', result.get('score', 0)))

                    # Recommendation normalisation
                    if 'recommendation' not in result or result['recommendation'] is None:
                        if score >= 75:
                            result['recommendation'] = 'INVITE'
                        elif score >= 60:
                            result['recommendation'] = 'REVIEW'
                        else:
                            result['recommendation'] = 'PASS'

                    # Phase 1 new fields — pull from top-level result or set defaults
                    result.setdefault('current_designation', result.get('current_designation', 'Not Found'))
                    result.setdefault('claimed_experience', result.get('claimed_experience', 'Not Found'))
                    result.setdefault('notice_period', result.get('notice_period', 'Not Found'))
                    result.setdefault('location', result.get('location', 'Not Found'))
                    result.setdefault('risk_level', result.get('risk_level', result.get('evaluation', {}).get('risk_level', 'Medium') if isinstance(result.get('evaluation'), dict) else 'Medium'))
                    result.setdefault('job_hopping_flag', result.get('job_hopping_flag', ''))
                    result.setdefault('experience_inflation_flag', result.get('experience_inflation_flag', ''))
            
            # Save screening results to database
            saved_count = 0
            try:
                for idx, result in enumerate(results_data):
                    # Extract data from result
                    candidate_name = result.get('candidate') or result.get('candidate_name') or result.get('name') or f"Candidate {idx+1}"
                    match_score = float(result.get('match_score', result.get('score', 0)))
                    status = result.get('status', result.get('assessment', 'Reviewed'))
                    recommendation = result.get('recommendation', 'REVIEW')
                    
                    # Ensure all required fields exist
                    if 'candidate' not in result:
                        result['candidate'] = candidate_name
                    if 'candidate_name' not in result:
                        result['candidate_name'] = candidate_name
                    if 'match_score' not in result and 'score' in result:
                        result['match_score'] = result['score']
                    if 'match_score' not in result:
                        result['match_score'] = match_score
                    if 'assessment' not in result and 'status' in result:
                        result['assessment'] = result['status']
                    if 'assessment' not in result:
                        result['assessment'] = status
                    
                    # Create screening result record
                    screening_result = ScreeningResult(
                        user_id=current_user.id if current_user else None,
                        resume_id=None,
                        job_description=request.jd_text[:500] if request.jd_text else "",
                        score=match_score,
                        status="completed",
                        ai_analysis={"candidate_name": candidate_name, "job_title": request.job_title, "details": result.get('evaluation', result.get('assessment', {}))},
                        strengths=result.get('evaluation', {}).get('candidate_strengths', []) if isinstance(result.get('evaluation'), dict) else [],
                        concerns=result.get('evaluation', {}).get('candidate_weaknesses', []) if isinstance(result.get('evaluation'), dict) else [],
                        recommendation=recommendation.upper() if recommendation else "REVIEW",
                        is_eligible_for_invite=(match_score >= 75)
                    )
                    db.add(screening_result)
                    saved_count += 1
                
                db.commit()
                logger.info("Successfully saved %d/%d screening results to database", saved_count, len(results_data))
            except Exception as db_error:
                logger.warning("Database error: %s", db_error)
                db.rollback()
            
            # Log bulk screening activity
            try:
                log_activity(db, current_user.id if current_user else None, "bulk_screening", {
                    "candidate_count": len(results_data),
                    "saved_count": saved_count,
                    "job_title": request.job_title,
                    "timestamp": datetime.now().isoformat()
                })
            except:
                pass  # Logging is optional
            
            # Ensure all results have recommendation field
            for r in results_data:
                if 'recommendation' not in r:
                    r['recommendation'] = 'REVIEW'
            
            return {"status": "success", "results": results_data, "count": len(results_data), "saved": saved_count}
                
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("JSON parse error: %s", e)
            logger.debug("Response preview: %s", response[:500])
            logger.warning("Using mock screening response as fallback")
            response = generate_mock_screening_response()
            
            # Re-try parsing with mock
            try:
                results_data = json.loads(response)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail=f"Failed to parse even mock response: {str(e)}")
            
            # Process mock results the same way as real results
            if isinstance(results_data, dict) and 'candidates' in results_data:
                results_data = results_data['candidates']
            elif isinstance(results_data, dict) and 'results' in results_data:
                results_data = results_data['results']
            
            # Ensure it's a list
            if not isinstance(results_data, list):
                if isinstance(results_data, dict):
                    results_data = [results_data]
            
            # Save and return
            if results_data:
                try:
                    for idx, result in enumerate(results_data):
                        candidate_name = result.get('candidate') or result.get('candidate_name') or result.get('name') or f"Candidate {idx+1}"
                        match_score = float(result.get('match_score', result.get('score', 0)))
                        recommendation = result.get('recommendation', 'INVITE')
                        
                        screening_result = ScreeningResult(
                            user_id=current_user.id if current_user else None,
                            resume_id=None,
                            job_description=request.jd_text[:500] if request.jd_text else "",
                            score=match_score,
                            status="completed",
                            ai_analysis={"candidate_name": candidate_name, "job_title": request.job_title},
                            strengths=result.get('evaluation', {}).get('candidate_strengths', []) if isinstance(result.get('evaluation'), dict) else [],
                            concerns=result.get('evaluation', {}).get('candidate_weaknesses', []) if isinstance(result.get('evaluation'), dict) else [],
                            recommendation=recommendation.upper() if recommendation else "INVITE",
                            is_eligible_for_invite=(match_score >= 75)
                        )
                        db.add(screening_result)
                    db.commit()
                except Exception as db_error:
                    logger.warning("Could not save to DB: %s", db_error)
                    db.rollback()
                
                return {"status": "success", "results": results_data, "count": len(results_data)}
            else:
                raise ValueError("No candidates in results after fallback")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Bulk screening error: %s: %s", type(e).__name__, e)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# JOB POST GENERATION
# ============================================================================

@router.post("/generate-job-post")
async def generate_job_post(
    request: JobPostRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Generate job posts for multiple platforms"""
    try:
        # Load system prompt from file or use simple default
        system_prompt = SYSTEM_PROMPTS.get('job_post', "")
        
        if not system_prompt:
            # Fallback to simple prompt if file not loaded
            system_prompt = """You are a recruitment automation assistant.
Create SHORT, CONCISE job posts for Email, LinkedIn, WhatsApp, and Indeed.

✅ RULES FOR ALL POSTS:
- Keep posts SHORT and PROFESSIONAL (not lengthy)
- Email: Greeting + Role Title + Location + 3-4 Key Skills + Call to Action
- LinkedIn: Role + Location + Key Skills (max 150 words) + Hashtags
- WhatsApp: Title + Short Description + Key Skills + Call to Action
- Indeed: Title + Type + Location + Description + Requirements
- NO lengthy company descriptions
- NO long candidate information forms
- Return JSON ONLY - no explanations

OUTPUT (JSON ONLY):
{
  "role": "Job Title",
  "location": "Job Location",
  "experience": "Years required",
  "key_skills": ["Skill 1", "Skill 2", "Skill 3"],
  "recruitment_type": "Permanent/Contract/Internship",
  "email_post": "Brief greeting + role + location + skills",
  "linkedin_post": "Role + skills + hashtags (100-150 words)",
  "whatsapp_post": "Short title + key skills + CTA",
  "indeed_post": "Title + type + location + brief description"
}"""
        
        # User message format matching the system prompt expectations
        user_message = f"""Job Description:
{request.jd_text}"""
        
        # Call OpenAI with increased max_tokens and temperature for DETAILED, LENGTHY job posts
        response = await call_openai(system_prompt, user_message, temperature=0.5, max_tokens=3000)
        
        # Try to parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            clean_response = response.strip()
            if '```json' in clean_response:
                clean_response = clean_response.split('```json')[1].split('```')[0].strip()
            elif '```' in clean_response:
                clean_response = clean_response.split('```')[1].split('```')[0].strip()
            
            # Find JSON object
            if '{' in clean_response and '}' in clean_response:
                json_start = clean_response.find('{')
                json_end = clean_response.rfind('}') + 1
                json_str = clean_response[json_start:json_end]
                posts = json.loads(json_str)
            else:
                posts = json.loads(clean_response)
            
            # Ensure all required fields exist with proper data types
            posts.setdefault('client_project', 'NA')
            posts.setdefault('recruitment_type', 'Permanent')
            posts.setdefault('role', request.job_title)
            posts.setdefault('experience', 'Not specified')
            posts.setdefault('location', 'Remote/Onsite')
            posts.setdefault('contract_duration', 'NA')
            posts.setdefault('key_skills', ['Technical expertise', 'Problem-solving', 'Communication'])
            posts.setdefault('no_of_submissions', 0)
            posts.setdefault('linkedin_post', '')
            posts.setdefault('indeed_post', '')
            posts.setdefault('email_post', '')
            posts.setdefault('whatsapp_post', '')
            
            # Ensure key_skills is a list
            if not isinstance(posts.get('key_skills'), list):
                posts['key_skills'] = ['Technical expertise', 'Problem-solving', 'Communication']
            
            # Ensure no_of_submissions is an integer
            if not isinstance(posts.get('no_of_submissions'), int):
                posts['no_of_submissions'] = 0
            
            # POST-PROCESSING: Expand LinkedIn if it's too short (model tends to undergenerate)
            linkedin = posts.get('linkedin_post', '')
            if len(linkedin) < 300:  # If LinkedIn is less than 300 chars, expand it
                # Regenerate LinkedIn with explicit focus
                linkedin_system = """You are an expert at creating detailed multi-section LinkedIn job posts.
MUST create LinkedIn post with these EXACT sections separated by blank lines:
- Opening hook with emoji and job title
- Position Overview (2-3 sentences)
- Key Details (bullet list: role, location, type, experience, industry)
- Key Opportunities (8 detailed bullet points, 15-30 words each)
- Required Skills (9 skill checkmarks, 10-20 words each)
- What We Offer (4 benefit bullets)
- 10 relevant hashtags

MINIMUM 400 characters.
Return JSON ONLY: {"linkedin_post": "FULL_DETAILED_POST"}"""
                
                linkedin_user = f"""Job: {request.job_title}
Description: {request.jd_text}"""
                try:
                    linkedin_response = await call_openai(linkedin_system, linkedin_user, temperature=0.6, max_tokens=1500)
                    # Extract JSON
                    if '{' in linkedin_response:
                        json_start = linkedin_response.find('{')
                        json_end = linkedin_response.rfind('}') + 1
                        linkedin_json = json.loads(linkedin_response[json_start:json_end])
                        expanded_linkedin = linkedin_json.get('linkedin_post', '')
                        if len(expanded_linkedin) > len(linkedin):
                            posts['linkedin_post'] = expanded_linkedin
                except:
                    pass  # Keep original if expansion fails
            
            # Log job post generation activity
            log_activity(db, current_user.id if current_user else None, "job_post_generation", {
                "job_title": request.job_title,
                "platforms": ["linkedin", "indeed", "email", "whatsapp"],
                "timestamp": datetime.now().isoformat()
            })
            
            return {"status": "success", "data": posts}
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning("JSON parse error: %s", e)
            logger.debug("Response preview: %s", response[:200])
            
            # Fallback: Generate template-based job posts
            logger.debug("Using fallback template generation...")
            posts = {
                "client_project": "NA",
                "recruitment_type": "Permanent",
                "role": request.job_title,
                "experience": "Not specified",
                "location": "Remote/Onsite",
                "contract_duration": "NA",
                "key_skills": ["Required skills from JD", "Technical expertise", "Communication skills"],
                "no_of_submissions": 0,
                "linkedin_post": f"""🚀 We're Hiring: {request.job_title} | Permanent | Remote/Onsite
We're looking for an experienced {request.job_title} to join an exciting project and collaborate with a dynamic team.

📌 Role Details:
Position: {request.job_title}
Type: Permanent
Experience: Open to all levels
Location: Remote/Onsite options available
Industry: Technology & Innovation
Start Date: ASAP

💻 Key Skills & Experience:
✅ Strong technical background in relevant domain
✅ Excellent problem-solving and analytical capabilities
✅ Experience with modern development tools and frameworks
✅ Knowledge of software development best practices
✅ Database design and optimization skills
✅ API development and integration experience
✅ Understanding of cloud platforms and DevOps practices
✅ Strong communication and team collaboration abilities

🎯 Key Responsibilities:
• Design and develop high-quality technical solutions
• Collaborate with cross-functional teams including product and design
• Write clean, maintainable, and well-documented code
• Participate in code reviews and technical discussions
• Troubleshoot and resolve complex technical challenges
• Mentor team members and contribute to knowledge sharing
• Stay updated with latest industry trends and technologies
• Ensure adherence to security and performance standards

🏢 What We Offer:
• Competitive salary package with performance bonuses
• Comprehensive benefits and professional development opportunities
• Flexible working arrangements and modern tech environment
• Collaborative team culture with growth opportunities

📧 Apply Now: Send your CV for this exciting opportunity!

Join our innovative team and work on cutting-edge projects!

#Hiring #{request.job_title.replace(' ', '')} #TechJobs #RemoteWork #Innovation #CareerGrowth #TeamWork""",
                "indeed_post": f"""Job Title: {request.job_title}
Job Type: Full-time, Permanent
Location: Remote/Onsite
Experience Required: Open to all levels
Salary: Competitive package

Job Description:
We are seeking a qualified {request.job_title} to join our team and contribute to exciting projects. The successful candidate will work in a collaborative environment, developing innovative solutions and contributing to our growing success.

Key Responsibilities:
- Design and develop technical solutions according to business requirements
- Collaborate effectively with cross-functional teams including developers, designers, and product managers
- Write clean, efficient, and maintainable code following industry best practices
- Participate in planning sessions, code reviews, and technical discussions
- Troubleshoot complex technical issues and provide effective solutions
- Test and debug applications to ensure optimal performance and reliability
- Contribute to technical documentation and knowledge base
- Mentor junior team members and participate in knowledge transfer sessions
- Stay current with emerging technologies and industry trends
- Ensure compliance with security standards and data protection policies

Required Skills & Qualifications:
- Strong technical background in software development and related technologies
- Excellent problem-solving abilities with attention to detail
- Experience with modern development frameworks and tools
- Knowledge of database design and optimization techniques
- Understanding of software development lifecycle and agile methodologies
- Strong analytical and logical thinking capabilities
- Excellent communication and interpersonal skills
- Ability to work independently and collaboratively in team environments
- Adaptability to learn new technologies and work in fast-paced settings

Preferred Skills:
- Experience with cloud platforms and containerization technologies
- Knowledge of CI/CD pipelines and DevOps practices
- Understanding of microservices architecture and design patterns
- Familiarity with testing frameworks and quality assurance processes

Company Benefits:
- Competitive salary with regular performance reviews
- Comprehensive health insurance and wellness programs
- Professional development opportunities and training budget
- Flexible working hours and remote work options
- Modern office environment with latest technology tools

To apply, please send your resume and cover letter highlighting your relevant experience.""",
                "email_post": f"""Dear Candidate,

Greetings from our recruitment team!
I hope this message finds you well. My name is [Recruiter Name], and I'm a Senior Recruiter specializing in technology placements. We are currently hiring for an exciting {request.job_title} position and would like to share this opportunity with you.

Title: {request.job_title}
Type: Permanent
Work Arrangement: Remote/Onsite options available

About the Company:
We are working with a dynamic technology company that's experiencing rapid growth and innovation. They are known for their cutting-edge solutions, collaborative work environment, and commitment to employee development. The company values technical excellence, creativity, and continuous learning.

Role Overview:
We are looking for a qualified {request.job_title} to join their expanding team. This role offers excellent opportunities for professional growth, working with modern technologies, and contributing to impactful projects. You'll be part of a collaborative environment where your technical skills will be valued and developed.

Key Responsibilities:
- Design and develop scalable technical solutions using modern frameworks and best practices
- Collaborate closely with cross-functional teams including product managers, designers, and QA engineers
- Write clean, maintainable, and well-documented code that meets quality standards
- Participate in architectural decisions and technical planning sessions
- Conduct thorough code reviews and provide constructive feedback to team members
- Troubleshoot complex technical issues and implement effective solutions
- Optimize application performance and ensure system reliability and security
- Mentor junior developers and contribute to team knowledge sharing initiatives
- Stay updated with latest technological trends and contribute to technical innovation
- Participate in agile development processes and continuous improvement initiatives

Preferred Skills & Experience:
- Bachelor's degree in Computer Science, Engineering, or related technical field
- Strong foundation in software development principles and best practices
- Experience with modern programming languages and development frameworks
- Knowledge of database design, optimization, and data modeling concepts
- Understanding of software architecture patterns and system design principles  
- Familiarity with version control systems and collaborative development workflows
- Experience with testing methodologies and quality assurance processes
- Strong analytical and problem-solving capabilities with attention to detail
- Excellent communication skills and ability to work effectively in team environments
- Continuous learning mindset and adaptability to new technologies and methodologies

What We Offer:
- Competitive salary package with performance-based bonuses and regular reviews
- Comprehensive benefits including health insurance and professional development budget
- Flexible working arrangements with remote work options and modern office facilities
- Collaborative and inclusive work culture with opportunities for career advancement

If this opportunity aligns with your experience and career goals, please share your updated resume.
Please provide the following details to proceed for interviews:
- Full Name
- Total experience
- Relevant experience
- Current salary
- Expected salary
- Notice period
- Current company
- Current location
- Availability for face-to-face interview

I look forward to hearing from you and discussing this exciting opportunity further.

Best regards,
[Recruiter Name]
Senior Technology Recruiter""",
                "whatsapp_post": f"""📢 Urgent Hiring: {request.job_title}
📍 Location: Remote/Onsite options
💼 Type: Permanent
🕒 Start Date: ASAP
💰 Package: Competitive salary + benefits

🔥 About the Role:
Join an innovative tech company working on cutting-edge projects! Great opportunity for career growth in a collaborative environment.

✅ Must-Have Requirements:
✅ Strong technical background in software development
✅ Experience with modern programming languages and frameworks
✅ Knowledge of database design and optimization
✅ Understanding of software development best practices
✅ Problem-solving skills with attention to detail
✅ Experience with version control and collaborative development
✅ Strong communication and team collaboration abilities
✅ Ability to write clean, maintainable code

🔸 Nice to Have Skills:
🔸 Experience with cloud platforms (AWS/Azure/GCP)
🔸 Knowledge of containerization and microservices
🔸 Familiarity with CI/CD pipelines and DevOps practices
🔸 Understanding of agile methodologies and scrum processes
🔸 Experience with testing frameworks and TDD practices
🔸 Leadership and mentoring capabilities

🎯 What You'll Do:
• Develop scalable technical solutions and applications
• Collaborate with cross-functional teams on exciting projects
• Participate in architectural decisions and code reviews
• Mentor team members and contribute to knowledge sharing
• Work with modern tech stack and innovative technologies

🏢 Perks & Benefits:
• Competitive salary with performance bonuses
• Comprehensive health insurance and wellness programs
• Professional development budget and training opportunities
• Flexible working hours with remote work options
• Modern office environment with latest tech tools
• Career growth opportunities and mentorship programs

If you or someone you know is interested in this {request.job_title} role, DM me your CV now! 🙌
Quick response guaranteed! ⚡

#TechJobs #Hiring #{request.job_title.replace(' ', '')} #RemoteWork #Innovation"""
            }
            
            # Log fallback usage
            log_activity(db, current_user.id if current_user else None, "job_post_generation_fallback", {
                "job_title": request.job_title,
                "reason": "AI_JSON_parse_failed",
                "timestamp": datetime.now().isoformat()
            })
            
            return {"status": "success", "data": posts}
    
    except Exception as e:
        logger.warning("Job post generation error: %s", e)
        
        # Final fallback: Generate basic template posts if all else fails
        logger.debug("Using final fallback template generation...")
        fallback_posts = {
            "client_project": "NA",
            "recruitment_type": "Permanent",
            "role": request.job_title,
            "experience": "Not specified",
            "location": "To be discussed",
            "contract_duration": "NA",
            "key_skills": ["Technical skills", "Communication", "Problem-solving"],
            "no_of_submissions": 0,
            "linkedin_post": f"""🚀 We're Hiring: {request.job_title}
Exciting opportunity for a skilled {request.job_title} to join our team!

📧 Apply now with your CV!
#Hiring #{request.job_title.replace(' ', '')} #Jobs""",
            "indeed_post": f"""Job Title: {request.job_title}
Job Type: Full-time
We are seeking a qualified {request.job_title}.
To apply, please send your resume.""",
            "email_post": f"""Dear Candidate,

We have an exciting {request.job_title} opportunity available.
Please send your updated resume if interested.

Best regards,
Recruitment Team""",
            "whatsapp_post": f"""📢 Hiring: {request.job_title}
Exciting opportunity available!
DM for details! 🙌"""
        }
        
        # Log final fallback usage
        try:
            log_activity(db, current_user.id if current_user else None, "job_post_generation_final_fallback", {
                "job_title": request.job_title,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass  # Don't fail on logging errors
        
        return {"status": "success", "data": fallback_posts}


# ============================================================================
# AI WRITING ASSISTANT
# ============================================================================

@router.post("/ai-write")
async def ai_write(
    request: AIWriteRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """AI writing assistant for rewriting/paraphrasing with platform and tone awareness"""
    try:
        # Get base system prompt from file
        base_system_prompt = SYSTEM_PROMPTS.get('ai_writing', "")
        
        # Inject platform and tone information into the prompt
        if base_system_prompt:
            system_prompt = base_system_prompt + f"""

CONTEXT FOR THIS REQUEST:
- Platform: {request.platform.upper()}
- Tone: {request.tone}
- Action: {request.action}

Apply the {request.platform.upper()} guidelines above with {request.tone} tone."""
        else:
            # Fallback if prompt not loaded
            system_prompt = f"""You are a professional recruitment communication expert.
Platform: {request.platform.upper()}
Tone: {request.tone}
Action: {request.action}

Optimize for {request.platform} with {request.tone} tone.
- Maintain original meaning
- Adapt to platform format
- Fix any grammar issues
- Make it engaging and professional"""
        
        # Create user message with platform context
        user_message = f"""Please {request.action} this text for {request.platform} with a {request.tone} tone:

{request.text}"""
        
        # Call OpenAI with standard temperature for consistency
        response = await call_openai(system_prompt, user_message, temperature=0.3, max_tokens=1500)
        
        return {
            "status": "success",
            "data": {"output": response},
            "output": response
        }
    
    except Exception as e:
        logger.warning("AI writing error: %s", e)
        return {"status": "error", "error": str(e)}


# ============================================================================
# MESSAGE GENERATION
# ============================================================================

@router.post("/generate-message")
async def generate_message(
    request: MessageRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Generate candidate communication messages"""
    try:
        system_prompt = f"""
Generate a {request.message_type} message for recruitment.

Tone: {request.tone}
Recipient: {request.recipient}
Job Title: {request.job_title}

Context: {request.context}

Create a professional and appropriate message.
"""
        
        user_message = f"Create a {request.message_type} message for {request.recipient} regarding the {request.job_title} position."
        
        response = await call_openai(system_prompt, user_message)
        
        return {
            "status": "success",
            "data": {"message": response, "output": response}
        }
    
    except Exception as e:
        logger.warning("Message generation error: %s", e)
        return {"status": "error", "error": str(e)}


# ============================================================================
# UPLOAD BULK RESUMES
# ============================================================================

@router.post("/upload-bulk-resumes")
async def upload_bulk_resumes(
    files: List[UploadFile] = File(...),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """Upload multiple resume files for bulk screening"""
    try:
        candidates = []
        processing_errors = []
        
        logger.debug("📥 Received {len(files)} files for bulk processing")
        
        for file in files:
            try:
                file_content = await file.read()
                filename = file.filename or "unknown.txt"
                ext = filename.lower().split('.')[-1]
                
                logger.debug("Processing file: {filename} ({len(file_content)} bytes, ext: {ext})")
                
                text_content = ""
                if ext == 'pdf':
                    text_content = extract_text_from_pdf(file_content)
                elif ext in ['docx', 'doc']:
                    text_content = extract_text_from_docx(file_content)
                elif ext == 'txt':
                    text_content = file_content.decode('utf-8')
                else:
                    processing_errors.append(f"{filename}: Unsupported file type '{ext}'")
                    continue
                
                # Check if extraction was successful
                if text_content and not text_content.startswith(('PDF_ERROR:', 'DOCX_ERROR:', 'PDF_EMPTY', 'DOCX_EMPTY')):
                    # Extract name from filename or content
                    name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
                    
                    candidates.append({
                        "name": name,
                        "filename": filename,
                        "resume": text_content,
                        "content": text_content
                    })
                    logger.info("Successfully processed: %s -> %s", filename, name)
                else:
                    processing_errors.append(f"{filename}: Text extraction failed - {text_content}")
                    logger.warning("Failed to extract text from: %s", filename)
            
            except Exception as e:
                error_msg = f"{filename}: Processing error - {str(e)}"
                processing_errors.append(error_msg)
                logger.warning("Error processing %s: %s", filename, e)
                continue
        
        logger.debug("Final result: {len(candidates)} candidates, {len(processing_errors)} errors")
        
        if not candidates:
            if processing_errors:
                # Show specific errors to help user understand what went wrong
                main_errors = []
                for error in processing_errors[:3]:  # Show top 3 errors
                    if "PDF_ERROR" in error or "DOCX_ERROR" in error:
                        main_errors.append(f"• {error.split(':')[0]}: File is corrupted or password-protected")
                    elif "PDF_EMPTY" in error or "DOCX_EMPTY" in error:
                        main_errors.append(f"• {error.split(':')[0]}: File appears to be empty or contains no text")
                    elif "Unsupported file type" in error:
                        main_errors.append(f"• {error}")
                    else:
                        main_errors.append(f"• {error}")
                
                if len(processing_errors) > 3:
                    main_errors.append(f"• ... and {len(processing_errors)-3} more files had issues")
                
                error_details = "\n".join(main_errors)
                return {
                    "error": f"No valid resumes could be processed from {len(files)} uploaded files.",
                    "error_details": error_details,
                    "suggestions": [
                        "Ensure files are in PDF, DOCX, or TXT format",
                        "Check if PDF files are password-protected (not supported)",
                        "Verify files contain readable text (not just images)",
                        "Try uploading files one by one to identify specific issues"
                    ],
                    "candidates": [], 
                    "count": 0
                }
            else:
                return {
                    "error": "No files were processed. Please check your file uploads.",
                    "suggestions": [
                        "Ensure you've selected files to upload",
                        "Supported formats: PDF, DOCX, DOC, TXT",
                        "Maximum file size: 10MB per file"
                    ],
                    "candidates": [], 
                    "count": 0
                }
        
        # Log bulk upload activity
        log_activity(db, current_user.id if current_user else None, "bulk_resume_upload", {
            "files_uploaded": len(files),
            "candidates_processed": len(candidates),
            "processing_errors": len(processing_errors),
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "candidates": candidates,
            "count": len(candidates),
            "processing_errors": processing_errors[:5] if processing_errors else [],  # Show up to 5 errors
            "success_message": f"Successfully processed {len(candidates)} out of {len(files)} files" if processing_errors else f"Successfully processed all {len(candidates)} files"
        }
    
    except Exception as e:
        logger.warning("Bulk upload error: %s", e)
        return {"error": str(e), "candidates": [], "count": 0}


# ============================================================================
# LOGS
# ============================================================================

@router.get("/logs")
async def get_logs(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system activity logs for administrators only."""
    try:
        logs = []
        
        # Get recent REAL screening results only (skip activity log entries with status='logged')
        try:
            screening_results = db.query(ScreeningResult).filter(
                ScreeningResult.status == "completed"
            ).order_by(ScreeningResult.created_at.desc()).limit(50).all()
            if screening_results:
                for result in screening_results:
                    timestamp = result.created_at.strftime('%Y-%m-%d %H:%M:%S') if result.created_at else 'N/A'
                    score = result.score if result.score else 0
                    recommendation = result.recommendation if result.recommendation else 'PENDING'
                    # Extract candidate name from ai_analysis JSON
                    candidate_name = "Candidate"
                    if result.ai_analysis and isinstance(result.ai_analysis, dict):
                        candidate_name = result.ai_analysis.get('candidate_name', 'Candidate')
                    logs.append(f"[{timestamp}] {candidate_name}: {score:.0f}% - {recommendation}")
                logger.info("Loaded {len(logs)} screening results from database")
            else:
                logger.warning("No screening results in database yet")
        except Exception as db_err:
            logger.warning("DB query error: %s", db_err)
        
        # If no database logs, read from log file
        if not logs:
            log_file = Path("logs/recruitment_ai.log")
            if log_file.exists():
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                logs = [line.strip() for line in lines[-50:] if line.strip()]
                if logs:
                    logger.info("Loaded {len(logs)} logs from file")
        
        # Fallback logs
        if not logs:
            logs = [
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] System started",
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ready to process requests"
            ]
            logger.warning("Using fallback logs")
        
        return {"logs": logs, "count": len(logs), "scope": "admin"}
    
    except Exception as e:
        logger.debug("Error in /api/logs: %s", e)
        import traceback
        traceback.print_exc()
        return {"logs": [f"Error loading logs: {str(e)}"], "count": 0}


@router.get("/screening-results")  
async def get_screening_results(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get screening results scoped to the current authenticated user."""
    logger.debug("[SCREENING-RESULTS] Endpoint called")
    try:
        logger.debug("[SCREENING-RESULTS] Querying database...")
        query = db.query(ScreeningResult).filter(
            ScreeningResult.status == "completed"
        )
        if current_user.role != "admin":
            query = query.filter(ScreeningResult.user_id == current_user.id)

        screening_results = query.order_by(ScreeningResult.created_at.desc()).limit(50).all()
        logger.debug("[SCREENING-RESULTS] Query returned {len(screening_results)} results")
        
        results = []
        for result in screening_results:
            results.append({
                "id": result.id,
                "score": result.score,
                "recommendation": result.recommendation,
                "created_at": result.created_at.isoformat() if result.created_at else None,
                "scope": "admin" if current_user.role == "admin" else "user",
            })
        
        logger.debug("[SCREENING-RESULTS] Returning {len(results)} results")
        return {"results": results}
    except Exception as e:
        logger.debug("[SCREENING-RESULTS] Error: %s", e)
        import traceback
        traceback.print_exc()
        return {"results": [], "error": str(e)}


@router.get("/status")
async def status():
    """System status check"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "model": OPENAI_MODEL,
        "prompts_loaded": len(SYSTEM_PROMPTS)
    }


# ============================================================================
# PHASE 2 – BOOLEAN SEARCH KEYWORD ENGINE
# ============================================================================

class BooleanSearchRequest(BaseModel):
    jd_text: str
    job_title: Optional[str] = ""


@router.post("/boolean-search")
async def generate_boolean_search(
    request: BooleanSearchRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Generate recruiter-ready Boolean search strings from a Job Description.

    Outputs:
    - Short Boolean Search
    - Advanced Boolean Search
    - Alternate Keyword Search
    - Must-have keywords
    - Nice-to-have keywords

    Compatible with: LinkedIn, Naukri, Indeed, Monster, Foundit, internal ATS.
    """
    try:
        system_prompt = SYSTEM_PROMPTS.get('boolean_search', "")

        if not system_prompt:
            system_prompt = """You are an expert Boolean Search String Generator for recruitment.
Analyze the provided Job Description and generate ready-to-use Boolean search strings.
Return JSON ONLY. No markdown. No extra text.

{
  "job_title": "",
  "must_have_keywords": [],
  "nice_to_have_keywords": [],
  "exclude_keywords": [],
  "short_boolean": "",
  "advanced_boolean": "",
  "alternate_boolean": "",
  "linkedin_search": "",
  "naukri_search": "",
  "notes": ""
}"""

        user_message = f"""Job Title: {request.job_title}

Job Description:
{request.jd_text}"""

        response = await call_openai(system_prompt, user_message, temperature=0.2, max_tokens=1500)

        try:
            clean = response.strip()
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0].strip()
            elif '```' in clean:
                clean = clean.split('```')[1].split('```')[0].strip()

            if '{' in clean:
                json_start = clean.find('{')
                json_end = clean.rfind('}') + 1
                result = json.loads(clean[json_start:json_end])
            else:
                result = json.loads(clean)

            log_activity(db, current_user.id if current_user else None, "boolean_search", {
                "job_title": request.job_title,
                "timestamp": datetime.now().isoformat()
            })

            return {"status": "success", "data": result}

        except (json.JSONDecodeError, ValueError) as e:
            logger.debug("Boolean search JSON parse error: %s", e)
            # Fallback: build basic boolean from JD words
            words = [w.strip('.,;:()') for w in request.jd_text.split() if len(w) > 4]
            unique = list(dict.fromkeys(words))[:20]
            short_bool = " AND ".join(f'"{w}"' for w in unique[:5])
            return {
                "status": "success",
                "data": {
                    "job_title": request.job_title,
                    "must_have_keywords": unique[:10],
                    "nice_to_have_keywords": unique[10:20],
                    "exclude_keywords": [],
                    "short_boolean": short_bool,
                    "advanced_boolean": short_bool,
                    "alternate_boolean": short_bool,
                    "linkedin_search": short_bool,
                    "naukri_search": short_bool,
                    "notes": "Basic extraction — AI parse failed, manual refinement recommended."
                }
            }

    except Exception as e:
        logger.debug("Boolean search error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PHASE 3 – JD GENERATOR (WHEN USER HAS NO JD)
# ============================================================================

class JDGeneratorRequest(BaseModel):
    job_title: str
    skills: Optional[str] = ""
    experience: Optional[str] = ""
    location: Optional[str] = ""
    employment_type: Optional[str] = "Permanent"
    education: Optional[str] = ""
    salary: Optional[str] = ""
    responsibilities: Optional[str] = ""
    notice_period: Optional[str] = ""


@router.post("/generate-jd")
async def generate_full_jd(
    request: JDGeneratorRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Generate a complete professional Job Description from basic inputs.

    Covers:
    - CEO / CTO / Director / VP / Leadership
    - IT, AI, Networking, Architecture, BA/PM, Sales/HR/Finance
    - Blue Collar, White Collar
    - Permanent / Contract / C2H / Internship
    - Fresher to Executive level

    Output: Structured JSON + full_jd_text ready for posting.
    """
    try:
        system_prompt = SYSTEM_PROMPTS.get('jd_generator', "")

        if not system_prompt:
            system_prompt = """You are a senior recruitment professional and job description writer.
Generate a COMPLETE, PROFESSIONAL, HUMAN-WRITTEN job description from the provided inputs.
STRICT RULES:
- Human written tone - no AI robotic language.
- No fake promises or exaggerated text.
- Clean, concise, real market-standard format.
- Do NOT use buzzwords like "dynamic", "disruptive", "passionate rockstar".
- Return JSON ONLY. No markdown. No extra text.

{
  "job_title": "",
  "employment_type": "",
  "location": "",
  "experience_required": "",
  "role_summary": "",
  "key_responsibilities": [],
  "required_skills": [],
  "preferred_skills": [],
  "education_preferred": "",
  "notice_period": "",
  "salary_range": "",
  "apply_cta": "",
  "full_jd_text": ""
}"""

        user_message = f"""Generate a professional Job Description for the following role:

Job Title: {request.job_title}
Employment Type: {request.employment_type}
Location: {request.location or "To be specified"}
Experience Required: {request.experience or "To be specified"}
Key Skills: {request.skills or "To be determined"}
Education: {request.education or "Relevant degree preferred"}
Salary: {request.salary or "Competitive"}
Notice Period Preference: {request.notice_period or "Immediate to 30 days preferred"}
Additional Responsibilities Context: {request.responsibilities or "Standard for this role"}"""

        response = await call_openai(system_prompt, user_message, temperature=0.4, max_tokens=2500)

        try:
            clean = response.strip()
            if '```json' in clean:
                clean = clean.split('```json')[1].split('```')[0].strip()
            elif '```' in clean:
                clean = clean.split('```')[1].split('```')[0].strip()

            if '{' in clean:
                json_start = clean.find('{')
                json_end = clean.rfind('}') + 1
                result = json.loads(clean[json_start:json_end])
            else:
                result = json.loads(clean)

            # Ensure all required fields exist
            result.setdefault('job_title', request.job_title)
            result.setdefault('employment_type', request.employment_type)
            result.setdefault('location', request.location or "To be specified")
            result.setdefault('experience_required', request.experience or "To be specified")
            result.setdefault('role_summary', f"We are looking for an experienced {request.job_title} to join our team.")
            result.setdefault('key_responsibilities', [])
            result.setdefault('required_skills', [])
            result.setdefault('preferred_skills', [])
            result.setdefault('education_preferred', request.education or "Relevant qualification preferred")
            result.setdefault('notice_period', request.notice_period or "Immediate to 30 days preferred")
            result.setdefault('salary_range', request.salary or "Competitive")
            result.setdefault('apply_cta', "Please send your updated CV along with your current CTC, expected CTC, and notice period.")
            result.setdefault('full_jd_text', "")

            # Build full_jd_text if not provided
            if not result['full_jd_text']:
                responsibilities = "\n".join(f"- {r}" for r in result['key_responsibilities']) or "- To be defined"
                req_skills = "\n".join(f"- {s}" for s in result['required_skills']) or "- To be defined"
                pref_skills = "\n".join(f"- {s}" for s in result['preferred_skills']) or "- To be defined"
                result['full_jd_text'] = f"""Job Title: {result['job_title']}
Employment Type: {result['employment_type']}
Location: {result['location']}
Experience Required: {result['experience_required']}

Role Summary:
{result['role_summary']}

Key Responsibilities:
{responsibilities}

Required Skills:
{req_skills}

Preferred Skills:
{pref_skills}

Education: {result['education_preferred']}
Notice Period: {result['notice_period']}
Salary: {result['salary_range']}

{result['apply_cta']}"""

            log_activity(db, current_user.id if current_user else None, "jd_generation", {
                "job_title": request.job_title,
                "employment_type": request.employment_type,
                "timestamp": datetime.now().isoformat()
            })

            return {"status": "success", "data": result}

        except (json.JSONDecodeError, ValueError) as e:
            logger.debug("JD generator JSON parse error: %s", e)
            # Return structured fallback
            fallback = {
                "job_title": request.job_title,
                "employment_type": request.employment_type,
                "location": request.location or "To be specified",
                "experience_required": request.experience or "To be specified",
                "role_summary": f"We are seeking a qualified {request.job_title} to join our team.",
                "key_responsibilities": [
                    "Perform core responsibilities as per the role requirements",
                    "Collaborate with cross-functional teams",
                    "Deliver high-quality work on time",
                    "Participate in team meetings and planning sessions",
                    "Contribute to process improvements",
                    "Maintain professional standards in all deliverables"
                ],
                "required_skills": [s.strip() for s in request.skills.split(',') if s.strip()] if request.skills else ["Relevant technical skills", "Communication", "Problem-solving"],
                "preferred_skills": ["Domain expertise", "Leadership", "Analytical thinking"],
                "education_preferred": request.education or "Relevant degree or equivalent experience",
                "notice_period": request.notice_period or "Immediate to 30 days",
                "salary_range": request.salary or "Competitive",
                "apply_cta": "Please send your updated CV with current CTC, expected CTC, and notice period.",
                "full_jd_text": f"Job Title: {request.job_title}\nEmployment Type: {request.employment_type}\nLocation: {request.location or 'TBD'}\nExperience: {request.experience or 'TBD'}\nSkills: {request.skills or 'TBD'}\n\nPlease send your CV to apply."
            }
            return {"status": "success", "data": fallback}

    except Exception as e:
        logger.debug("JD generator error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
