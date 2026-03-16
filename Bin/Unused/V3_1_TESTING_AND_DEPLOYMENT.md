# Recruitment ATS v3.1 - Testing & Deployment Guide

## Pre-Deployment Verification ✅

### Code Quality Checks
- ✅ Python syntax verified (no compilation errors)
- ✅ All imports resolve correctly
- ✅ Graceful fallbacks for missing dependencies
- ✅ Non-breaking changes to existing routes
- ✅ All existing endpoints preserved

### Phase Completion Summary

| Phase | Status | Component | Changes |
|-------|--------|-----------|---------|
| 1 | ✅ Complete | UI Enhancements | Message tab, Status indicator |
| 2 | ✅ Complete | Supabase Module | Isolated, async-safe handler |
| 3 | ✅ Complete | Integration Hooks | 3 async save points added |
| 4 | 🔄 In Progress | Testing | Verification steps below |

---

## Testing Checklist

### Test 1: Server Startup
```bash
python advanced_app_v3.py
```
**Expected:** Server starts on http://localhost:5001 without errors
**Verify:** 
- ✅ No import errors
- ✅ Supabase handler initializes (or gracefully falls back)
- ✅ "STARTUP" messages in logs

---

### Test 2: Dashboard Loading
1. Open http://localhost:5001 in browser
2. Verify:
   - ✅ Title shows "Recruitment ATS v3.1"
   - ✅ Green status dot appears in header
   - ✅ 5 tabs visible: Screen Candidates, Bulk Screening, Create Job Post, **Generate Message**, Activity Logs
   - ✅ All existing tabs still work

---

### Test 3: Status Indicator
1. Server running on localhost:5001
2. Verify:
   - ✅ Green dot visible and pulsing
   - ✅ "System Online" text displayed
   - ✅ Status updates every ~15 seconds (check browser console for fetch calls)
   - ✅ Stop server → indicator turns red (System Offline)

---

### Test 4: Generate Message Tab (NEW)
1. Click "Generate Message" tab
2. Fill form:
   - Message Type: "Interview Invitation"
   - Recipient: "John Smith"
   - Job Title: "Senior Developer"
   - Tone: "Professional"
   - Context: (optional) "Strong candidate with AI experience"
3. Click "Generate Message"
4. Verify:
   - ✅ Loading spinner appears
   - ✅ Message generated in ~5-10 seconds
   - ✅ Message appears in textarea
   - ✅ Copy button works (copies to clipboard)
   - ✅ Download button works (downloads .txt file)
   - ✅ Success message appears: "✓ Message generated successfully!"
5. Try all message types to verify variety

---

### Test 5: File Upload - Click Upload
1. Go to "Screen Candidates" tab
2. Click "Click to upload or drag & drop" under Resume
3. Select a PDF/DOCX file
4. Verify:
   - ✅ File uploads successfully
   - ✅ Text extracted and populated in textarea
   - ✅ Success message shown

---

### Test 6: File Upload - Drag & Drop
1. Go to "Create Job Post" tab
2. Have a PDF file ready on desktop
3. Drag the file and drop it on "Click to upload or drag & drop"
4. Verify:
   - ✅ Drag area highlights (green border)
   - ✅ File uploads and extracts text
   - ✅ Success message shown

---

### Test 7: Existing Features Still Work
#### 7a: Screen Single Candidate
1. Fill all required fields
2. Click "Screen Candidate"
3. Verify: ✅ Screening completes, score shown

#### 7b: Bulk Screening
1. Upload multiple resume files
2. Provide JD
3. Click "Screen All Candidates"
4. Verify: ✅ All candidates screened

#### 7c: Job Post Generation
1. Fill job details
2. Click "Generate Posts"
3. Verify: ✅ Posts generated for all 4 platforms

#### 7d: Activity Logs
1. Click "Activity Logs" tab
2. Click "Refresh Logs"
3. Verify: ✅ Recent logs displayed

---

### Test 8: Backend - Supabase Integration
**Only if Supabase is configured in .env**

1. Run a screening:
   - Input resume and JD
   - Click "Screen Candidate"
   - Check Supabase dashboard
2. Verify in "screening_results" table:
   - ✅ Row created with candidate_name, job_title, match_score
   - ✅ Timestamp recorded

3. Run generate message:
   - Generate a message
   - Check Supabase dashboard
4. Verify in "ai_messages" table:
   - ✅ Row created with message_type, recipient, message_content
   - ✅ Timestamp recorded

5. Upload resumes:
   - Upload 2-3 resume files
   - Check Supabase dashboard
6. Verify in "resumes" table:
   - ✅ Rows created with candidate_name, filename, file_hash
   - ✅ No full file content stored (just metadata)

---

### Test 9: Graceful Fallback (Supabase Optional)
1. Remove/comment SUPABASE_URL from .env
2. Restart server
3. Try all features (screening, messaging, uploads)
4. Verify:
   - ✅ All features work normally
   - ✅ No database errors in UI
   - ✅ Logs show "not connected" messages for Supabase

