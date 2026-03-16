"""
AI Helper Functions - Direct OpenAI Integration
Provides prompts and utilities for rewriting, messages, and AI features
"""

import os
import json
import httpx
import asyncio
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Get configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

# ============================================================================
# PROMPTS
# ============================================================================

WRITING_PROMPTS = {
    "rewrite": {
        "professional": "Rewrite the following text in a professional tone, maintaining the original message but improving clarity, grammar, and impact. Make it suitable for business communication.",
        "formal": "Rewrite the following text in a formal and official tone. Use sophisticated language and proper business etiquette.",
        "friendly": "Rewrite the following text in a warm, friendly and approachable tone. Make it personal and engaging while maintaining professionalism.",
        "casual": "Rewrite the following text in a casual, conversational tone. Keep it light and natural as if talking to a friend."
    },
    "paraphrase": {
        "professional": "Paraphrase the following text while maintaining a professional tone. Provide 3 different versions with varying emphasis.",
        "formal": "Paraphrase the following text in a formal manner. Provide 2-3 variations that sound official and structured.",
        "friendly": "Paraphrase the following text in a warm, friendly manner. Create 3 alternatives that feel personal and approachable.",
        "casual": "Paraphrase the following text in a casual way. Provide 2-3 variations that sound natural and conversational."
    },
    "reply": {
        "professional": "Generate a professional reply to the following text. Be courteous, clear, and solution-focused.",
        "formal": "Generate a formal, official reply to the following text. Use proper business etiquette and structure.",
        "friendly": "Generate a warm and friendly reply to the following text. Show genuine interest and approachability.",
        "casual": "Generate a casual, friendly reply to the following text. Keep it light and natural."
    }
}

MESSAGE_PROMPTS = {
    "interview": {
        "subject": "Interview Invitation",
        "template": "You are a recruitment specialist. Generate a compelling interview invitation message to {recipient} for the {job_title} position. "
                   "Make it professional, warm, and encouraging. Include: greeting, position details, why they're a great fit, "
                   "interview logistics suggestion, and call to action. Context: {context}"
    },
    "rejection": {
        "subject": "Application Update",
        "template": "You are a compassionate HR professional. Generate a respectful rejection message for {recipient} who applied for {job_title}. "
                   "Be empathetic, provide positive feedback, suggest future opportunities, and maintain a positive company image. Context: {context}"
    },
    "offer": {
        "subject": "Job Offer",
        "template": "You are an HR specialist. Generate an exciting job offer message for {recipient} for the {job_title} position. "
                   "Include congratulations, key details (title, team, reporting structure), next steps, and enthusiasm. Context: {context}"
    },
    "follow_up": {
        "subject": "Follow-up on Your Application",
        "template": "You are a recruiting coordinator. Generate a professional follow-up message for {recipient} regarding their application for {job_title}. "
                   "Express continued interest, ask about their availability, and provide a timeline. Context: {context}"
    }
}

# ============================================================================
# AI WRITING FUNCTIONS
# ============================================================================

async def call_openai_api(prompt: str, user_text: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Call OpenAI API directly with enhanced prompt
    Returns: {status: 'success'|'error', output: '...', note: '...', error: '...'}
    """
    if not OPENAI_API_KEY:
        return {"status": "error", "error": "OpenAI API key not configured"}
    
    try:
        full_prompt = f"{prompt}\n\nText to process:\n{user_text}"
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are an expert writing assistant. Provide clear, actionable output."},
                        {"role": "user", "content": full_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1000
                },
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                output = data.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
                return {
                    "status": "success",
                    "output": output,
                    "note": f"Generated using {OPENAI_MODEL}"
                }
            else:
                error_msg = response.text[:200]
                logger.error(f"OpenAI API error: {response.status_code} - {error_msg}")
                return {"status": "error", "error": f"API error: {response.status_code}"}
                
    except asyncio.TimeoutError:
        return {"status": "error", "error": f"Request timeout after {timeout}s"}
    except Exception as e:
        logger.error(f"OpenAI call error: {str(e)}")
        return {"status": "error", "error": str(e)[:200]}


def get_writing_prompt(action: str, tone: str, platform: str) -> str:
    """Get the appropriate prompt for writing actions"""
    
    base_prompt = WRITING_PROMPTS.get(action, {}).get(tone, 
        f"Rewrite the text in a {tone} tone")
    
    # Add platform-specific context
    platform_hints = {
        "email": "Format for email communication.",
        "whatsapp": "Keep it concise for messaging. Use friendly, casual language.",
        "linkedin": "Make it professional and impactful for LinkedIn.",
        "message": "Make it suitable for a quick message or chat."
    }
    
    platform_hint = platform_hints.get(platform, "")
    
    return f"{base_prompt}\n{platform_hint}" if platform_hint else base_prompt


def get_message_prompt(message_type: str, recipient: str, job_title: str, context: str) -> str:
    """Get the appropriate prompt for message generation"""
    
    template = MESSAGE_PROMPTS.get(message_type, {}).get("template", 
        "Generate a professional message")
    
    prompt = template.format(
        recipient=recipient or "the candidate",
        job_title=job_title or "the position",
        context=context or "No additional context"
    )
    
    return prompt

# ============================================================================
# CONTEXT-AWARE MESSAGE GENERATION
# ============================================================================

def enhance_prompt_with_context(base_prompt: str, context: str) -> str:
    """
    Enhance a prompt with additional context for better results
    
    Examples:
    - "team lead to manager" -> suggest career advancement
    - "budget constraints" -> mention flexibility
    - "urgent hire" -> emphasize timeline
    """
    
    if not context:
        return base_prompt
    
    # Parse context for specific scenarios
    context_lower = context.lower()
    enhancements = []
    
    if any(word in context_lower for word in ["promotion", "lead to manager", "advance"]):
        enhancements.append("Emphasize this as a career advancement opportunity and highlight growth potential.")
    
    if any(word in context_lower for word in ["urgent", "asap", "immediate", "soon"]):
        enhancements.append("Mention urgency and express strong interest in accelerating the timeline.")
    
    if any(word in context_lower for word in ["compensation", "salary", "budget", "cost"]):
        enhancements.append("Be mindful of compensation discussions and show flexibility if mentioned.")
    
    if any(word in context_lower for word in ["remote", "flexible", "location"]):
        enhancements.append("Highlight flexibility regarding work location or arrangements.")
    
    if any(word in context_lower for word in ["team", "culture", "collaborative"]):
        enhancements.append("Emphasize team fit and company culture alignment.")
    
    if enhancements:
        return f"{base_prompt}\n\nAdditional Context:\n" + "\n".join(f"- {e}" for e in enhancements)
    
    return base_prompt

# ============================================================================
# BATCH GENERATION
# ============================================================================

async def generate_multiple_messages(message_type: str, recipient: str, job_title: str, 
                                    context: str, tone: str = "professional", 
                                    count: int = 3) -> Dict[str, Any]:
    """
    Generate multiple message variations
    """
    prompt = get_message_prompt(message_type, recipient, job_title, context)
    prompt = enhance_prompt_with_context(prompt, context)
    
    # Modify prompt to request multiple variations
    prompt += f"\n\nPlease provide {count} different variations with different angles/emphasis."
    
    return await call_openai_api(prompt, "", timeout=45)
