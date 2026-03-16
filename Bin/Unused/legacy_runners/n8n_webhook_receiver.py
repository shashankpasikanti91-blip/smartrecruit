#!/usr/bin/env python
"""Webhook receiver for n8n integration"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from dotenv import load_dotenv
import json
from datetime import datetime

load_dotenv()

app = FastAPI(title="Recruitment AI - n8n Bridge")

# Enable CORS for n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/webhook/screen-candidate")
async def webhook_screen_candidate(data: dict):
    """
    Webhook endpoint for candidate screening
    
    Expected data:
    {
        "candidate_name": "John Doe",
        "candidate_resume": "resume text...",
        "job_title": "Senior Developer",
        "job_description": "jd text..."
    }
    """
    try:
        candidate_name = data.get("candidate_name", "Unknown")
        resume = data.get("candidate_resume", "")
        job_title = data.get("job_title", "")
        jd = data.get("job_description", "")
        
        if not resume or not jd:
            raise HTTPException(status_code=400, detail="Missing resume or JD")
        
        # Call OpenAI API directly
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="Missing OpenAI API key")
        
        prompt = f"""You are an expert recruiter. Analyze this candidate-job match:

CANDIDATE RESUME:
{resume}

JOB DESCRIPTION:
{jd}

Provide:
1. Match score (0-100)
2. Key strengths (2-3 bullets)
3. Skill gaps (2-3 bullets)
4. Recommendation (STRONG MATCH / GOOD MATCH / POSSIBLE / POOR MATCH)

Format response clearly."""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.7
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        result = response.json()
        analysis = result["choices"][0]["message"]["content"]
        
        return {
            "success": True,
            "candidate_name": candidate_name,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/generate-message")
async def webhook_generate_message(data: dict):
    """
    Webhook endpoint for message generation
    
    Expected data:
    {
        "message_type": "interview_invite",
        "recipient_name": "John",
        "recipient_email": "john@example.com",
        "job_title": "Senior Developer",
        "context": {}
    }
    """
    try:
        msg_type = data.get("message_type", "interview_invite")
        recipient_name = data.get("recipient_name", "")
        job_title = data.get("job_title", "")
        recipient_email = data.get("recipient_email", "")
        
        if not recipient_name or not job_title:
            raise HTTPException(status_code=400, detail="Missing recipient_name or job_title")
        
        templates = {
            "interview_invite": f"""Dear {recipient_name},

We are pleased to invite you for an interview for the {job_title} position at our company.

Please let us know your availability for a 30-minute video interview over the next week.

We look forward to speaking with you!

Best regards,
Recruitment Team""",
            
            "rejection": f"""Dear {recipient_name},

Thank you for your interest in the {job_title} position. After careful review of your application, we have decided to move forward with other candidates at this time.

We appreciate your time and effort. We encourage you to apply for future positions that match your profile.

Best regards,
Recruitment Team""",
            
            "offer": f"""Dear {recipient_name},

Congratulations! We are pleased to offer you the {job_title} position at our company.

Please find the offer letter attached. We look forward to welcoming you to our team.

Please confirm your acceptance within 48 hours.

Best regards,
HR Team""",
            
            "follow_up": f"""Dear {recipient_name},

Following up on your application for the {job_title} position. We are still reviewing applications and will contact you shortly.

Thank you for your patience.

Best regards,
Recruitment Team"""
        }
        
        message = templates.get(msg_type, templates["interview_invite"])
        
        subject_map = {
            "interview_invite": f"Interview Invitation - {job_title}",
            "rejection": f"Application Update - {job_title}",
            "offer": f"Job Offer - {job_title}",
            "follow_up": f"Follow-up - {job_title} Position"
        }
        
        return {
            "success": True,
            "message_type": msg_type,
            "recipient": recipient_name,
            "email": recipient_email,
            "message": message,
            "subject": subject_map.get(msg_type, "Message from Recruitment Team"),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/webhook/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Recruitment AI - n8n Bridge",
        "openai_connected": bool(os.getenv("OPENAI_API_KEY")),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Recruitment AI - n8n Bridge",
        "version": "1.0.0",
        "endpoints": [
            "POST /webhook/screen-candidate",
            "POST /webhook/generate-message",
            "GET /webhook/health"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*80)
    print("RECRUITMENT AI - n8n WEBHOOK BRIDGE")
    print("="*80)
    print("\nStarting webhook server on http://localhost:8000")
    print("\nEndpoints:")
    print("  - Health: GET http://localhost:8000/webhook/health")
    print("  - Screen: POST http://localhost:8000/webhook/screen-candidate")
    print("  - Message: POST http://localhost:8000/webhook/generate-message")
    print("\n" + "="*80 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
