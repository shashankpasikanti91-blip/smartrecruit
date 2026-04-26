#!/usr/bin/env python3
import paramiko

HOST = "5.223.67.236"; USER = "root"; PASS = "856Reey@nsh"
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

# Check the main.py router includes on the server
_, s, _ = c.exec_command("cat /opt/srp-ats/app/main.py | grep -E 'include_router|prefix' | head -30")
print("=== main.py routers ===")
print(s.read().decode())

# Check v3_2_compat.py routes
_, s, _ = c.exec_command("cat /opt/srp-ats/app/routers/v3_2_compat.py | grep -E '@router\\.get|@router\\.post|prefix' | head -30")
print("=== v3_2_compat routes ===")
print(s.read().decode())

# Check screening.py routes
_, s, _ = c.exec_command("cat /opt/srp-ats/app/routers/screening.py | grep -E '@router\\.get|@router\\.post|prefix' | head -20")
print("=== screening.py routes ===")
print(s.read().decode())

# Test some variations
for route in ["/api/resume/list", "/api/screen/results", "/api/screening/results",
              "/api/ai/screen", "/api/jobs", "/api/v1/jobs", "/health", "/api/health"]:
    _, s, _ = c.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:8009{route}")
    code = s.read().decode().strip()
    print(f"  {route}: {code}")

c.close()

