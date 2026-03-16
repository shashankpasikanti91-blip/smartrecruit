#!/usr/bin/env python3
"""
Debug screening results endpoints
"""
import requests
import json

BASE_URL = "http://localhost:5003"

print("=" * 80)
print("ENDPOINT DEBUG TEST")
print("=" * 80)

print("\n1. Testing /api/screening-results endpoint:")
print("-" * 80)
try:
    r = requests.get(f"{BASE_URL}/api/screening-results", timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    results = data.get("results", [])
    print(f"Results count: {len(results)}")
    if data.get("error"):
        print(f"Error: {data.get('error')}")
    if results:
        if len(results) > 5:
            print(f"First 5 of {len(results)} results:")
        for item in results[:5]:
            print(f"  [{item.get('id')}] {item.get('score')}% - {item.get('recommendation')}")
    else:
        print("No results returned")
except Exception as e:
    print(f"Request failed: {e}")

print("\n2. Testing /api/logs endpoint:")
print("-" * 80)
try:
    r = requests.get(f"{BASE_URL}/api/logs", timeout=5)
    print(f"Status: {r.status_code}")
    data = r.json()
    logs = data.get("logs", [])
    print(f"Logs count: {len(logs)}")
    if logs:
        if len(logs) > 5:
            print(f"First 5 of {len(logs)} logs:")
        for log in logs[:5]:
            print(f"  {log}")
except Exception as e:
    print(f"Request failed: {e}")

print("\n3. Database file check:")
print("-" * 80)
import os
import sqlite3

db_file = 'srp_smartrecruit_v3_2.db'
if os.path.exists(db_file):
    print(f"✓ {db_file} exists")
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM screening_results")
        count = cursor.fetchone()[0]
        print(f"Total screening_results records: {count}")
        
        cursor.execute("SELECT id, score, recommendation FROM screening_results ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        if rows:
            print("Latest records in database:")
            for id, score, rec in rows:
                print(f"  [ID {id}] {score}% - {rec}")
        conn.close()
    except Exception as e:
        print(f"Database error: {e}")
else:
    print(f"✗ {db_file} DOES NOT EXIST")

print("\n" + "=" * 80)
