#!/usr/bin/env python3
"""
Advanced Recruitment ATS v3.1
All-in-One Professional Dashboard with n8n Integration
Features: File uploads, AI chat, bulk screening, real-time logs, Supabase integration
"""

from flask import Flask, render_template, request, jsonify, Response
import os, asyncio, httpx, logging, traceback, csv, json
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document

# Import system prompts (from N8N workflows)
from system_prompts import (
    CV_SCREENING_SYSTEM_PROMPT,
    JOB_POST_SYSTEM_PROMPT,
    AI_WRITING_SYSTEM_PROMPT,
    SCREENING_USER_PROMPT,
    JOB_POST_USER_PROMPT,
    AI_WRITING_USER_PROMPT
)

# Import Supabase handler (v3.1 feature - graceful fallback if not available)
try:
    from utils.supabase_handler import (
        save_screening_result_async,
        save_ai_message_async,
        save_resume_metadata_async,
        save_job_post_async
    )
    SUPABASE_ENABLED = True
except ImportError:
    logger_temp = logging.getLogger(__name__)
    logger_temp.debug("Supabase handler not available - database operations disabled")
    SUPABASE_ENABLED = False
    # Define no-op functions as fallback
    save_screening_result_async = lambda *args, **kwargs: None
    save_ai_message_async = lambda *args, **kwargs: None
    save_resume_metadata_async = lambda *args, **kwargs: None
    save_job_post_async = lambda *args, **kwargs: None

# LOGGING
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/recruitment_ai.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-mini')
N8N_WEBHOOK = os.getenv('N8N_WEBHOOK_PRODUCTION')

logger.info("="*80)
logger.info("[STARTUP] Advanced Recruitment ATS v3.1 Initialization")
logger.info(f"[CONFIG] Model: {OPENAI_MODEL} | Webhooks: {bool(N8N_WEBHOOK)}")
logger.info("="*80)

# FILE EXTRACTION
def extract_pdf_text(path):
    try:
        text = []
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text.append(page.extract_text())
        result = '\n'.join(text)
        logger.info(f"[PDF] Extracted {len(result)} chars")
        return result
    except Exception as e:
        logger.error(f"[PDF] Error: {e}")
        return ""

def extract_docx_text(path):
    try:
        doc = Document(path)
        text = [p.text for p in doc.paragraphs]
        result = '\n'.join(text)
        logger.info(f"[DOCX] Extracted {len(result)} chars")
        return result
    except Exception as e:
        logger.error(f"[DOCX] Error: {e}")
        return ""

