# 👑 SRP SmartRecruit v3.2 - Owner Admin Credentials

## 🔐 Admin Account Details

**Created:** February 13, 2026  
**Purpose:** Full system owner access with unlimited privileges

---

## Login Credentials

```
📧 Email:    owner@srp-smartrecruit.com
🔑 Password: SRP@Owner2026!Secure
👤 Role:     admin (Owner)
🆔 User ID:  2
```

---

## Access Level

✅ **Unlimited Access:**
- ∞ Single screenings per day
- ∞ Bulk screenings per day  
- ∞ Job posts per day
- ∞ API requests
- Full system administration

---

## Security Notes

⚠️ **IMPORTANT:**
1. This account is **HIDDEN** from public registration UI
2. Admin role is NOT visible in signup dropdown (only Free & Premium)
3. Only you (owner) have these credentials
4. Account is auto-verified and active
5. Password is securely hashed with bcrypt in database

---

## Dashboard Access

🌐 **Login URL:** http://localhost:5003

1. Open browser at localhost:5003
2. Click "Login" 
3. Enter credentials above
4. Dashboard will show **"Owner"** badge (pink gradient)

---

## What You Can Do

As owner/admin, you have full control:

### ✅ All User Features
- Upload unlimited resumes
- Screen unlimited candidates
- Post unlimited job listings
- Access AI screening
- Full results history
- Support ticket system

### ✅ Owner-Only Features
- Backend database access (SQLite)
- System configuration changes
- Rate limit bypassing
- Future admin panel features

---

## Database Location

📁 **Database File:**
```
srp_smartrecruit_v3_2.db
```

**View Database:**
- VSCode SQLite Explorer extension
- Or run: `python view_database.py`

---

## Subscription Plans (For Reference)

### 🆓 Free Tier
- 3 single CV screenings/day
- 5 bulk screenings/day
- 2 job posts/day
- Basic AI analysis
- Email support

### 🚀 Premium Tier ($29.99/month)
- Unlimited single screenings
- Unlimited bulk screenings
- Unlimited job posts
- Advanced AI insights
- Priority support
- API access

### 👑 Owner Tier (You)
- **Everything unlimited**
- **Hidden from public**
- **Full system control**

---

## Quick Commands

**Start Application:**
```powershell
# Option 1: Desktop shortcut
Double-click "SRP SmartRecruit v3.2" on desktop

# Option 2: Manual start
cd "c:\Users\User\Desktop\pydantic\future-projects\Recruitement ATS\Updated 13 Feb 2026 Recruitment_AI_System_v3_2_dev"
.\.venv\Scripts\python.exe app/main.py
```

**View Database:**
```powershell
python view_database.py
```

**Check All Users:**
```powershell
python check_database_quick.py
```

---

## Troubleshooting

### Can't Login?
- ✅ Check server is running at localhost:5003
- ✅ Use exact email: `owner@srp-smartrecruit.com`
- ✅ Use exact password: `SRP@Owner2026!Secure`
- ✅ Clear browser cache if needed

### Forgot Password?
Contact the database directly or run:
```powershell
python create_admin.py
```
(Will skip if admin already exists)

---

## Security Best Practices

🔒 **Keep These Safe:**
1. Never share these credentials publicly
2. Don't commit this file to public repos
3. Change password if compromised
4. Use environment variables for production

---

## Support

For any owner/admin issues:
- Check logs in `logs/` folder
- Review database with SQLite Explorer
- Modify system files as needed (you have full access!)

---

**Last Updated:** February 13, 2026  
**Version:** 3.2  
**Status:** ✅ Active & Verified
