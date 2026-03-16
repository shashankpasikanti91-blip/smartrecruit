# SRP SmartRecruit v3.2 — End-to-End Test Checklist
*Use this to verify the full user journey before going live.*

Base URL: `https://yourdomain.com` (or `http://localhost:8000` locally)

---

## Setup
```bash
# Set base URL
BASE=http://localhost:8000

# Or production:
BASE=https://yourdomain.com
```

---

## 1. Health Check ✅

```bash
curl -s $BASE/health | python -m json.tool
```

**Expected:** `{"status": "healthy", "version": "3.2.0", "database": "connected"}`

---

## 2. User Registration ✅

```bash
curl -s -X POST $BASE/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com", "password": "TestPass123!"}' \
  | python -m json.tool
```

**Expected:** 201 Created
```json
{
  "message": "Registration successful. Please verify your email with OTP.",
  "user_id": <id>,
  "email": "testuser@example.com"
}
```
> In development: `otp_code` is also returned.
> In production: OTP is sent to email — check inbox.

**Check:**
- [ ] 201 status code returned
- [ ] `user_id` present
- [ ] Duplicate email returns 400 "Email already registered"
- [ ] Weak password (< 8 chars) returns 422

---

## 3. OTP Verification ✅

```bash
# Replace 123456 with the OTP from email or dev response
curl -s -X POST $BASE/api/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com", "otp_code": "123456"}' \
  | python -m json.tool
```

**Expected:** `{"message": "Email verified successfully. You can now login.", "success": true}`

**Check:**
- [ ] Correct OTP → verified
- [ ] Wrong OTP → 400 "Invalid OTP code"
- [ ] Expired OTP (>10 min old) → 400 "OTP has expired"
- [ ] Already-used OTP → 400 "Invalid OTP code"

---

## 4. Login ✅

```bash
TOKEN=$(curl -s -X POST $BASE/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com", "password": "TestPass123!"}' \
  | python -c "import sys,json; d=json.load(sys.stdin); print(d['access_token'])")
echo "Token: $TOKEN"
```

**Expected:** `{"access_token": "eyJ...", "token_type": "bearer", "user": {...}}`

**Check:**
- [ ] Token returned
- [ ] Wrong password → 401 "Incorrect email or password"
- [ ] Unverified account → 403 "Please verify your email"
- [ ] Second login invalidates first session (single-session enforcement)

---

## 5. Auth — Get Current User ✅

```bash
curl -s $BASE/api/auth/me \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool
```

**Expected:** User object with `id`, `email`, `role`, `is_verified: true`

**Check:**
- [ ] Returns user data with valid token
- [ ] Invalid token → 401
- [ ] Expired token → 401
- [ ] No token → 401 (or 403)

---

## 6. Resume Upload ✅

```bash
curl -s -X POST $BASE/api/resume/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@sample_resume.txt;type=text/plain" \
  | python -m json.tool
```

**Expected:** 201 Created
```json
{"id": <resume_id>, "filename": "sample_resume.txt", "file_size": <n>, ...}
```

Save `resume_id` for next step.

**Check:**
- [ ] PDF upload works
- [ ] DOCX upload works
- [ ] TXT upload works
- [ ] File > 10MB → 400 rejection
- [ ] Unauthenticated → 401/403
- [ ] Unsupported extension (e.g. .exe) → 400

---

## 7. Resume Screening ✅

```bash
# Replace RESUME_ID with id from step 6
curl -s -X POST $BASE/api/screening/screen \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resume_id": RESUME_ID, "job_description": "Senior Python developer with FastAPI, PostgreSQL, Docker experience, 3+ years"}' \
  | python -m json.tool
```

**Expected:** 200 OK
```json
{
  "id": <screening_id>,
  "score": <0-100>,
  "recommendation": "interview|review|reject",
  "strengths": [...],
  "concerns": [...],
  "is_eligible_for_invite": true|false
}
```

**Check:**
- [ ] Score between 0 and 100
- [ ] Recommendation present
- [ ] High score (≥75) sets `is_eligible_for_invite: true`
- [ ] Invalid `resume_id` → 404
- [ ] Resume from another user → 404 (ownership check)
- [ ] Rate limit: free user 3 screenings/day, 4th → 429

