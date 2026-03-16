#!/usr/bin/env python3
"""
Advanced Recruitment ATS System - v3.0
Complete integration with all n8n workflows: Screening, Job Posting, AI Writing
Features: File uploads, AI chat, bulk processing, real-time logs, advanced analytics
"""

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
import asyncio
import traceback
import logging
import json
import csv
from datetime import datetime
from io import StringIO

import httpx
import PyPDF2
from docx import Document

# Import AI helpers
from utils.ai_helpers import (
    get_writing_prompt, get_message_prompt, enhance_prompt_with_context,
    call_openai_api, generate_multiple_messages, OPENAI_API_KEY as HELPER_OPENAI_KEY, OPENAI_MODEL as HELPER_OPENAI_MODEL
)

# ============================================================================
# SETUP LOGGING
# ============================================================================
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/recruitment_ai.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============================================================================
# CONFIGURATION
# ============================================================================
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
N8N_WEBHOOK = os.getenv('N8N_WEBHOOK_PRODUCTION')
CONTROL_PANEL_WEBHOOK = os.getenv('N8N_WEBHOOK_CONTROL_PANEL', N8N_WEBHOOK)

logger.info("[ATS v3.0] System initialized")
logger.info(f"[CONFIG] OpenAI Model: {OPENAI_MODEL}")
logger.info(f"[CONFIG] Webhooks configured: {bool(N8N_WEBHOOK)}")

# ============================================================================
# FILE UPLOAD HELPERS
# ============================================================================

def extract_pdf_text(file_path):
    """Extract text from PDF file"""
    try:
        text = []
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text.append(page.extract_text())
        result = '\n'.join(text)
        logger.info(f"[PDF] Extracted: {len(result)} chars")
        return result
    except Exception as e:
        logger.error(f"[PDF] Extraction failed: {str(e)}")
        return ""

def extract_docx_text(file_path):
    """Extract text from DOCX file"""
    try:
        doc = Document(file_path)
        text = [paragraph.text for paragraph in doc.paragraphs]
        result = '\n'.join(text)
        logger.info(f"✓ DOCX extracted: {len(result)} chars")
        return result
    except Exception as e:
        logger.error(f"✗ DOCX extraction failed: {str(e)}")
        return ""

def extract_text_file(file_path):
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        logger.info(f"✓ TXT extracted: {len(text)} chars")
        return text
    except Exception as e:
        logger.error(f"✗ TXT extraction failed: {str(e)}")
        return ""

def read_csv_data(file_path):
    """Read CSV file and return as list of dicts"""
    try:
        data = []
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                data.append(row)
        logger.info(f"✓ CSV read: {len(data)} rows")
        return data
    except Exception as e:
        logger.error(f"✗ CSV read failed: {str(e)}")
        return []

# ============================================================================
# WEBHOOK INTEGRATION
# ============================================================================

async def call_n8n_webhook(payload, webhook_url=None, timeout=60):
    """
    Call n8n webhook asynchronously
    Returns: {status: 'success'|'timeout'|'error', data: {...}, error: '...'}
    """
    if not webhook_url:
        webhook_url = N8N_WEBHOOK
    
    try:
        logger.info(f"→ Calling webhook: {webhook_url[:80]}...")
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(webhook_url, json=payload)
            result = {
                "status": "success",
                "code": response.status_code,
                "data": response.json() if response.text else {}
            }
            logger.info(f"✓ Webhook response: {response.status_code}")
            return result
    except asyncio.TimeoutError:
        logger.error(f"✗ Webhook timeout after {timeout}s")
        return {"status": "timeout", "error": f"Webhook request exceeded {timeout}s"}
    except Exception as e:
        logger.error(f"✗ Webhook error: {str(e)}\n{traceback.format_exc()}")
        return {"status": "error", "error": str(e)}

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def index():
    """Main ATS dashboard"""
    return render_template('advanced_index.html')

@app.route('/api/status')
def status():
    """Health check endpoint"""
    return jsonify({
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "model": OPENAI_MODEL,
        "webhook_configured": bool(N8N_WEBHOOK)
    })

# ============================================================================
# FILE UPLOAD ENDPOINT
# ============================================================================