---

### Test 10: Error Handling
1. Try screening with empty fields → should show error
2. Try generating message without recipient → should show error
3. Upload invalid file type → should show error
4. Try generating message with API key issues → should show graceful error
5. Verify:
   - ✅ All errors handled gracefully
   - ✅ User-friendly error messages
   - ✅ App doesn't crash

---

## Database Schema Setup (If Using Supabase)

Run this in Supabase SQL editor to create required tables:

```sql
-- Resumes (metadata only)
CREATE TABLE resumes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  candidate_name TEXT NOT NULL,
  filename TEXT NOT NULL,
  file_hash TEXT UNIQUE,
  num_pages INT DEFAULT 1,
  upload_timestamp TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Screening Results
CREATE TABLE screening_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  resume_id UUID REFERENCES resumes(id) ON DELETE SET NULL,
  candidate_name TEXT NOT NULL,
  job_title TEXT NOT NULL,
  match_score INT CHECK (match_score >= 0 AND match_score <= 100),
  recommendation TEXT,
  assessment TEXT,
  screening_timestamp TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- AI Messages
CREATE TABLE ai_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  message_type TEXT NOT NULL,
  recipient TEXT NOT NULL,
  job_title TEXT NOT NULL,
  tone TEXT,
  message_content TEXT,
  generated_timestamp TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Activity Logs
CREATE TABLE activity_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  log_level TEXT,
  log_message TEXT,
  component TEXT,
  timestamp TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Job Posts
CREATE TABLE job_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_title TEXT NOT NULL,
  location TEXT,
  experience INT,
  platforms JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS if desired
ALTER TABLE resumes ENABLE ROW LEVEL SECURITY;
ALTER TABLE screening_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE job_posts ENABLE ROW LEVEL SECURITY;
```

---

## Performance Notes

### Non-Blocking Operations
- All Supabase saves happen in background threads
- API responses return immediately
- Database writes don't delay UI
- Perfect for production workloads

### Async Patterns Used
- Thread-based async (works with Flask)
- Graceful degradation if Supabase unavailable
- No blocking I/O on main request thread
- Suitable for moderate traffic (1000s of concurrent users)

---

## Rollback Plan

If any issues occur, rollback is simple:

```bash
git log --oneline
# Should see Phase 1, 2, 3 commits at top

# To rollback to v3.0 stable:
git revert HEAD~2  # Revert Phase 3
git revert HEAD~1  # Revert Phase 2  
git revert HEAD    # Revert Phase 1

# Or reset directly:
git reset --hard <commit-before-phase-1>
```

---

## Production Deployment Checklist

- [ ] All tests passed (Test 1-10 above)
- [ ] Supabase tables created (if using database)
- [ ] .env variables configured:
  - [ ] OPENAI_API_KEY set
  - [ ] OPENAI_MODEL set
  - [ ] SUPABASE_URL set (if using database)
  - [ ] SUPABASE_KEY set (if using database)
- [ ] Server started without errors
- [ ] Status indicator working
- [ ] All 5 tabs visible and functional
- [ ] Generate Message tab working
- [ ] File uploads working (click and drag-drop)
- [ ] Existing features verified
- [ ] Graceful fallback tested
- [ ] Database saves verified (optional)
- [ ] Error handling verified
- [ ] Performance acceptable
- [ ] Logs showing expected activity

---

## Support & Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'supabase'"
**Solution:** The app gracefully disables Supabase. To fix:
```bash
pip install supabase==2.0.0
```

### Issue: Status indicator red/not updating
**Solution:** Check `/api/status` endpoint:
```bash
curl http://localhost:5001/api/status
# Should return: {"status": "online", "timestamp": "...", "model": "...", "webhook": true/false}
```

### Issue: Message tab not generating messages
**Solution:** Verify OpenAI API key:
```bash
# Check .env file has valid OPENAI_API_KEY
curl -X POST http://localhost:5001/api/generate-message \
  -H "Content-Type: application/json" \
  -d '{"message_type":"interview_invite", "recipient":"Test", "job_title":"Role"}'
```

### Issue: Supabase not saving data
**Solution:** Check if connected:
```bash
# Look in logs for "[SUPABASE]" messages
# If it says "not connected", check .env for SUPABASE_URL and SUPABASE_KEY
```

---

## Next Steps (Future Versions)

- [ ] Add authentication layer
- [ ] Implement webhook logging
- [ ] Add email integration for generated messages
- [ ] Create analytics dashboard
- [ ] Add batch export to Excel
- [ ] Implement message templates
- [ ] Add candidate pipeline management
- [ ] Create team collaboration features

---

**Version:** 3.1 Development
**Release Date:** February 7, 2026
**Status:** Ready for Testing ✅
