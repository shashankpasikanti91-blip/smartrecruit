#!/usr/bin/env python3
"""Create and verify demo accounts via API + direct DB update."""
import urllib.request, urllib.error, json, subprocess, time

BASE = "https://recruit.srpailabs.com"
PGPASS = "AtsSecure4a16b511b68b557d2bf68af7"

ACCOUNTS = [
    {"email": "demo@srpailabs.com",   "password": "SRPDemo2026!",     "role": "admin", "label": "Demo Admin"},
    {"email": "client@srpailabs.com", "password": "ClientView2026!",  "role": "pro",   "label": "Client Viewer"},
]

def api(path, data):
    body = json.dumps(data).encode()
    r = urllib.request.Request(BASE + path, data=body, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return json.loads(resp.read().decode()), resp.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode()), e.code

def psql(query):
    r = subprocess.run(
        ["docker", "exec", "-e", f"PGPASSWORD={PGPASS}", "srp-ats-db",
         "psql", "-U", "srp_ats", "-d", "srp_ats", "-t", "-c", query],
        capture_output=True, text=True
    )
    return r.stdout.strip()

for acc in ACCOUNTS:
    email = acc["email"]
    password = acc["password"]
    role = acc["role"]
    label = acc["label"]

    # Check if user exists already
    exists = psql(f"SELECT id FROM users WHERE email='{email}';").strip()
    if exists:
        # Update: set verified, active, role
        psql(f"UPDATE users SET is_verified=true, is_active=true, role='{role}' WHERE email='{email}';")
        print(f"[UPDATED] {label}")
        print(f"  Email   : {email}")
        print(f"  Password: {password}")
        print(f"  Role    : {role}")
        # Test login
        res, s = api("/api/auth/login", {"email": email, "password": password})
        if s == 200 and res.get("access_token"):
            print(f"  Login   : OK (token obtained)")
        else:
            print(f"  Login   : {s} - {res}")
    else:
        # Register
        res, s = api("/api/auth/register", {"email": email, "password": password, "full_name": label, "company": "SRP AI"})
        print(f"  Register: {s} - {res.get('message','') or res}")
        time.sleep(0.5)
        # Force-verify and set role in DB
        psql(f"UPDATE users SET is_verified=true, is_active=true, role='{role}' WHERE email='{email}';")
        # Test login
        res, s = api("/api/auth/login", {"email": email, "password": password})
        if s == 200 and res.get("access_token"):
            print(f"[CREATED] {label}")
            print(f"  Email   : {email}")
            print(f"  Password: {password}")
            print(f"  Role    : {role}")
            print(f"  Login   : OK (token obtained)")
        else:
            print(f"[FAILED]  {label}: login returned {s} - {res}")
    print()

# Verify final DB state
print("=== DB USER LIST ===")
result = psql("SELECT id, email, role, is_verified, is_active FROM users ORDER BY id;")
print(result)
