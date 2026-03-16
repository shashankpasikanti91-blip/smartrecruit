#!/usr/bin/env python3
"""
Advanced Recruitment ATS System - v3.0
IMPORTANT: This app has been replaced by advanced_app.py
To run the advanced version with AI chat, file uploads, and full n8n integration:

    python advanced_app.py

Legacy v2.0 kept for reference - v3.0 recommended for production use.
"""

from flask import Flask, render_template, request, jsonify
import os
import asyncio
import httpx
from datetime import datetime
from dotenv import load_dotenv
import logging
from werkzeug.utils import secure_filename
import PyPDF2
from docx import Document
import csv
import traceback
from io import StringIO

# Setup logging
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

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')
SUPABASE_URL = os.getenv('SUPABASE_URL')
N8N_WEBHOOK = os.getenv('N8N_WEBHOOK_PRODUCTION')

logger.info(f"✓ App initialized - Webhook: {bool(N8N_WEBHOOK)}")

# ============================================================================
# HOME PAGE
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'webhook_configured': bool(N8N_WEBHOOK),
        'model': OPENAI_MODEL
    })

@app.route('/api/upload-file', methods=['POST'])
def upload_file():
    """Handle PDF, DOC, DOCX, TXT, CSV uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        allowed_ext = {'pdf', 'doc', 'docx', 'txt', 'csv'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_ext:
            return jsonify({'error': f'Unsupported. Allowed: {", ".join(allowed_ext)}'}), 400
        
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        logger.info(f"📤 File uploaded: {filename}")
        
        try:
            if file_ext == 'pdf':
                content = extract_pdf_text(temp_path)
            elif file_ext in ['doc', 'docx']:
                content = extract_docx_text(temp_path)
            elif file_ext == 'csv':
                content = read_csv(temp_path)
            else:
                with open(temp_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            logger.info(f"✓ Extracted {len(content)} chars from {file_ext.upper()}")
            
            return jsonify({
                'success': True,
                'filename': file.filename,
                'content': content,
                'file_type': file_ext,
                'size': len(content),
                'message': f'✓ {file_ext.upper()} processed'
            })
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/bulk-screen', methods=['POST'])
def bulk_screen():
    """Bulk screen candidates from CSV with JD"""
    try:
        data = request.json
        csv_content = data.get('csv_content', '')
        job_desc = data.get('job_description', '')
        job_title = data.get('job_title', '')
        
        if not all([csv_content, job_desc, job_title]):
            logger.warning("❌ Missing CSV, JD or job title")
            return jsonify({'error': 'Missing CSV, Job Description, or Job Title'}), 400
        
        logger.info(f"📊 Bulk screening: {job_title}")
        
        # Parse CSV
        csv_file = StringIO(csv_content)
        reader = csv.DictReader(csv_file)
        candidates = list(reader)
        
        if not candidates:
            return jsonify({'error': 'CSV is empty'}), 400
        
        logger.info(f"📋 Processing {len(candidates)} candidates")
        
        results = []
        for idx, cand in enumerate(candidates, 1):
            try:
                name = cand.get('name') or cand.get('Name') or cand.get('candidate_name') or f'Candidate {idx}'
                resume = cand.get('resume') or cand.get('Resume') or cand.get('cv') or cand.get('CV') or ''
                
                if not resume:
                    logger.warning(f"⚠️ No resume for {name}")
                    results.append({'candidate': name, 'status': 'SKIPPED', 'reason': 'No resume'})
                    continue
                
                logger.info(f"  [{idx}/{len(candidates)}] {name}")
                
                result = asyncio.run(call_webhook({
                    'candidate_name': name,
                    'candidate_resume': resume,
                    'job_title': job_title,
                    'job_description': job_desc
                }))
                
                results.append({
                    'candidate': name,
                    'status': 'PROCESSED',
                    'result': result
                })
            
            except Exception as e:
                logger.error(f"❌ Error for {name}: {str(e)}")
                results.append({'candidate': name, 'status': 'ERROR', 'error': str(e)})
        
        logger.info(f"✓ Bulk completed")
        
        return jsonify({
            'success': True,
            'total': len(candidates),
            'processed': sum(1 for r in results if r['status'] == 'PROCESSED'),
            'skipped': sum(1 for r in results if r['status'] == 'SKIPPED'),
            'errors': sum(1 for r in results if r['status'] == 'ERROR'),
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"❌ Bulk error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/screen-candidate', methods=['POST'])
def screen_candidate():
    """Screen a candidate using AI"""
    try:
        data = request.json
        
        candidate_name = data.get('candidate_name', 'Unknown')
        candidate_resume = data.get('candidate_resume', '')
        job_title = data.get('job_title', '')
        job_description = data.get('job_description', '')
        
        if not all([candidate_resume, job_title, job_description]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Call n8n webhook
        result = asyncio.run(call_webhook({
            'candidate_name': candidate_name,
            'candidate_resume': candidate_resume,
            'job_title': job_title,
            'job_description': job_description
        }))
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Screening error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-message', methods=['POST'])
def generate_message():
    """Generate a message for candidate"""
    try:
        data = request.json
        
        message_type = data.get('message_type', 'interview_invitation')
        recipient_name = data.get('recipient_name', '')
        recipient_email = data.get('recipient_email', '')
        job_title = data.get('job_title', '')
        
        if not all([recipient_name, recipient_email, job_title]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Generate message
        result = asyncio.run(call_webhook({
            'message_type': message_type,
            'recipient_name': recipient_name,
            'recipient_email': recipient_email,
            'job_title': job_title
        }))
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Message generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    """Handle resume file upload (PDF, DOC, DOCX)"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file extension
        allowed_extensions = {'pdf', 'doc', 'docx', 'txt'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'File type not supported. Allowed: {", ".join(allowed_extensions)}'}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        try:
            # Extract text based on file type
            if file_ext == 'pdf':
                content = extract_pdf_text(temp_path)
            elif file_ext in ['doc', 'docx']:
                content = extract_docx_text(temp_path)
            else:  # txt
                content = file.read().decode('utf-8', errors='ignore')
            
            return jsonify({
                'success': True,
                'filename': file.filename,
                'content': content,
                'size': len(content),
                'file_type': file_ext,
                'message': f'Successfully extracted text from {file_ext.upper()}'
            })
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent logs"""
    try:
        log_file = 'logs/recruitment_ai.log'
        if not os.path.exists(log_file):
            return jsonify({'logs': [], 'total': 0})
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
            recent = lines[-100:] if len(lines) > 100 else lines
        
        return jsonify({'logs': recent, 'total': len(lines)})
    
    except Exception as e:
        logger.error(f"Log read error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_pdf_text(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        raise Exception(f"Failed to extract PDF: {str(e)}")

def extract_docx_text(file_path):
    """Extract text from DOCX/DOC file"""
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text.strip()
    except Exception as e:
        logger.error(f"DOCX extraction error: {str(e)}")
        raise Exception(f"Failed to extract DOCX: {str(e)}")

def read_csv(file_path):
    """Read CSV file content"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"CSV reading error: {str(e)}")
        raise Exception(f"Failed to read CSV: {str(e)}")