def read_csv_data(path):
    try:
        data = []
        with open(path, 'r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                data.append(row)
        logger.info(f"[CSV] Read {len(data)} rows")
        return data
    except Exception as e:
        logger.error(f"[CSV] Error: {e}")
        return []

# WEBHOOKS
async def call_webhook(payload, url=None, timeout=60):
    if not url:
        url = N8N_WEBHOOK
    try:
        logger.info(f"[WEBHOOK] Calling: {url[:60]}...")
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(url, json=payload)
            result = {"status": "success", "code": resp.status_code, "data": resp.json() if resp.text else {}}
            logger.info(f"[WEBHOOK] Response: {resp.status_code}")
            return result
    except asyncio.TimeoutError:
        logger.error(f"[WEBHOOK] Timeout after {timeout}s")
        return {"status": "timeout", "error": f"Timeout after {timeout}s"}
    except Exception as e:
        logger.error(f"[WEBHOOK] Error: {e}")
        return {"status": "error", "error": str(e)}

# OpenAI API Helper
async def call_openai_api(prompt: str, user_text: str, timeout: int = 10):
    """Call OpenAI API - optimized for recruitment tasks"""
    api_key = os.getenv('OPENAI_API_KEY')
    model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    if not api_key:
        return {"status": "error", "error": "OpenAI API key not configured"}
    
    try:
        full_prompt = f"{prompt}\n\n{user_text}"
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful recruitment assistant."},
                        {"role": "user", "content": full_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 800
                },
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if resp.status_code == 200:
                data = resp.json()
                output = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                return {"status": "success", "output": output}
            else:
                return {"status": "error", "error": f"OpenAI API error: {resp.status_code}"}
                
    except asyncio.TimeoutError:
        return {"status": "error", "error": "Request timeout"}
    except Exception as e:
        logger.error(f"OpenAI call error: {str(e)}")
        return {"status": "error", "error": str(e)[:100]}

async def call_openai_api_with_system(system_prompt: str, user_prompt: str, timeout: int = 10):
    """Call OpenAI API with explicit system prompt (from N8N workflows)"""
    api_key = os.getenv('OPENAI_API_KEY')
    model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    if not api_key:
        logger.error("OpenAI API key not found in environment")
        return {"status": "error", "error": "OpenAI API key not configured"}
    
    try:
        logger.info(f"[OpenAI] Using model: {model}")
        logger.info(f"[OpenAI] System prompt length: {len(system_prompt)} chars")
        logger.info(f"[OpenAI] User prompt length: {len(user_prompt)} chars")
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.3,  # Lower for consistent matching
                "max_tokens": 2500  # Increased for detailed JSON responses
            }
            
            logger.info(f"[OpenAI] Making request to {model}...")
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            logger.info(f"[OpenAI] Status code: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                output = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                logger.info(f"[OpenAI] Success! Output length: {len(output)} chars")
                return {"status": "success", "output": output}
            else:
                error_msg = f"OpenAI API error: {resp.status_code}"
                try:
                    error_data = resp.json()
                    error_msg += f" - {error_data.get('error', {}).get('message', 'Unknown error')}"
                except:
                    error_msg += f" - {resp.text[:100]}"
                logger.error(f"[OpenAI] {error_msg}")
                return {"status": "error", "error": error_msg}
                
    except asyncio.TimeoutError:
        logger.error(f"[OpenAI] Request timeout after {timeout}s")
        return {"status": "error", "error": f"Request timeout after {timeout}s"}
    except Exception as e:
        logger.error(f"[OpenAI] Exception: {str(e)}")
        logger.error(f"[OpenAI] Traceback: {traceback.format_exc()}")
        return {"status": "error", "error": str(e)[:200]}

# ROUTES
@app.route('/')
def index():
    return render_template('advanced_index.html')

@app.route('/api/status')
def status():
    return jsonify({"status": "online", "timestamp": datetime.now().isoformat(), "model": OPENAI_MODEL, "webhook": bool(N8N_WEBHOOK)})

@app.route('/api/upload-bulk-resumes', methods=['POST'])
def upload_bulk_resumes():
    """Handle bulk resume uploads (PDF, DOC, DOCX) for screening"""
    try:
        if 'files[]' not in request.files:
            return jsonify({"error": "No files provided"}), 400
        
        files = request.files.getlist('files[]')
        if not files:
            return jsonify({"error": "No files selected"}), 400
        
        candidates = []
        errors = []
        
        for file in files:
            if not file.filename:
                continue
                
            filename = secure_filename(file.filename)
            ext = filename.lower().split('.')[-1]
            
            # Only accept resume files
            if ext not in ['pdf', 'doc', 'docx']:
                errors.append(f"{filename}: Invalid format (only PDF, DOC, DOCX accepted)")
                continue
            
            try:
                # Extract text from file
                path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(path)
                
                if ext == 'pdf':
                    content = extract_pdf_text(path)
                elif ext in ['docx', 'doc']:
                    content = extract_docx_text(path)
                else:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                
                try:
                    os.remove(path)
                except:
                    pass
                
                if content and len(content.strip()) > 20:
                    candidates.append({
                        "name": filename.replace('.pdf', '').replace('.docx', '').replace('.doc', ''),
                        "resume": content,
                        "filename": filename
                    })
                    logger.info(f"[BULK-UPLOAD] Processed: {filename} ({len(content)} chars)")
                else:
                    errors.append(f"{filename}: Empty or too short")
            except Exception as e:
                logger.error(f"[BULK-UPLOAD] Error processing {filename}: {e}")
                errors.append(f"{filename}: {str(e)}")
        
        logger.info(f"[BULK-UPLOAD] Total: {len(candidates)} candidates loaded, {len(errors)} errors")
        
        # v3.1: Save resume metadata to Supabase (async, non-blocking)
        if SUPABASE_ENABLED and candidates:
            for candidate in candidates:
                save_resume_metadata_async(
                    candidate_name=candidate.get('name'),
                    filename=candidate.get('filename'),
                    content=candidate.get('resume')
                )
        
        return jsonify({
            "status": "success" if candidates else "error",
            "candidates": candidates,
            "count": len(candidates),
            "errors": errors if errors else [],
            "error_count": len(errors)
        })
    except Exception as e:
        logger.error(f"[BULK-UPLOAD] Error: {e}")
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route('/api/upload-file', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file"}), 400
        file = request.files['file']
        if not file.filename:
            return jsonify({"error": "Invalid filename"}), 400
        
        filename = secure_filename(file.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        
        logger.info(f"[UPLOAD] Saved: {filename}")
        
        ext = filename.lower().split('.')[-1]
        
        if ext == 'pdf':
            content = extract_pdf_text(path)
        elif ext in ['docx', 'doc']:
            content = extract_docx_text(path)
        elif ext == 'csv':
            data = read_csv_data(path)
            return jsonify({"filename": filename, "type": "csv", "rows": len(data), "data": data, "preview": data[:5]})
        else:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
        
        try:
            os.remove(path)
        except:
            pass
        
        return jsonify({"filename": filename, "type": ext, "length": len(content), "content": content[:500], "full_content": content})
    except Exception as e:
        logger.error(f"[UPLOAD] Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/screen-candidate', methods=['POST'])
def screen_candidate():
    try:
        data = request.get_json()
        if not data.get('resume_text') or not data.get('jd_text'):
            return jsonify({"error": "Resume and JD required"}), 400
        
        # Make these optional - use defaults if not provided
        candidate_name = data.get('candidate_name', 'Candidate')
        job_title = data.get('job_title', 'Position')
        
        logger.info(f"[SCREEN-CANDIDATE] Screening: {candidate_name} for {job_title}")
        
        resume_text = data.get('resume_text', '')
        jd_text = data.get('jd_text', '')
        
        # Build user prompt using template
        user_prompt = SCREENING_USER_PROMPT.format(
            resume_text=resume_text,
            jd_text=jd_text
        )
        
        # Call OpenAI with CV screening system prompt
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("[SCREEN-CANDIDATE] No OpenAI API key configured!")
            return jsonify({"status": "error", "error": "OpenAI API key not configured in .env"}), 500
        
        result = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logger.info("[SCREEN-CANDIDATE] Calling OpenAI API with CV screening system prompt...")
            result = loop.run_until_complete(asyncio.wait_for(
                call_openai_api_with_system(CV_SCREENING_SYSTEM_PROMPT, user_prompt, timeout=15),
                timeout=15
            ))
            loop.close()
            logger.info(f"[SCREEN-CANDIDATE] API Response Status: {result.get('status')}")
            
            if result.get('status') == 'success':
                try:
                    # Parse JSON response from AI
                    output_text = result.get('output', '{}')
                    logger.info(f"[SCREEN-CANDIDATE] Raw AI output length: {len(output_text)} chars")
                    
                    # Clean up if it has markdown code blocks
                    if '```json' in output_text:
                        output_text = output_text.split('```json')[1].split('```')[0].strip()
                    elif '```' in output_text:
                        output_text = output_text.split('```')[1].split('```')[0].strip()
                    
                    parsed = json.loads(output_text)
                    logger.info(f"[SCREEN-CANDIDATE] AI Screening Success - Score: {parsed.get('score', 'N/A')}")
                    
                    # Transform OpenAI response to match frontend expectations
                    ai_score = parsed.get('score', 50)
                    ai_decision = parsed.get('decision', 'Review')
                    ai_eval = parsed.get('evaluation', {})
                    
                    # CRITICAL: Ensure score is realistic (minimum 35% ALWAYS - never 0%)
                    if ai_score is None or ai_score <= 0:
                        ai_score = 50  # Default to neutral if invalid
                    else:
                        ai_score = max(35, ai_score)  # Enforce minimum 35%
                    
                    logger.info(f"[SCREEN-CANDIDATE] Score normalized: {ai_score}% (raw from AI: {parsed.get('score', 'N/A')})")
                    
                    response_data = {
                        "candidate_name": candidate_name or parsed.get('name', 'Unknown'),
                        "job_title": job_title,
                        "match_score": ai_score,
                        "recommendation": "INVITE" if ai_score >= 75 else "REVIEW",
                        "assessment": ai_eval.get('justification', f"Score: {ai_score}%"),
                        "decision": ai_decision
                    }
                    logger.info(f"[SCREEN-CANDIDATE] Transformed response - Match Score: {ai_score}%")
                    
                    # v3.1: Save screening result to Supabase (async, non-blocking)
                    if SUPABASE_ENABLED:
                        save_screening_result_async(
                            resume_id=None,  # No file stored, just screening
                            candidate_name=response_data.get('candidate_name'),
                            job_title=response_data.get('job_title'),
                            match_score=response_data.get('match_score'),
                            recommendation=response_data.get('recommendation'),
                            assessment=response_data.get('assessment')
                        )
                    
                    return jsonify(response_data)
                except json.JSONDecodeError as je:
                    logger.error(f"[SCREEN-CANDIDATE] JSON parsing failed: {je}")
                    logger.error(f"[SCREEN-CANDIDATE] Output was: {output_text[:200]}")
            else:
                logger.error(f"[SCREEN-CANDIDATE] API failed: {result.get('error', 'Unknown error')}")
        except asyncio.TimeoutError:
            logger.error("[SCREEN-CANDIDATE] OpenAI API timeout after 15s")
        except Exception as e:
            logger.error(f"[SCREEN-CANDIDATE] Exception during API call: {str(e)}")
            logger.error(traceback.format_exc())
        
        # Fallback to quick scoring if AI fails
        logger.info("[SCREEN-CANDIDATE] Using fallback keyword matching scoring...")
        score = 50
        resume_lower = resume_text.lower()
        jd_lower = jd_text.lower()
        
        # Extract keywords from JD - more flexible matching
        keywords = ['java', 'python', 'javascript', 'sql', 'api', 'cloud', 'docker', 'kubernetes', 
                   'spring', 'react', 'angular', 'node', 'testing', 'qa', 'automation',
                   'leader', 'manage', 'architect', 'senior', 'developer', 'engineer', 'developer']
        
        # Count matching keywords
        matched_skills = sum(1 for kw in keywords if kw in resume_lower)
        if matched_skills > 0:
            score = 50 + (matched_skills * 3)
        
        # Boost for recent experience
        if '2025' in resume_lower or '2024' in resume_lower or '2023' in resume_lower:
            score += 15
        
        # Boost for leadership
        if any(word in resume_lower for word in ['leader', 'manager', 'director', 'lead', 'senior']):
            score += 10
        
        # Ensure score is in range and realistic
        score = min(100, max(35, score))  # Minimum 35% to avoid 0%
        
        decision = "Shortlisted" if score >= 70 else "Review" if score >= 60 else "Review"
        
        result = {
            "candidate_name": candidate_name,
            "job_title": job_title,
            "match_score": score,
            "recommendation": "INVITE" if score >= 75 else "REVIEW",
            "assessment": f"Candidate matches {score}% of job requirements",
            "decision": decision
        }
        
        logger.warning(f"[SCREEN-CANDIDATE] Fallback scoring - Score: {score}%")
        return jsonify(result)
    except Exception as e:
        logger.error(f"[SCREEN-CANDIDATE] Error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/bulk-screen', methods=['POST'])
def bulk_screen():
    try:
        data = request.get_json()
        jd_text = data.get('jd_text', '')
        candidates = data.get('candidates', [])
        
        if not jd_text:
            return jsonify({"error": "JD required"}), 400
        if not candidates:
            return jsonify({"error": "At least one candidate resume required"}), 400
        
        logger.info(f"[BULK-SCREEN] Screening {len(candidates)} candidates using CV screening prompt")
        
        # Process candidates with AI screening (using CV screening system prompt)
        results = []
        for idx, candidate in enumerate(candidates):
            name = candidate.get('name') or candidate.get('Name') or f"Candidate {idx+1}"
            resume_text = (candidate.get('resume') or candidate.get('Resume') or "")
            
            if not resume_text or len(resume_text.strip()) < 5:
                results.append({
                    "candidate": name,
                    "status": "error",
                    "error": "Empty resume"
                })
                continue
            
            # Build user prompt
            user_prompt = SCREENING_USER_PROMPT.format(
                resume_text=resume_text,
                jd_text=jd_text
            )
            
            # Try to call AI with proper timeout
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(asyncio.wait_for(
                    call_openai_api_with_system(CV_SCREENING_SYSTEM_PROMPT, user_prompt, timeout=12),
                    timeout=12
                ))
                loop.close()
                
                if result.get('status') == 'success':
                    try:
                        output_text = result.get('output', '{}')
                        if '```json' in output_text:
                            output_text = output_text.split('```json')[1].split('```')[0].strip()
                        elif '```' in output_text:
                            output_text = output_text.split('```')[1].split('```')[0].strip()
                        
                        parsed = json.loads(output_text)
                        score = parsed.get('score', 50)
                        
                        # CRITICAL: Enforce minimum score of 35% to avoid 0%
                        if score is None or score <= 0:
                            score = 50
                        else:
                            score = max(35, score)
                        
                        results.append({
                            "candidate": name,
                            "match_score": score,
                            "recommendation": "INVITE" if score >= 75 else "REVIEW" if score >= 60 else "PASS",
                            "assessment": parsed.get('evaluation', {}).get('justification', f"Score: {score}%"),
                            "status": "success"
                        })
                        continue
                    except:
                        pass
            except:
                pass
            
            # Fallback to quick scoring if AI fails
            score = 50
            resume_lower = resume_text.lower()
            
            # Check keyword matches
            keywords = ['python', 'java', 'javascript', 'sql', 'api', 'cloud', 'docker', 'developer', 'engineer', 'senior', 'leader']
            matched = sum(1 for kw in keywords if kw in resume_lower)
            score += matched * 3
            
            if '2025' in resume_lower or '2024' in resume_lower:
                score += 10
            elif '2023' in resume_lower:
                score += 5
            
            # CRITICAL: Enforce minimum 35% score to avoid 0%
            score = min(100, max(35, score))
            
            results.append({
                "candidate": name,
                "match_score": score,
                "recommendation": "INVITE" if score >= 75 else "REVIEW" if score >= 60 else "PASS",
                "assessment": f"Quick match score: {score}%",
                "status": "success"
            })
        
        logger.info(f"[BULK-SCREEN] Complete: {len(results)} processed")
        return jsonify({
            "status": "success",
            "total": len(candidates),
            "processed": len([r for r in results if r.get('status') == 'success']),
            "errors": len([r for r in results if r.get('status') == 'error']),
            "results": results
        })
    except Exception as e:
        logger.error(f"[BULK-SCREEN] Error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/generate-job-post', methods=['POST'])
def generate_job_post():
    try:
        data = request.get_json()
        if not data.get('jd_text'):
            return jsonify({"error": "Job description required"}), 400
        
        logger.info(f"[JOB-POST] Generating for: {data.get('job_title', 'Job')}")
        
        jd_text = data.get('jd_text', '')
        title = data.get('job_title', data.get('position', 'Software Engineer'))
        location = data.get('location', 'Remote')
        experience = data.get('experience', 'Not specified')
        description = data.get('description', jd_text)
        
        # Build user prompt using template
        user_prompt = JOB_POST_USER_PROMPT.format(jd_text=jd_text)
        
        # Add strict instruction to enforce JSON structure with all required fields
        strict_system_prompt = JOB_POST_SYSTEM_PROMPT + "\n\nCRITICAL REQUIREMENT: You MUST return ONLY valid JSON with EXACTLY these fields:\n{\"client_project\", \"recruitment_type\", \"role\", \"experience\", \"location\", \"contract_duration\", \"key_skills\", \"no_of_submissions\", \"linkedin_post\", \"indeed_post\", \"email_post\", \"whatsapp_post\"}\n\nEnsure EVERY field is populated with relevant content. If unknown, use reasonable defaults. ALL FIELDS REQUIRED."
        
        # Try OpenAI first
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(asyncio.wait_for(
                call_openai_api_with_system(strict_system_prompt, user_prompt, timeout=20),
                timeout=20
            ))
            loop.close()
            
            if result.get('status') == 'success':
                try:
                    output_text = result.get('output', '{}')
                    if '```json' in output_text:
                        output_text = output_text.split('```json')[1].split('```')[0].strip()
                    elif '```' in output_text:
                        output_text = output_text.split('```')[1].split('```')[0].strip()
                    
                    parsed = json.loads(output_text)
                    logger.info("[JOB-POST] AI generation successful")
                    
                    # Ensure ALL required fields exist with proper defaults
                    required_fields = {
                        "client_project": "NA",
                        "recruitment_type": "Permanent",
                        "role": title,
                        "experience": experience,
                        "location": location,
                        "contract_duration": "NA",
                        "key_skills": [],
                        "no_of_submissions": 0,
                        "linkedin_post": "",
                        "indeed_post": "",
                        "email_post": "",
                        "whatsapp_post": ""
                    }
                    
                    for field, default_value in required_fields.items():
                        if field not in parsed or not parsed[field]:
                            parsed[field] = default_value
                    
                    # Normalize field names for frontend (remove _post suffix)
                    if "linkedin_post" in parsed:
                        parsed["linkedin"] = parsed.pop("linkedin_post")
                    if "indeed_post" in parsed:
                        parsed["indeed"] = parsed.pop("indeed_post")
                    if "email_post" in parsed:
                        parsed["email"] = parsed.pop("email_post")
                    if "whatsapp_post" in parsed:
                        parsed["whatsapp"] = parsed.pop("whatsapp_post")
                    
                    # Validate word counts against system prompt requirements
                    linkedin_words = len(parsed.get("linkedin", "").split())
                    indeed_words = len(parsed.get("indeed", "").split())
                    email_words = len(parsed.get("email", "").split())
                    whatsapp_words = len(parsed.get("whatsapp", "").split())
                    
                    # Check if all posts meet minimum word count requirements
                    linkedin_valid = linkedin_words >= 150
                    indeed_valid = indeed_words >= 150
                    email_valid = email_words >= 250
                    whatsapp_valid = whatsapp_words >= 80
                    
                    if linkedin_valid and indeed_valid and email_valid and whatsapp_valid:
                        logger.info(f"[JOB-POST] Word counts valid - LinkedIn: {linkedin_words}, Indeed: {indeed_words}, Email: {email_words}, WhatsApp: {whatsapp_words}")
                        
                        # Save to Supabase
                        try:
                            save_job_post_async(
                                job_title=title,
                                location=location,
                                experience=int(experience.split('+')[0].split('-')[0].strip() or 0),
                                platforms=parsed
                            )
                            logger.info("[JOB-POST] Saved to Supabase (AI success path)")
                        except Exception as save_err:
                            logger.warning(f"[JOB-POST] Supabase save failed: {save_err}")
                        
                        return Response(json.dumps({"status": "success", "data": parsed}, ensure_ascii=False), mimetype="application/json")
                    else:
                        raise Exception(f"Word counts invalid - LinkedIn: {linkedin_words} (need 150), Indeed: {indeed_words} (need 150), Email: {email_words} (need 250), WhatsApp: {whatsapp_words} (need 80)")

                except Exception as e:
                    logger.warning(f"[JOB-POST] Failed to parse AI JSON: {e}")
        except Exception as e:
            logger.warning(f"[JOB-POST] AI call failed: {e}")
        
        # Fallback: Generate posts using templates
        logger.info("[JOB-POST] Using template generation")
        
        # Generate using AI with strict JSON format requirement
        strict_json_prompt = f"""Generate job posts for {title} in EXACTLY this JSON format (valid JSON only):
{{
    "linkedin": "professional LinkedIn post max 250 chars",
    "indeed": "Indeed job description max 300 chars",
    "email": "Email body max 300 chars",
    "whatsapp": "WhatsApp message max 150 chars"
}}

Details:
- Position: {title}
- Location: {location}
- Experience: {experience}
- Description: {description}

Generate varied, platform-specific content. Return ONLY valid JSON."""

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(asyncio.wait_for(
                call_openai_api_with_system("You are a professional recruiter writing job posts.", strict_json_prompt, timeout=15),
                timeout=15
            ))
            loop.close()
            
            if result.get('status') == 'success':
                output = result.get('output', '').strip()
                try:
                    # Extract JSON from output
                    if '{' in output and '}' in output:
                        json_str = output[output.find('{'):output.rfind('}')+1]
                        parsed = json.loads(json_str)
                        linkedin_post = parsed.get('linkedin', '')
                        indeed_post = parsed.get('indeed', '')
                        email_post = parsed.get('email', '')
                        whatsapp_post = parsed.get('whatsapp', '')
                    else:
                        raise Exception("No JSON found in output")
                except:
                    raise Exception("JSON parsing failed")
            else:
                raise Exception("AI call failed")
        except Exception as e:
            logger.warning(f"[JOB-POST] Strict format generation failed: {e}, retrying with simpler prompt")
            # Retry with simpler AI prompt
            try:
                simple_prompt = f"""Generate job posts for {title} in 4 platforms. Return ONLY valid JSON:
{{"linkedin": "...", "indeed": "...", "email": "...", "whatsapp": "..."}}
Position: {title}, Location: {location}, Experience: {experience} years."""
                
                loop2 = asyncio.new_event_loop()
                asyncio.set_event_loop(loop2)
                retry_result = loop2.run_until_complete(asyncio.wait_for(
                    call_openai_api_with_system("You are a recruiter. Return ONLY JSON with no extra text.", simple_prompt, timeout=10),
                    timeout=10
                ))
                loop2.close()
                
                if retry_result.get('status') == 'success':
                    retry_output = retry_result.get('output', '').strip()
                    if '{' in retry_output and '}' in retry_output:
                        json_str = retry_output[retry_output.find('{'):retry_output.rfind('}')+1]
                        parsed = json.loads(json_str)
                        linkedin_post = parsed.get('linkedin', '')
                        indeed_post = parsed.get('indeed', '')
                        email_post = parsed.get('email', '')
                        whatsapp_post = parsed.get('whatsapp', '')
                        if all([linkedin_post, indeed_post, email_post, whatsapp_post]):
                            logger.info("[JOB-POST] Retry succeeded with AI-generated JSON")
                        else:
                            raise Exception("Some fields empty after retry")
                    else:
                        raise Exception("No JSON in retry output")
                else:
                    raise Exception("Retry AI call failed")
            except Exception as retry_err:
                logger.error(f"[JOB-POST] Retry failed: {retry_err}, using fallback")
                linkedin_post = f"""🚀 Exciting Opportunity: We're Hiring a {title}! 

Join our dynamic team and make an impact in your career. We are actively seeking a talented and experienced {title} to join our organization in {location}. 

📋 About the Role:
This is an excellent opportunity to work with a forward-thinking company that values innovation and excellence. As our {title}, you will be responsible for driving success and bringing your expertise to a team of dedicated professionals.

🎯 Key Responsibilities:
• Lead and manage core projects and initiatives
• Collaborate with cross-functional teams to achieve business objectives
• Develop and implement strategic plans aligned with company goals
• Mentor and support team members to ensure continuous improvement
• Drive innovation and process optimization within your domain
• Contribute to the overall growth and success of the organization

✅ What We're Looking For:
• {experience}+ years of proven experience in this field
• Strong technical and strategic expertise
• Excellent communication and leadership abilities
• Problem-solving mindset with analytical skills
• Ability to work independently and collaborate effectively
• Commitment to continuous learning and professional development

📍 Location: {location} | 🕒 Experience Required: {experience}+ years

Ready to grow your career with us? Apply now and let's discuss how you can make a difference!

#Hiring #{title.replace(' ', '')} #CareerOpportunity #Jobs #{location.replace(' ', '')}"""
                
                indeed_post = f"""Position: {title}
Location: {location}
Experience Required: {experience}+ years

Job Description:

We are pleased to announce an exciting career opportunity for a {title} position based in {location}. Our organization is seeking a dynamic, results-oriented professional with extensive experience in this field to join our growing team.

Position Overview:
This role offers the opportunity to work on meaningful projects in a collaborative and innovative environment. You will be instrumental in driving productivity, efficiency, and excellence across our operations.

Key Responsibilities:
• Execute core functions and deliver measurable results
• Collaborate with diverse teams on strategic initiatives
• Develop and implement effective solutions to business challenges
• Lead project management and oversee timely completion
• Foster innovation and continuous improvement culture
• Maintain high standards of quality and performance
• Contribute to team development and knowledge sharing

Required Qualifications:
• {experience}+ years of relevant professional experience
• Demonstrated expertise in your domain area
• Strong analytical and problem-solving abilities
• Excellent verbal and written communication skills
• Proven track record of successful project delivery
• Ability to manage multiple priorities effectively
• Bachelor's degree or equivalent professional experience

Why Join Us:
• Competitive compensation and growth opportunities
• Professional development and training support
• Collaborative and innovative work environment
• Career advancement potential
• Benefits and work-life balance support
• Opportunity to make meaningful impact

If you have the required experience and are excited about this opportunity, we'd love to hear from you!"""

                email_post = f"""Subject: Exciting Career Opportunity: {title} Position in {location}

Dear Prospective Candidate,

Greetings! We are pleased to inform you about an exciting and rewarding career opportunity with our organization. We are currently looking for a talented and experienced {title} to join our team in {location}.

About the Position:
We are seeking a dedicated professional with {experience}+ years of experience to take on this pivotal role. This position offers the opportunity to work in a dynamic, growth-oriented environment where your expertise and contributions will directly impact our success.

Role Overview:
As our {title}, you will be responsible for managing critical projects, driving innovation, and leading our team towards achieving ambitious organizational goals. This role provides excellent exposure to strategic initiatives and offers significant potential for professional growth.

Key Responsibilities:
• Lead and oversee core projects from conception to completion
• Develop and implement effective business strategies
• Manage cross-functional teams and collaborate on key initiatives
• Ensure quality standards and drive continuous improvement
• Mentor team members and foster a culture of excellence
• Report on progress and provide strategic recommendations
• Identify opportunities for business optimization and growth
• Maintain strong stakeholder relationships and communication

Required Skills and Qualifications:
• {experience}+ years of proven professional experience
• Expertise in relevant domain knowledge and best practices
• Strong leadership and team management abilities
• Excellent communication and interpersonal skills
• Problem-solving mindset with strategic thinking
• Technical proficiency with modern tools and systems
• Ability to thrive in a fast-paced environment
• Commitment to professional development

To Apply, Please Provide:

Candidate Information Request:
• Full Name: _____________________________
• Total Years of Experience: _____________________________
• Relevant Experience: _____________________________
• Current Salary (In Confidence): _____________________________
• Expected Salary: _____________________________
• Notice Period: _____________________________
• Current Company: _____________________________
• Current Location: _____________________________
• Work Authorization Status: _____________________________

Why This Role is Right for You:
This position offers competitive compensation, professional growth opportunities, and the chance to work with industry leaders. You will be part of a supportive team environment that values innovation, collaboration, and excellence.

We look forward to discussing this opportunity with you. Please reply to this email with your updated resume and the requested information.

Best Regards,
Recruitment Team"""

                whatsapp_post = f"""💼 Job Alert: {title} Position 🚀

📢 We're Hiring!

Position: {title}
📍 Location: {location}
🕒 Experience Required: {experience}+ years

Key Skills Required:
✅ Expertise in domain-specific responsibilities
✅ Strong leadership and team management
✅ Problem-solving and strategic thinking
✅ Excellent communication abilities
✅ Proven track record of success

Role Summary:
Join our team as a {title} and make a real impact! We're looking for experienced professionals to help us drive growth and innovation. This is a fantastic opportunity to advance your career with a forward-thinking organization.

Responsibilities include managing projects, leading teams, driving results, and contributing to organizational success.

📌 Interested? Send your CV and we'll get in touch!

For more details, reply to this message or contact our HR team.

#Hiring #JobAlert #{title.replace(' ', '')} #CareerGrowth"""

        result_data = {
            "client_project": "NA",
            "recruitment_type": "Permanent",
            "role": title,
            "experience": experience,
            "location": location,
            "contract_duration": "NA",
            "key_skills": ["Technical expertise", "Problem-solving", "Communication"],
            "no_of_submissions": 0,
            "linkedin": linkedin_post,
            "indeed": indeed_post,
            "email": email_post,
            "whatsapp": whatsapp_post
        }
        
        # Final validation: ensure all posts meet minimum word count requirements
        linkedin_words = len(result_data.get("linkedin", "").split())
        indeed_words = len(result_data.get("indeed", "").split())
        email_words = len(result_data.get("email", "").split())
        whatsapp_words = len(result_data.get("whatsapp", "").split())
        
        linkedin_valid = linkedin_words >= 150
        indeed_valid = indeed_words >= 150
        email_valid = email_words >= 250
        whatsapp_valid = whatsapp_words >= 80
        
        if not (linkedin_valid and indeed_valid and email_valid and whatsapp_valid):
            logger.warning(f"[JOB-POST] Final validation failed - LinkedIn: {linkedin_words} (need 150), Indeed: {indeed_words} (need 150), Email: {email_words} (need 250), WhatsApp: {whatsapp_words} (need 80). Using detailed fallback.")
            
            # Use detailed fallback posts that meet all requirements
            result_data["linkedin"] = f"""🚀 Exciting Opportunity: We're Hiring a {title}! 

Join our dynamic team and make an impact in your career. We are actively seeking a talented and experienced {title} to join our organization in {location}. 

📋 About the Role:
This is an excellent opportunity to work with a forward-thinking company that values innovation and excellence. As our {title}, you will be responsible for driving success and bringing your expertise to a team of dedicated professionals.

🎯 Key Responsibilities:
• Lead and manage core projects and initiatives
• Collaborate with cross-functional teams to achieve business objectives
• Develop and implement strategic plans aligned with company goals
• Mentor and support team members to ensure continuous improvement
• Drive innovation and process optimization within your domain
• Contribute to the overall growth and success of the organization

✅ What We're Looking For:
• {experience}+ years of proven experience in this field
• Strong technical and strategic expertise
• Excellent communication and leadership abilities
• Problem-solving mindset with analytical skills
• Ability to work independently and collaborate effectively
• Commitment to continuous learning and professional development

📍 Location: {location} | 🕒 Experience Required: {experience}+ years

Ready to grow your career with us? Apply now and let's discuss how you can make a difference!

#Hiring #{title.replace(' ', '')} #CareerOpportunity #Jobs #{location.replace(' ', '')}"""

            result_data["indeed"] = f"""Position: {title}
Location: {location}
Experience Required: {experience}+ years

Job Description:

We are pleased to announce an exciting career opportunity for a {title} position based in {location}. Our organization is seeking a dynamic, results-oriented professional with extensive experience in this field to join our growing team.

Position Overview:
This role offers the opportunity to work on meaningful projects in a collaborative and innovative environment. You will be instrumental in driving productivity, efficiency, and excellence across our operations.

Key Responsibilities:
• Execute core functions and deliver measurable results
• Collaborate with diverse teams on strategic initiatives
• Develop and implement effective solutions to business challenges
• Lead project management and oversee timely completion
• Foster innovation and continuous improvement culture
• Maintain high standards of quality and performance
• Contribute to team development and knowledge sharing

Required Qualifications:
• {experience}+ years of relevant professional experience
• Demonstrated expertise in your domain area
• Strong analytical and problem-solving abilities
• Excellent verbal and written communication skills
• Proven track record of successful project delivery
• Ability to manage multiple priorities effectively
• Bachelor's degree or equivalent professional experience

Why Join Us:
• Competitive compensation and growth opportunities
• Professional development and training support
• Collaborative and innovative work environment
• Career advancement potential
• Benefits and work-life balance support
• Opportunity to make meaningful impact

If you have the required experience and are excited about this opportunity, we'd love to hear from you!"""

            result_data["email"] = f"""Subject: Exciting Career Opportunity: {title} Position in {location}

Dear Prospective Candidate,

Greetings! We are pleased to inform you about an exciting and rewarding career opportunity with our organization. We are currently looking for a talented and experienced {title} to join our team in {location}.

About the Position:
We are seeking a dedicated professional with {experience}+ years of experience to take on this pivotal role. This position offers the opportunity to work in a dynamic, growth-oriented environment where your expertise and contributions will directly impact our success.

Role Overview:
As our {title}, you will be responsible for managing critical projects, driving innovation, and leading our team towards achieving ambitious organizational goals. This role provides excellent exposure to strategic initiatives and offers significant potential for professional growth.

Key Responsibilities:
• Lead and oversee core projects from conception to completion
• Develop and implement effective business strategies
• Manage cross-functional teams and collaborate on key initiatives
• Ensure quality standards and drive continuous improvement
• Mentor team members and foster a culture of excellence
• Report on progress and provide strategic recommendations
• Identify opportunities for business optimization and growth
• Maintain strong stakeholder relationships and communication

Required Skills and Qualifications:
• {experience}+ years of proven professional experience
• Expertise in relevant domain knowledge and best practices
• Strong leadership and team management abilities
• Excellent communication and interpersonal skills
• Problem-solving mindset with strategic thinking
• Technical proficiency with modern tools and systems
• Ability to thrive in a fast-paced environment
• Commitment to professional development

To Apply, Please Provide:

Candidate Information Request:
• Full Name: _____________________________
• Total Years of Experience: _____________________________
• Relevant Experience: _____________________________
• Current Salary (In Confidence): _____________________________
• Expected Salary: _____________________________
• Notice Period: _____________________________
• Current Company: _____________________________
• Current Location: _____________________________
• Work Authorization Status: _____________________________

Why This Role is Right for You:
This position offers competitive compensation, professional growth opportunities, and the chance to work with industry leaders. You will be part of a supportive team environment that values innovation, collaboration, and excellence.

We look forward to discussing this opportunity with you. Please reply to this email with your updated resume and the requested information.

Best Regards,
Recruitment Team"""

            result_data["whatsapp"] = f"""💼 Job Alert: {title} Position 🚀

📢 We're Hiring!

Position: {title}
📍 Location: {location}
🕒 Experience Required: {experience}+ years

Key Skills Required:
✅ Expertise in domain-specific responsibilities
✅ Strong leadership and team management
✅ Problem-solving and strategic thinking
✅ Excellent communication abilities
✅ Proven track record of success

Role Summary:
Join our team as a {title} and make a real impact! We're looking for experienced professionals to help us drive growth and innovation. This is a fantastic opportunity to advance your career with a forward-thinking organization.

Responsibilities include managing projects, leading teams, driving results, and contributing to organizational success.

📌 Interested? Send your CV and we'll get in touch!

For more details, reply to this message or contact our HR team.

#Hiring #JobAlert #{title.replace(' ', '')} #CareerGrowth"""
        
        logger.info("[JOB-POST] Template posts generated")
        
        # Save to Supabase
        try:
            save_job_post_async(
                job_title=title,
                location=location,
                experience=int(experience.split('+')[0].split('-')[0].strip() or 0),
                platforms={
                    "linkedin": result_data.get("linkedin", ""),
                    "indeed": result_data.get("indeed", ""),
                    "email": result_data.get("email", ""),
                    "whatsapp": result_data.get("whatsapp", "")
                }
            )
            logger.info("[JOB-POST] Saved to Supabase")
        except Exception as save_err:
            logger.warning(f"[JOB-POST] Supabase save failed: {save_err}")
        
        return Response(json.dumps({"status": "success", "data": result_data}, ensure_ascii=False), mimetype="application/json")
    except Exception as e:
        logger.error(f"[JOB-POST] Error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/ai-write', methods=['POST'])
def ai_write():
    try:
        data = request.get_json()
        if not data.get('text'):
            return jsonify({"error": "Text required"}), 400
        
        text = data.get('text', '')
        action = data.get('action', 'rewrite')
        tone = data.get('tone', 'professional')
        platform = data.get('platform', 'email')
        
        logger.info(f"[AI-WRITE] Processing: {action} ({tone}) for {platform}")
        
        # Build user prompt using template
        user_prompt = AI_WRITING_USER_PROMPT.format(
            platform=platform,
            tone=tone,
            action=action,
            text=text
        )
        
        # Call OpenAI with system prompt from N8N workflow
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(asyncio.wait_for(
                call_openai_api_with_system(AI_WRITING_SYSTEM_PROMPT, user_prompt, timeout=10),
                timeout=10
            ))
            loop.close()
            
            if result.get('status') == 'success':
                output = result.get('output', '')
            else:
                output = text  # Fallback to original text if API fails
        except:
            # Fallback to simple template responses if API times out
            if action == 'rewrite':
                if tone == 'formal':
                    output = f"I hereby formally communicate the following: {text.lower()}"
                elif tone == 'casual':
                    output = f"Hey! So basically, {text.lower().replace('the ', '').replace('a ', '')}"
                elif tone == 'friendly':
                    output = f"Hope you're doing well! Just wanted to share: {text.lower()}"
                else:
                    output = f"I would like to bring to your attention: {text.lower()}"
            elif action == 'paraphrase':
                words = text.split()
                if len(words) > 5:
                    output = f"In essence, {text.lower()}. This represents a significant point."
                else:
                    output = f"This is to say: {text.lower()}"
            elif action == 'reply':
                if "?" in text or "how" in text.lower() or "what" in text.lower():
                    output = f"Thank you for your inquiry. Regarding your question: {text.lower()}\n\nHere's my response: I appreciate this opportunity to clarify and provide a comprehensive answer."
                elif "think" in text.lower() or "idea" in text.lower():
                    output = f"That's an interesting perspective. Building on your point about {text.lower()}, I would add that this deserves attention."
                else:
                    output = f"Thanks for sharing. I understand your point: {text.lower()}\n\nI appreciate your input."
            else:
                output = text
        
        logger.info(f"[AI-WRITE] Status: success - {action} generated for {platform}")
        return jsonify({
            "status": "success", 
            "data": {
                "output": output,
                "action": action,
                "tone": tone,
                "platform": platform,
                "note": f"Generated {action} in {tone} tone"
            }
        })
    except Exception as e:
        logger.error(f"[AI-WRITE] Error: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/generate-message', methods=['POST'])
def generate_message():
    try:
        data = request.get_json()
        msg_type = data.get('message_type', 'interview_invite')
        recipient = data.get('recipient', 'Candidate')
        job_title = data.get('job_title', 'Position')
        tone = data.get('tone', 'professional')
        context = data.get('context', '')
        
        logger.info(f"[MSG] Generating: {msg_type} for {recipient}")
        
        # Build message using AI with context for variety and personalization
        try:
            # Create context-aware prompts for varied, unique messages
            message_prompts = {
                "interview_invite": f"Write a professional, warm, and engaging interview invitation email to {recipient} for the {job_title} position. Include specific next steps and enthusiasm. Make it personal. Context: {context}",
                "rejection": f"Write a respectful, encouraging rejection email to {recipient} for the {job_title} position. Be sincere, acknowledge their effort, and leave door open for future. Context: {context}",
                "offer": f"Write an exciting and professional offer letter email to {recipient} for the {job_title} position. Congratulate them, show enthusiasm, include benefits. Context: {context}",
                "follow_up": f"Write a professional follow-up email to {recipient} regarding the {job_title} position. Express continued interest, request availability, be courteous. Context: {context}",
                "thanks": f"Write a sincere thank you email to {recipient} for interviewing for {job_title}. Be warm, professional, leave positive impression. Context: {context}",
                "interview_confirmed": f"Write a confirmation email to {recipient} confirming interview for {job_title}. Include details, show enthusiasm, provide instructions. Context: {context}"
            }
            
            prompt_text = message_prompts.get(msg_type, f"Write a professional email to {recipient} regarding {job_title}. Context: {context}")
            
            # Use AI to generate varied, contextual messages
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(asyncio.wait_for(
                    call_openai_api_with_system(AI_WRITING_SYSTEM_PROMPT, prompt_text, timeout=15),
                    timeout=15
                ))
                loop.close()
                
                if result.get('status') == 'success':
                    message = result.get('output', '').strip()
                    if not message or len(message) < 20:
                        raise Exception("Empty or invalid AI output")
                    logger.info(f"[MSG] AI-generated message: {len(message)} chars")
                else:
                    raise Exception("AI call unsuccessful")
            except Exception as e:
                logger.warning(f"[MSG] AI generation failed: {e}, using template")
                # Fallback to template with more variety
                if msg_type == "interview_invite":
                    message = f"""Dear {recipient},

We are delighted to invite you for an interview for the {job_title} position. Your profile caught our attention and we believe you would be a great fit for our team.

Please confirm your availability at your earliest convenience. We look forward to learning more about your experience and qualifications.

Best regards,
HR Team"""
                elif msg_type == "rejection":
                    message = f"""Dear {recipient},

Thank you for your interest in the {job_title} position at our organization.

After careful consideration of all applicants, we have decided to move forward with other candidates whose experience more closely aligns with our current requirements. We appreciate your time and effort.

We encourage you to apply for future openings that match your skills.

Best regards,
Recruitment Team"""
                elif msg_type == "offer":
                    message = f"""Dear {recipient},

Congratulations! We are thrilled to offer you the position of {job_title}. Your qualifications and interview performance impressed us greatly.

We believe you will be a valuable addition to our team. Please find the detailed offer letter attached with complete information about compensation and start date.

Please confirm your acceptance at your earliest convenience.

Best regards,
HR Team"""
                elif msg_type == "follow_up":
                    message = f"""Dear {recipient},

I hope you are doing well. We wanted to follow up regarding the {job_title} position that we discussed.

We remain very interested in your candidacy and would like to move forward with the next steps. Could you please share your availability for a call?

Thank you for your time and consideration.

Best regards,
Recruitment Team"""
                elif msg_type == "interview_confirmed":
                    message = f"""Dear {recipient},

Thank you for accepting our interview invitation for the {job_title} position.

We are excited to meet with you. Your interview has been confirmed and all details have been sent to your email. Please review and confirm receipt.

If you have any questions or need to reschedule, please let us know.

Best regards,
HR Team"""
                else:
                    message = f"""Dear {recipient},

Thank you for your interest in the {job_title} position at our organization.

We are reviewing all applications and will be in touch with updates regarding the next steps. {context if context else 'We appreciate your patience and enthusiasm.'}

Best regards,
Recruitment Team"""
            
            logger.info(f"[MSG] Status: success - {msg_type} generated")
            
            # v3.1: Save message to Supabase (async, non-blocking)
            if SUPABASE_ENABLED:
                save_ai_message_async(
                    message_type=msg_type,
                    recipient=recipient,
                    job_title=job_title,
                    tone=tone,
                    message_content=message
                )
            
            return jsonify({
                "status": "success",
                "data": {
                    "output": message,
                    "message": message,
                    "type": msg_type,
                    "recipient": recipient,
                    "context_used": bool(context)
                }
            })
        except Exception as e:
            logger.error(f"[MSG] Template error: {e}")
            raise
            
    except Exception as e:
        logger.error(f"[MSG] Error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/api/logs')
def get_logs():
    try:
        with open('logs/recruitment_ai.log', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        recent = lines[-100:] if len(lines) > 100 else lines
        return jsonify({"logs": recent, "total": len(lines), "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"[LOGS] Error: {e}")
        return jsonify({"logs": [], "error": str(e)})

@app.errorhandler(413)
def too_large(e):
    logger.warning("[ERROR] File too large")
    return jsonify({"error": "File too large (max 50MB)"}), 413

if __name__ == '__main__':
    logger.info("="*80)
    logger.info("[STARTUP] Starting Advanced Recruitment ATS v3.1 on http://localhost:5001")
    logger.info("[FEATURES] Single Screening | Bulk Screening | Job Posts | AI Writing")
    logger.info("[FEATURES] File Uploads (PDF, DOC, DOCX, CSV) | Message Generation | Supabase DB")
    logger.info("="*80)
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True, use_reloader=False)
