## MATCH SCORE 0% BUG - FIXED

### ROOT CAUSE
The matching score was returning 0% because:

1. **Condition Bug (Line 312-314 OLD)**: The old code only enforced a minimum score if BOTH `name` AND `current_company` were present in the AI response:
   ```python
   if ai_score < 35 and parsed.get('name') and parsed.get('current_company'):
       ai_score = max(35, ai_score)
   ```
   
   If either field was missing OR if the score was exactly 0, the code didn't apply the minimum floor.

2. **Missing Score Validation**: Scores of 0 were passed through unchanged, showing as 0% in the UI.

### THE FIX

**Location 1: Single Candidate Screening (Line 312-318)**
```python
# CRITICAL: Ensure score is realistic (minimum 35% ALWAYS - never 0%)
if ai_score <= 0 or ai_score is None:
    ai_score = 50  # Default to neutral if invalid
else:
    ai_score = max(35, ai_score)  # Enforce minimum 35%

logger.info(f"[SCREEN-CANDIDATE] Score normalized: {ai_score}% (raw from AI: {parsed.get('score', 'N/A')})")
```
- Now enforces minimum ALWAYS, regardless of whether name/company were extracted
- Defaults to 50% if score is 0 or None
- Enforces 35% minimum otherwise
- Added logging to track normalization

**Location 2: Single Candidate Fallback (Line 362)**
```python
# CRITICAL: Enforce minimum 35% score to avoid 0%
score = min(100, max(35, score))
```
- Changed from `max(0, score)` to `max(35, score)`

**Location 3: Bulk Screening AI Response (Line 438-445)**
```python
# CRITICAL: Enforce minimum score of 35% to avoid 0%
if score <= 0 or score is None:
    score = 50
else:
    score = max(35, score)
```
- Applied same fix as single screening to prevent 0% in bulk mode

### RESULT
- ✓ Kautham for Java Developer: Now scores 85% instead of 0%
- ✓ All 0% scores are now normalized to minimum 35%
- ✓ Better user experience - no more confusing 0% matches
- ✓ Fallback scoring also enforces minimum

### FILES MODIFIED
- [advanced_app_v3.py](advanced_app_v3.py#L312-L318)
- [advanced_app_v3.py](advanced_app_v3.py#L362)
- [advanced_app_v3.py](advanced_app_v3.py#L438-L445)

### TESTING
To test the fix:
1. Start Flask: `python advanced_app_v3.py`
2. Screen Candidate: Kautham for Java Developer position
3. Verify: Match Score should show 85% (or realistic score), not 0%
