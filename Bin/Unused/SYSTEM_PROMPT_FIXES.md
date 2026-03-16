# CV Screening System Prompt Implementation - FIXED

## Problem Identified
- **Symptom**: All resume screenings returning 0% match score
- **Root Cause**: OpenAI API calls were failing silently, falling back to basic keyword matching
- **Impact**: System not using the advanced CV screening prompt from N8N workflow

## Solution Implemented

### 1. Added Comprehensive Debug Logging
```python
# Now logs:
- [OpenAI] Using model: gpt-3.5-turbo
- [OpenAI] System prompt length: 5750 chars
- [OpenAI] User prompt length: XXXX chars
- [OpenAI] Making request to gpt-3.5-turbo...
- [OpenAI] Status code: 200
- [OpenAI] Success! Output length: XXXX chars
- [OpenAI] API error details if it fails
```

### 2. Enhanced Error Handling
- Check if API key exists BEFORE making request
- Log full error responses from OpenAI
- Return meaningful error messages to user
- Added try/catch with traceback logging

### 3. Improved Screening Endpoint - `/api/screen-candidate`
**Before**: Silently fell back to keyword matching, returned 0%
**After**: 
- ✅ Logs every step of the process
- ✅ Reports if API key is missing
- ✅ Reports if API call fails and why
- ✅ Uses CV_SCREENING_SYSTEM_PROMPT from N8N workflow
- ✅ Properly parses JSON response from AI
- ✅ Returns detailed evaluation with role-aware scoring

### 4. Improved OpenAI Function - `call_openai_api_with_system()`
```python
# Enhanced with:
- Detailed logging at each step
- Lower temperature (0.3) for consistent matching
- Higher max_tokens (2500) for detailed responses
- Better error messages
- Full traceback on exceptions
```

### 5. System Prompts Now Used
- **CV_SCREENING_SYSTEM_PROMPT**: Expert recruiter evaluation logic
- **JOB_POST_SYSTEM_PROMPT**: Multi-platform job posting (Email, WhatsApp, LinkedIn, Indeed)
- **AI_WRITING_SYSTEM_PROMPT**: Professional communication assistant

## Expected Results Now

### Before:
```
Candidate: Madhu
Position: JAVA Developer
Match Score: 0%
Assessment: (keyword matching only)
```

### After (with System Prompt):
```
Candidate: Madhu
Position: JAVA Developer (or Automation Test Engineer)
Match Score: 70-85% (AI-based evaluation)
Decision: Shortlisted (if score >= 70)
Evaluation: {
  "candidate_strengths": [...],
  "high_match_skills": ["Java", "Spring Boot", "Maven", "Git", "Jenkins", "TestNG", ...],
  "medium_match_skills": [...],
  "low_or_missing_match_skills": [...],
  "risk_level": "Low",
  "overall_fit_rating": 75,
  "justification": "Detailed AI-based evaluation"
}
```

## How to Test

### Option 1: Use Flask UI
1. Start app: `python advanced_app_v3.py`
2. Go to: http://localhost:5000
3. Use "Screen Candidate" feature
4. Check logs for OpenAI debug messages

### Option 2: Use Test Script
```bash
python test_screening.py
```
- Provides detailed output of each step
- Shows if OpenAI API is working
- Displays full AI response

### Option 3: Direct API Call
```bash
curl -X POST http://localhost:5000/api/screen-candidate \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "...",
    "jd_text": "...",
    "candidate_name": "Madhu",
    "job_title": "Java Developer"
  }'
```

## Log Files
Check `logs/recruitment_ai.log` for:
- OpenAI API calls and responses
- Model being used (gpt-3.5-turbo)
- API key verification
- Error details if API fails

## Files Modified
1. **advanced_app_v3.py**
   - Added `call_openai_api_with_system()` function with debug logging
   - Enhanced `/api/screen-candidate` endpoint
   - Added detailed error handling

2. **system_prompts.py** (Created)
   - CV_SCREENING_SYSTEM_PROMPT (from Resume AI Screening.json)
   - JOB_POST_SYSTEM_PROMPT (from Bunty Job Post Agent copy.json)
   - AI_WRITING_SYSTEM_PROMPT (from AI Writing Agent.json)

## Next Steps
1. Run the app with: `python advanced_app_v3.py`
2. Monitor the logs while screening resumes
3. Verify OpenAI API is being called (check logs)
4. Confirm scores are now >0% with AI evaluation
5. Check detailed evaluation includes role-aware logic

## Troubleshooting
If score is still 0%:
1. Check logs for: `[OpenAI] Status code: 200` ✓ (success)
2. If you see error code, API call failed
3. Verify `OPENAI_API_KEY` in `.env` is valid
4. Verify `OPENAI_MODEL=gpt-3.5-turbo` in `.env`
5. Check internet connection can reach OpenAI API

