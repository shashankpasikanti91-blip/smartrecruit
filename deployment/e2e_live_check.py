#!/usr/bin/env python3
"""Quick live HTTPS E2E check against recruit.srpailabs.com — runs locally."""
import ssl
import sys
import time
import urllib.error
import urllib.request

CTX = ssl.create_default_context()
BASE = "https://recruit.srpailabs.com"

CHECKS = [
    ("/health",              [200]),
    ("/",                    [200, 307, 308]),
    ("/login",               [200, 307, 308]),
    ("/signup",              [200, 307, 308]),
    ("/api/auth/csrf",       [200]),
    ("/api/auth/providers",  [200]),
    ("/api/auth/me",         [401, 403, 405]),
    ("/api/resume/list",     [401, 403, 405]),
    ("/api/support/tickets", [401, 403, 405]),
    ("/api/screening/results", [401, 403, 405]),
]

passed = 0
failed = 0
failures = []

print(f"\nLive E2E → {BASE}\n")

for path, expected in CHECKS:
    code = None
    err_msg = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                BASE + path, headers={"User-Agent": "SRP-E2E/2.0"}
            )
            with urllib.request.urlopen(req, context=CTX, timeout=12) as r:
                code = r.status
            break  # got a clean response — stop retrying
        except urllib.error.HTTPError as ex:
            code = ex.code
            break  # HTTP error IS a valid response — stop retrying
        except Exception as ex:
            err_msg = str(ex)
            if attempt < 2:
                time.sleep(2)

    if code is None:
        print(f"  [FAIL] {path}  ->  {err_msg}")
        failed += 1
        failures.append(path)
    else:
        ok = code in expected
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {path}  <-  HTTP {code}")
        if ok:
            passed += 1
        else:
            failed += 1
            failures.append(f"{path} (got {code}, expected {expected})")

print(f"\n{'='*50}")
print(f"  PASSED: {passed}/{passed+failed}")
if failures:
    print(f"  FAILED: {failed}/{passed+failed}")
    for f in failures:
        print(f"    x {f}")
    print("=" * 50)
    sys.exit(1)
else:
    print("  ALL CHECKS PASSED")
print("=" * 50)
