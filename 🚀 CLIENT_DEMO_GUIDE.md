# 🚀 Client Demo Setup Guide
## SRP SmartRecruit v3.2 - 7-Day Trial

---

## ✅ Quick Start (3 Steps)

### Step 1: Create Demo Account
```powershell
# Run this command in the project folder:
.venv\Scripts\python.exe CREATE_DEMO_ACCOUNT.py
```

**Demo Credentials Created:**
- 📧 Email: `demo@srp-smartrecruit.com`
- 🔑 Password: `Demo@2026`
- 🎯 Access: Premium (Full Features)
- ⏰ Valid: 7 Days

---

### Step 2: Start Server with Public URL
```
Double-click: Desktop shortcut "SRP SmartRecruit v3.2"
OR
Run: START_WITH_NGROK.bat
```

**This will:**
- ✅ Start the server
- ✅ Create public URL (ngrok)
- ✅ Display shareable link
- ✅ Keep running for 7 days

---

### Step 3: Share with Client

**Copy the ngrok URL shown in terminal:**
```
🌐 Public URL: https://xxxx-xx-xxx-xxx-xx.ngrok-free.app
```

**Send to client:**
```
🎯 Access Your Demo:
URL: https://xxxx-xx-xxx-xxx-xx.ngrok-free.app

📧 Login Credentials:
Email: demo@srp-smartrecruit.com
Password: Demo@2026

⏰ Valid for: 7 days
🎁 Full Premium Access included
```

---

## 🔥 What Client Can Demo

### ✅ Full Premium Features:
- ✓ **Unlimited resume screenings**
- ✓ **Unlimited bulk CV processing** (5-50 resumes at once)
- ✓ **Unlimited job posts** (LinkedIn, Indeed, Email, WhatsApp)
- ✓ **AI Writing Assistant** (rewrite, paraphrase, reply)
- ✓ **Advanced AI insights**
- ✓ **Real-time activity logs**
- ✓ **Secure authentication**

### 📱 Mobile Friendly:
- ✓ Works on phones and tablets
- ✓ Responsive design
- ✓ Touch-optimized

---

## 🛡️ Security Features (Built-in)

✅ **Strong password requirements**
✅ **Email validation**
✅ **OTP verification system**
✅ **Session management**
✅ **Encrypted passwords**
✅ **Secure database storage**
✅ **Input validation**
✅ **Error handling**

---

## 📊 Database Status

Run this to check database:
```powershell
.venv\Scripts\python.exe view_database.py
```

**Automatically stores:**
- ✓ User accounts
- ✓ Screening results
- ✓ Job posts
- ✓ Activity logs
- ✓ Session data

---

## 🔧 Troubleshooting

### Issue: Ngrok not working
**Solution:**
1. Install ngrok: https://ngrok.com/download
2. Get auth token: https://dashboard.ngrok.com/get-started/your-authtoken
3. Run: `ngrok config add-authtoken YOUR_TOKEN`
4. Restart using desktop shortcut

### Issue: Server not starting
**Solution:**
```powershell
# Stop any running processes
Get-Process -Name "*python*","*uvicorn*" | Stop-Process -Force

# Start fresh
.\START_WITH_NGROK.bat
```

### Issue: Demo account not working
**Solution:**
```powershell
# Recreate demo account
.venv\Scripts\python.exe CREATE_DEMO_ACCOUNT.py
```

### Issue: Database not saving data
**Solution:**
```powershell
# Check database status
.venv\Scripts\python.exe check_database_quick.py

# View all data
.venv\Scripts\python.exe view_database.py
```

---

## 📞 During Demo - Important URLs

### For You (Admin):
```
Local: http://localhost:5003
Database Viewer: python view_database.py
Logs: logs/recruitment_ai.log
```

### For Client:
```
Public URL: https://xxxx.ngrok-free.app (from terminal)
Demo Login: demo@srp-smartrecruit.com / Demo@2026
```

---

## ⏰ After 7 Days

### Option 1: Extend Demo
```powershell
# Update demo account expiry
# (Manual database update or recreate account)
.venv\Scripts\python.exe CREATE_DEMO_ACCOUNT.py
```

### Option 2: Convert to Paid
1. Client can register their own account
2. They choose Premium plan (₹30,000/month)
3. They get their own credentials
4. Delete demo account

---

## 🎯 Demo Tips

### Before Client Demo:
✅ Test everything works locally first
✅ Create demo account
✅ Start ngrok and verify URL works
✅ Do a test screening to show speed
✅ Have sample resumes and JD ready

### During Demo:
✅ Show single resume screening (fast results)
✅ Show bulk processing (5-10 resumes)
✅ Generate job posts (all 4 formats)
✅ Show AI writing assistant
✅ Show mobile version (open on phone)
✅ Highlight security features

### After Demo:
✅ Send them the URL and credentials again
✅ Give them 7 days to explore
✅ Follow up in 3-4 days
✅ Answer any questions
✅ Show pricing plans

---

##  Current Pricing

### Free Trial:
- ✓ 3 resume screenings/day
- ✓ 5 bulk CV screenings/day
- ✓ 3 job posts/day
- ✓ Basic features

### Premium (₹30,000/month):
- ✓ **Unlimited everything**
- ✓ Advanced AI insights
- ✓ Priority support
- ✓ API access
- ✓ All features unlocked

---

## 📝 Files Cleaned Up

### ✅ Organized Structure:
```
Project Root/
├── 🚀 Desktop Shortcut (created on Desktop)
├── START_WITH_NGROK.bat (main startup)
├── CREATE_DEMO_ACCOUNT.py (demo setup)
├── 🚀 CLIENT_DEMO_GUIDE.md (this file)
├── app/ (main application)
├── templates/ (HTML files)
├── logs/ (activity logs)
├── Bin/Unused/ (old test files - moved here)
└── srp_smartrecruit_v3_2.db (database)
```

### 🗑️ Moved to Bin/Unused:
- All test_*.py files
- Old markdown documentation
- Duplicate configuration files
- Temporary debug scripts

**Only important files remaining in root!**

---

## ✅ Final Checklist

Before giving to client:

- [ ] Desktop shortcut created and working
- [ ] Demo account created (email/password noted)
- [ ] Database verified (python view_database.py)
- [ ] Ngrok installed and configured
- [ ] Public URL generated and tested
- [ ] All features tested locally
- [ ] Mobile version tested
- [ ] Sample resumes prepared
- [ ] Sample job descriptions prepared
- [ ] This guide reviewed

---

## 🎉 You're Ready!

Everything is set up for a professional client demo:

1. ✅ **Clean project** (unused files moved to Bin)
2. ✅ **Desktop shortcut** (easy access)
3. ✅ **Demo account** (ready to use)
4. ✅ **Database working** (stores all data)
5. ✅ **Public URL** (ngrok integration)
6. ✅ **7-day access** (stable and professional)
7. ✅ **Security built-in** (production-ready)

**Double-click the desktop shortcut and share the URL!**

---

## 📞 Support

If you have any issues:
1. Check this guide first
2. Run database verification
3. Restart using desktop shortcut
4. Check logs folder for errors

**Good luck with your client demo!** 🚀