@app.route('/api/upload-file', methods=['POST'])
def upload_file():
    """
    Universal file upload endpoint
    Supports: PDF, DOC, DOCX, TXT, CSV
    """
    try:
        if 'file' not in request.files:
            logger.warning("File upload attempted without file")
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if not file.filename:
            logger.warning("File upload attempted with empty filename")
            return jsonify({"error": "Invalid filename"}), 400
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        logger.info(f"✓ File uploaded: {filename}")
        
        # Extract text based on file type
        ext = filename.lower().split('.')[-1]
        text_content = ""
        
        if ext == 'pdf':
            text_content = extract_pdf_text(file_path)
        elif ext in ['docx', 'doc']:
            text_content = extract_docx_text(file_path)
        elif ext == 'txt':
            text_content = extract_text_file(file_path)
        elif ext == 'csv':
            csv_data = read_csv_data(file_path)
            return jsonify({
                "filename": filename,
                "type": "csv",
                "rows": len(csv_data),
                "data": csv_data,
                "preview": csv_data[:5] if csv_data else []
            })
        
        # Clean up temp file
        try:
            os.remove(file_path)
            logger.info(f"✓ Temp file cleaned: {filename}")
        except:
            pass
        
        return jsonify({
            "filename": filename,
            "type": ext,
            "length": len(text_content),
            "content": text_content[:500] + "..." if len(text_content) > 500 else text_content,
            "full_content": text_content
        })
        
    except Exception as e:
        logger.error(f"✗ File upload error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

# ============================================================================
# CANDIDATE SCREENING
# ============================================================================

@app.route('/api/screen-candidate', methods=['POST'])
def screen_candidate():
    """
    Screen single candidate against JD
    Calls n8n Resume Screening workflow
    """
    try:
        data = request.get_json()
        candidate_name = data.get('candidate_name', 'Candidate')
        resume_text = data.get('resume_text', '')
        job_title = data.get('job_title', '')
        jd_text = data.get('jd_text', '')
        
        if not resume_text or not jd_text:
            logger.warning("Screening attempted with missing resume or JD")
            return jsonify({"error": "Resume and JD are required"}), 400
        
        logger.info(f"→ Screening candidate: {candidate_name}")
        
        payload = {
            "task_type": "Screen CV against JD",
            "candidate_name": candidate_name,
            "resume_text": resume_text,
            "job_title": job_title,
            "jd_text": jd_text
        }
        
        # Call webhook
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(call_n8n_webhook(payload))
        
        logger.info(f"✓ Screening completed: {result['status']}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"✗ Screening error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ============================================================================
# BULK SCREENING
# ============================================================================

@app.route('/api/bulk-screen', methods=['POST'])
def bulk_screen():
    """
    Bulk screen multiple candidates from CSV
    """
    try:
        data = request.get_json()
        candidates = data.get('candidates', [])
        job_title = data.get('job_title', '')
        jd_text = data.get('jd_text', '')
        
        if not candidates or not jd_text:
            logger.warning("Bulk screening attempted with missing data")
            return jsonify({"error": "Candidates and JD are required"}), 400
        
        logger.info(f"→ Bulk screening started: {len(candidates)} candidates")
        
        stats = {
            "total": len(candidates),
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "results": []
        }
        
        for idx, candidate in enumerate(candidates):
            try:
                name = candidate.get('name') or candidate.get('Name') or f"Candidate {idx+1}"
                resume = candidate.get('resume') or candidate.get('Resume') or ""
                
                if not resume:
                    logger.warning(f"Skipping {name} - no resume")
                    stats["skipped"] += 1
                    continue
                
                payload = {
                    "task_type": "Screen CV against JD",
                    "candidate_name": name,
                    "resume_text": resume,
                    "job_title": job_title,
                    "jd_text": jd_text
                }
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(call_n8n_webhook(payload))
                
                stats["results"].append({
                    "candidate": name,
                    "status": result['status'],
                    "data": result.get('data', {})
                })
                stats["processed"] += 1
                logger.info(f"✓ Screened: {name}")
                
            except Exception as e:
                logger.error(f"✗ Error screening {name}: {str(e)}")
                stats["errors"] += 1
        
        logger.info(f"✓ Bulk screening completed: {stats['processed']} processed, {stats['errors']} errors")
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"✗ Bulk screening error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ============================================================================
# JOB POST GENERATION
# ============================================================================

@app.route('/api/generate-job-post', methods=['POST'])
def generate_job_post():
    """
    Generate job post for multiple platforms
    Calls n8n Job Post Agent workflow
    """
    try:
        data = request.get_json()
        job_title = data.get('job_title', '')
        jd_text = data.get('jd_text', '')
        
        if not jd_text:
            logger.warning("Job post generation attempted with missing JD")
            return jsonify({"error": "Job description is required"}), 400
        
        logger.info(f"→ Generating job post: {job_title}")
        
        payload = {
            "task_type": "Create Job Post",
            "job_title": job_title,
            "jd_text": jd_text
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(call_n8n_webhook(payload))
        
        logger.info(f"✓ Job post generated: {result['status']}")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"✗ Job post generation error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ============================================================================
# AI WRITING AGENT
# ============================================================================

@app.route('/api/ai-write', methods=['POST'])
def ai_write():
    """
    AI Writing Agent - Rewrite, paraphrase, reply to text
    Uses direct OpenAI API for better context-aware responses
    """
    try:
        data = request.get_json()
        text = data.get('text', '')
        action = data.get('action', 'rewrite')  # rewrite, paraphrase, reply
        tone = data.get('tone', 'professional')
        platform = data.get('platform', 'email')
        context = data.get('context', '')
        
        if not text:
            logger.warning("AI writing attempted with empty text")
            return jsonify({"status": "error", "error": "Text is required"}), 400
        
        logger.info(f"→ AI writing: {action} ({tone}, {platform})")
        
        # Get enhanced prompt
        prompt = get_writing_prompt(action, tone, platform)
        prompt = enhance_prompt_with_context(prompt, context)
        
        # Call OpenAI directly
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(call_openai_api(prompt, text, timeout=45))
        
        if result['status'] == 'success':
            logger.info(f"✓ AI writing completed successfully")
        else:
            logger.error(f"✗ AI writing error: {result.get('error', 'Unknown')}")
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"✗ AI writing error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ============================================================================
# MESSAGE GENERATION
# ============================================================================

@app.route('/api/generate-message', methods=['POST'])
def generate_message():
    """
    Generate candidate messages (interview, rejection, offer, follow-up)
    Uses context-aware prompting for better results
    """
    try:
        data = request.get_json()
        message_type = data.get('message_type', 'interview')
        recipient = data.get('recipient', '')
        job_title = data.get('job_title', '')
        tone = data.get('tone', 'professional')
        context = data.get('context', '')
        
        logger.info(f"→ Generating {message_type} message to {recipient} for {job_title}")
        logger.info(f"  Context: {context[:100] if context else 'None'}")
        
        # Get enhanced prompt with context awareness
        prompt = get_message_prompt(message_type, recipient, job_title, context)
        prompt = enhance_prompt_with_context(prompt, context)
        
        # Call OpenAI directly
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(call_openai_api(prompt, "", timeout=45))
        
        if result['status'] == 'success':
            logger.info(f"✓ Message generated successfully")
        else:
            logger.error(f"✗ Message generation error: {result.get('error', 'Unknown')}")
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"✗ Message generation error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ============================================================================
# ACTIVITY LOGS
# ============================================================================

@app.route('/api/logs')
def get_logs():
    """Get real-time activity logs"""
    try:
        log_file = 'logs/recruitment_ai.log'
        if not os.path.exists(log_file):
            return jsonify({"logs": [], "total": 0})
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Return last 100 lines
        recent_logs = lines[-100:] if len(lines) > 100 else lines
        
        return jsonify({
            "logs": recent_logs,
            "total": len(lines),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"✗ Log retrieval error: {str(e)}")
        return jsonify({"logs": [], "error": str(e)})

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(413)
def too_large(e):
    logger.warning("File too large uploaded")
    return jsonify({"error": "File too large (max 50MB)"}), 413

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == '__main__':
    logger.info("🚀 Starting Advanced Recruitment ATS v3.0")
    app.run(debug=True, host='0.0.0.0', port=5000)