async def call_webhook(data):
    """Call n8n webhook with comprehensive error handling"""
    if not N8N_WEBHOOK:
        logger.error("❌ Webhook not configured")
        return {'error': 'Webhook not configured', 'success': False}
    
    try:
        logger.info(f"🔗 Calling webhook...")
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                N8N_WEBHOOK,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            logger.info(f"📨 Response: {response.status_code}")
            
            if response.status_code in [200, 202]:
                result = {
                    'success': True,
                    'status': 'completed' if response.status_code == 200 else 'queued',
                    'timestamp': datetime.now().isoformat()
                }
                try:
                    result['data'] = response.json()
                except:
                    result['data'] = response.text[:500]
                
                logger.info(f"✓ Webhook OK")
                return result
            else:
                error_msg = f'Webhook error: {response.status_code}'
                logger.error(f"❌ {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code,
                    'details': response.text[:300]
                }
    
    except asyncio.TimeoutError:
        error_msg = "Webhook timeout (60 seconds)"
        logger.error(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg, 'code': 'TIMEOUT'}
    
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Webhook error: {error_msg}\n{traceback.format_exc()}")
        return {'success': False, 'error': error_msg, 'code': 'ERROR'}

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

# ============================================================================
# RUN APP
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("RECRUITMENT AI SYSTEM - WEB UI")
    print("="*70)
    print(f"\n✓ Starting web server...")
    print(f"✓ Access at: http://localhost:5000")
    print(f"✓ Model: {OPENAI_MODEL}")
    print(f"✓ Webhook: {'✓ Configured' if N8N_WEBHOOK else '✗ Not configured'}")
    print("\n" + "="*70 + "\n")
    
    # Run on all interfaces
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        use_reloader=False
    )
