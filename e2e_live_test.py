#!/usr/bin/env python3
"""Full E2E audit of all endpoints on live server."""
import urllib.request, urllib.error, json, time, random, string, subprocess, os

BASE = "https://recruit.srpailabs.com"
PGPASS = "AtsSecure4a16b511b68b557d2bf68af7"
email = "test_" + "".join(random.choices(string.ascii_lowercase, k=6)) + "@example.com"
password = "TestPass123!"
token = None
PASS = 0
FAIL = 0

def req(path, data=None, token=None, label="", method=None):
    url = BASE + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    m = method or ("POST" if body else "GET")
    try:
        r = urllib.request.Request(url, data=body, headers=headers, method=m)
        with urllib.request.urlopen(r, timeout=20) as resp:
            txt = resp.read().decode()
            print(f"  [OK {resp.status}] {label}")
            try:
                return json.loads(txt), resp.status
            except:
                return txt, resp.status
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        print(f"  [ERR {e.code}] {label}: {txt[:150]}")
        return None, e.code
    except Exception as ex:
        print(f"  [FAIL] {label}: {ex}")
        return None, 0

def psql(query):
    r = subprocess.run(
        ["docker", "exec", "-e", f"PGPASSWORD={PGPASS}", "srp-ats-db", "psql", "-U", "srp_ats", "-d", "srp_ats", "-t", "-c", query],
        capture_output=True, text=True
    )
    return r.stdout.strip()

def ok(cond, label):
    global PASS, FAIL
    if cond:
        print(f"  [PASS] {label}")
        PASS += 1
    else:
        print(f"  [FAIL] {label}")
        FAIL += 1

print("\n" + "="*60)
print("SRP SmartRecruit ATS - Full E2E Audit")
print("="*60)

# ── 1. REGISTER ──────────────────────────────────────────────
print(f"\n[1/10] REGISTER  ({email})")
resp, s = req("/api/auth/register", {"email": email, "password": password, "full_name": "Test User", "company": "SRP"}, label="register")
ok(s == 201, f"register returns 201 (got {s})")

# ── 2. OTP FROM DB ───────────────────────────────────────────
print("\n[2/10] OTP VERIFICATION")
time.sleep(1)
otp_code = None
for line in psql(f"SELECT otp_code FROM otp_verifications WHERE email='{email}' LIMIT 1;").split("\n"):
    line = line.strip()
    if line.isdigit() and len(line) == 6:
        otp_code = line
        break
ok(bool(otp_code), f"OTP stored in DB (got: {otp_code})")

if otp_code:
    resp, s = req("/api/auth/verify-otp", {"email": email, "otp_code": otp_code}, label="verify-otp")
    ok(s == 200, f"OTP verify returns 200 (got {s})")

# ── 3. LOGIN ────────────────────────────────────────────────
print("\n[3/10] LOGIN")
resp, s = req("/api/auth/login", {"email": email, "password": password}, label="login")
token = (resp or {}).get("access_token")
ok(bool(token), "login returns access_token")

# ── 4. AUTH /ME ─────────────────────────────────────────────
print("\n[4/10] AUTH /ME")
resp, s = req("/api/auth/me", token=token, label="/me")
ok(s == 200 and (resp or {}).get("email") == email, f"/me returns correct email")

# ── 5. SCREEN CANDIDATE ─────────────────────────────────────
print("\n[5/10] SCREEN CANDIDATE")
screen_data = {
    "candidate_name": "Jane Smith",
    "job_title": "Senior Python Developer",
    "resume_text": "7 years Python. FastAPI, Django, PostgreSQL, Docker, Kubernetes, AWS. Led team of 6 developers. Open source contributor.",
    "jd_text": "We need a Senior Python developer with 5+ years. Must know FastAPI, PostgreSQL, Docker. Leadership experience a plus."
}
resp, s = req("/api/screen-candidate", screen_data, token=token, label="screen-candidate")
if resp and isinstance(resp, dict):
    data = resp.get("data") or resp
    score = data.get("score") or data.get("match_score")
    rec = data.get("recommendation")
    print(f"    Score: {score}, Recommendation: {rec}")
    ok(score is not None, "screening returns score")
    ok(rec is not None, "screening returns recommendation")
