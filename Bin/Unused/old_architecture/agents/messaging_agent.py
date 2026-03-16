"""
Messaging Agent for AI-Generated Communications
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from openai import OpenAI
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class MessagingAgent:
    """AI agent for generating recruitment messages"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-mini"):
        """Initialize messaging agent"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        logger.info(f"Messaging agent initialized with model: {model}")
    
    def _build_message_prompt(
        self,
        message_type: str,
        tone: str,
        platform: str,
        recipient_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Build message generation prompt"""
        
        tone_guidelines = {
            "formal": "Use formal language, professional titles, and structured paragraphs.",
            "professional": "Use professional language while maintaining warmth and approachability.",
            "semi_formal": "Balance professionalism with casual elements. Use conversational language.",
            "friendly": "Use warm, conversational tone. Include personal touches but remain professional.",
            "casual": "Use relaxed, friendly language. Can use contractions and colloquialisms."
        }
        
        platform_guidelines = {
            "email": "Format as a complete email with subject line and body. Use proper email structure.",
            "whatsapp": "Format for WhatsApp. Can use emojis, bullet points, line breaks for readability.",
            "linkedin": "Format for LinkedIn. Professional but can be more engaging. Include relevant hashtags.",
            "telegram": "Format for Telegram. Can use formatting, emojis, and concise messages.",
            "sms": "Keep under 160 characters or clearly indicate as multi-part message."
        }
        
        job_title = context.get("job_title", "the position")
        company_name = context.get("company_name", "our company")
        location = context.get("location", "")
        
        base_prompt = f"""You are an expert recruitment communication specialist. Generate a compelling {message_type} message for {platform}.

=== GUIDELINES ===
Tone: {tone_guidelines.get(tone, "professional")}
Platform: {platform_guidelines.get(platform, "general")}
Recipient: {recipient_name}

=== CONTEXT ===
Job Title: {job_title}
Company: {company_name}
Location: {location}
"""
        
        if message_type == "job_posting":
            base_prompt += f"""
Additional context:
- Responsibilities: {json.dumps(context.get('responsibilities', [])[:3])}
- Key Skills: {json.dumps(context.get('key_skills', [])[:5])}
- Experience Required: {context.get('experience_required', 'Not specified')} years
- Salary Range: {context.get('salary_range', 'Competitive')}
"""
        
        elif message_type == "interview_invite":
            base_prompt += f"""
Additional context:
- Interview Stage: {context.get('interview_stage', 'Phone screening')}
- Scheduled Date/Time: {context.get('interview_datetime', 'TBD')}
- Interview Link: {context.get('interview_link', 'To be provided')}
"""
        
        elif message_type == "offer":
            base_prompt += f"""
Additional context:
- Salary: {context.get('salary', 'To be discussed')}
- Start Date: {context.get('start_date', 'To be confirmed')}
- Benefits: {json.dumps(context.get('benefits', [])[:3])}
"""
        
        base_prompt += f"""

=== REQUIREMENTS ===
1. Make the message compelling and personalized
2. Highlight key benefits for the candidate
3. Include clear call-to-action
4. Keep it concise but informative
5. Match the specified tone and platform format

Generate the message below. For email, include "Subject:" line. No JSON formatting needed, just the message content.
"""
        
        return base_prompt
    
    def generate_message(
        self,
        message_type: str,
        tone: str,
        platform: str,
        recipient_name: str,
        context: Optional[Dict[str, Any]] = None,
        custom_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a message"""
        try:
            context = context or {}
            
            # Build prompt
            prompt = self._build_message_prompt(
                message_type=message_type,
                tone=tone,
                platform=platform,
                recipient_name=recipient_name,
                context=context
            )
            
            if custom_content:
                prompt += f"\n\nAdditional content to include:\n{custom_content}"
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Higher for creativity
                timeout=30
            )
            
            body = response.choices[0].message.content.strip()
            
            # Parse email subject if present
            subject = None
            if platform == "email" and body.startswith("Subject:"):
                lines = body.split("\n", 2)
                subject = lines[0].replace("Subject:", "").strip()
                body = lines[2] if len(lines) > 2 else "\n".join(lines[1:])
            
            result = {
                "id": str(uuid.uuid4()),
                "message_type": message_type,
                "platform": platform,
                "tone": tone,
                "subject": subject,
                "body": body,
                "generated_at": datetime.utcnow().isoformat(),
                "ai_model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            }
            
            logger.info(f"Generated {message_type} message for {platform}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating message: {str(e)}")
            raise
    
    def generate_job_posting(
        self,
        job_title: str,
        company_name: str,
        tone: str = "professional",
        platforms: Optional[list] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate job posting for multiple platforms"""
        
        platforms = platforms or ["linkedin", "email", "whatsapp"]
        context = context or {}
        context.update({
            "job_title": job_title,
            "company_name": company_name
        })
        
        messages = {}
        for platform in platforms:
            try:
                msg = self.generate_message(
                    message_type="job_posting",
                    tone=tone,
                    platform=platform,
                    recipient_name="Candidate",
                    context=context
                )
                messages[platform] = msg
            except Exception as e:
                logger.error(f"Error generating posting for {platform}: {str(e)}")
                messages[platform] = {"error": str(e)}
        
        return {
            "job_title": job_title,
            "company_name": company_name,
            "messages": messages,
            "generated_at": datetime.utcnow().isoformat()
        }