---

## 8. Get Screening Results ✅

```bash
curl -s $BASE/api/screening/results \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool
```

**Expected:** List of screening results for current user.

```bash
# Get single result
curl -s $BASE/api/screening/results/SCREENING_ID \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool
```

---

## 9. Interview Invite ✅

```bash
curl -s -X POST $BASE/api/screening/invite \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "screening_id": SCREENING_ID,
    "candidate_name": "John Doe",
    "candidate_email": "john.doe@example.com",
    "interview_date": "2026-04-01T10:00:00"
  }' \
  | python -m json.tool
```

**Expected:** 201 Created with invite details.

**Check:**
- [ ] Invite created for eligible candidate
- [ ] Invite for ineligible candidate (score < 75) → check behavior (warn or block)

---

## 10. AI Endpoint ✅

```bash
# Writing Assistant
curl -s -X POST $BASE/api/ai/writing-assist \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "We looking for developer with python skills", "context": "job posting"}' \
  | python -m json.tool
```

**Expected:**
```json
{
  "improved_text": "...",
  "suggestions": ["...", "..."],
  "tone": "professional"
}
```

```bash
# Generate job description
curl -s -X POST "$BASE/api/ai/generate-job-description?job_title=Backend+Developer&requirements=Python+FastAPI+3yrs" \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool
```

**Check:**
- [ ] Returns structured improvement
- [ ] `suggestions` is a list
- [ ] Unauthenticated → 401/403

---

## 11. Support Ticket ✅

```bash
# Authenticated ticket
curl -s -X POST $BASE/api/support/ticket \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "I cannot upload my resume", "category": "technical"}' \
  | python -m json.tool
```

**Expected:**
```json
{"id": <n>, "message": "Support ticket created successfully", "ticket_number": "TICKET-000001", "status": "open"}
```

```bash
# Anonymous ticket
curl -s -X POST $BASE/api/support/ticket \
  -H "Content-Type: application/json" \
  -d '{"message": "Anonymous support request", "category": "general", "user_email": "anon@example.com"}' \
  | python -m json.tool
```

**Check:**
- [ ] Authenticated ticket → links to user
- [ ] Anonymous ticket → accepted (no auth required)
- [ ] `GET /api/support/tickets` returns user's tickets
- [ ] `GET /api/support/admin/tickets` → requires admin role

---

## 12. Logout ✅

```bash
curl -s -X POST $BASE/api/auth/logout \
  -H "Authorization: Bearer $TOKEN" \
  | python -m json.tool
```

**Expected:** `{"message": "Logged out successfully"}`

**Check:**
- [ ] Token is invalidated after logout
- [ ] Using old token after logout → 401 "Session expired"

---

## 13. Password Reset ✅

```bash
# Step 1: Request reset
curl -s -X POST $BASE/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com"}' \
  | python -m json.tool

# Step 2: Reset with OTP
curl -s -X POST $BASE/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"email": "testuser@example.com", "otp_code": "OTP_FROM_EMAIL", "new_password": "NewPass456!"}' \
  | python -m json.tool
```

**Check:**
- [ ] Reset OTP sent (dev: returned in response)
- [ ] Password updated with correct OTP
- [ ] Old password no longer works
- [ ] All sessions invalidated after reset

---

## 14. Edge Cases & Security ✅

| Test | Expected |
|------|----------|
| SQL injection in email field `'OR 1=1--` | 422 Validation error (Pydantic blocks it) |
| XSS in support message `<script>alert(1)</script>` | Stored as text, not executed |
| JWT from another user | 401 / 404 (data isolation) |
| Access other user's resume | 404 (ownership enforced) |
| Admin endpoint as regular user | 403 Forbidden |
| `/api/auth/register` with very long password (1000 chars) | 422 (max_length=100 enforced) |

---

## Quick Smoke Test Script

Run this to verify all endpoints in one pass:

```bash
python comprehensive_test_suite.py
```

Or for a quick check:

```bash
python final_verification.py
```