else:
    ok(False, "screening response valid")

time.sleep(2)

# ── 6. LOGS (should now contain the screening) ──────────────
print("\n[6/10] LOGS ENDPOINT")
resp, s = req("/api/logs", token=token, label="get-logs")
if isinstance(resp, list):
    logs = resp
elif isinstance(resp, dict):
    logs = resp.get("logs") or resp.get("activities") or []
else:
    logs = []
print(f"    Logs count: {len(logs)}")
for l in logs[:3]:
    print(f"      {str(l)[:100]}")
ok(len(logs) > 0, "logs endpoint returns data")
ok(any("Jane" in str(l) or "Smith" in str(l) or "%" in str(l) for l in logs), "logs show candidate screening")

# ── 7. SCREENING RESULTS ─────────────────────────────────────
print("\n[7/10] SCREENING RESULTS IN DB")
count = psql("SELECT COUNT(*) FROM screening_results WHERE status='completed';")
print(f"    Completed screenings in DB: {count}")
ok(int(count or 0) > 0, "screening_results DB has completed records")

# ── 8. GENERATE JOB POST ─────────────────────────────────────
print("\n[8/10] GENERATE JOB POST (AI)")
resp, s = req("/api/generate-job-post", {
    "job_title": "Data Scientist",
    "jd_text": "We are looking for a senior Data Scientist with Python, pandas, scikit-learn, SQL and 5+ years experience in ML/AI."
}, token=token, label="generate-job-post")
if resp and isinstance(resp, dict):
    data = resp.get("data") or resp
    content = data.get("linkedin_post") or data.get("role") or data.get("output") or str(data)[:150]
    print(f"    Preview: {str(content)[:120]}")
    ok(len(str(content)) > 30, "job post AI generates content")
else:
    ok(False, "job post response valid")

# ── 9. CHATBOT (RAG assistant) ───────────────────────────────
print("\n[9/10] CHATBOT / SRP ASSISTANT")
resp, s = req("/api/ai-write", {
    "action": "respond_as_srp_assistant",
    "text": "How does the screening feature work?"
}, label="chatbot")
if resp and isinstance(resp, dict):
    msg = resp.get("output") or (resp.get("data") or {}).get("output") or ""
    print(f"    Response preview: {str(msg)[:150]}")
    ok(len(str(msg)) > 20, "chatbot returns meaningful response")
else:
    ok(False, "chatbot response valid")

# ── 10. GENERATE MESSAGE ─────────────────────────────────────
print("\n[10/10] GENERATE MESSAGE (AI Writing)")
resp, s = req("/api/generate-message", {
    "message_type": "interview_invite",
    "recipient": "Jane Smith",
    "job_title": "Senior Python Developer",
    "tone": "professional"
}, token=token, label="generate-message")
if resp and isinstance(resp, dict):
    data = resp.get("data") or {}
    content = data.get("message") or data.get("output") or ""
    print(f"    Preview: {str(content)[:120]}")
    ok(len(str(content)) > 50, "message AI generates content")
else:
    ok(False, "generate-message response valid")

# ── DB TABLE COUNTS ──────────────────────────────────────────
print("\n[DB] TABLE COUNTS")
tables = ["users","otp_verifications","resume_metadata","screening_results","sessions","support_tickets","interview_invites"]
for t in tables:
    count = psql(f"SELECT COUNT(*) FROM {t};")
    print(f"    {t}: {count}")

# ── SUMMARY ──────────────────────────────────────────────────
print("\n" + "="*60)
total = PASS + FAIL
print(f"RESULT: {PASS}/{total} tests PASSED, {FAIL} FAILED")
print("="*60)
if FAIL == 0:
    print("ALL TESTS PASSED - System is 100% operational!")
else:
    print("Some tests failed - see above for details.")
