"""
Quick Test Script for SRP SmartRecruit v3.2
Tests all major endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5003"

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def test_health():
    """Test health endpoint"""
    print("\n🏥 Testing Health Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print(f"{GREEN}✓ Health check passed{RESET}")
            print(f"  Response: {response.json()}")
            return True
        else:
            print(f"{RED}✗ Health check failed{RESET}")
            return False
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        return False


def test_register():
    """Test user registration"""
    print("\n📝 Testing User Registration...")
    try:
        data = {
            "email": f"test_user_{hash('test')}@example.com",
            "password": "SecurePass123!"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
        if response.status_code == 201:
            print(f"{GREEN}✓ Registration successful{RESET}")
            result = response.json()
            print(f"  User: {result.get('email')}")
            print(f"  OTP: {result.get('otp_code')} (for testing)")
            return result
        else:
            print(f"{YELLOW}⚠ Registration response: {response.status_code}{RESET}")
            print(f"  {response.json()}")
            return None
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        return None


def test_otp_verify(email, otp):
    """Test OTP verification"""
    print("\n🔐 Testing OTP Verification...")
    try:
        data = {
            "email": email,
            "otp_code": otp
        }
        response = requests.post(f"{BASE_URL}/api/auth/verify-otp", json=data)
        if response.status_code == 200:
            print(f"{GREEN}✓ OTP verified{RESET}")
            print(f"  {response.json()['message']}")
            return True
        else:
            print(f"{RED}✗ OTP verification failed{RESET}")
            return False
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        return False


def test_login(email, password):
    """Test login"""
    print("\n🔑 Testing Login...")
    try:
        data = {
            "email": email,
            "password": password
        }
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
        if response.status_code == 200:
            print(f"{GREEN}✓ Login successful{RESET}")
            result = response.json()
            print(f"  Token: {result['access_token'][:20]}...")
            print(f"  Role: {result['user']['role']}")
            return result['access_token']
        else:
            print(f"{RED}✗ Login failed{RESET}")
            return None
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        return None


def test_protected_endpoint(token):
    """Test protected endpoint (get current user)"""
    print("\n👤 Testing Protected Endpoint...")
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        if response.status_code == 200:
            print(f"{GREEN}✓ Protected endpoint accessed{RESET}")
            user = response.json()
            print(f"  Email: {user['email']}")
            print(f"  Verified: {user['is_verified']}")
            return True
        else:
            print(f"{RED}✗ Access denied{RESET}")
            return False
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        return False


def test_api_docs():
    """Test if API docs are accessible"""
    print("\n📚 Testing API Documentation...")
    try:
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print(f"{GREEN}✓ API docs accessible at {BASE_URL}/docs{RESET}")
            return True
        else:
            print(f"{RED}✗ API docs not accessible{RESET}")
            return False
    except Exception as e:
        print(f"{RED}✗ Error: {e}{RESET}")
        return False


def main():
    """Run all tests"""
    print("="*60)
    print("🧪 SRP SmartRecruit v3.2 - Quick Test Suite")
    print("="*60)
    
    results = []
    
    # Test 1: Health
    results.append(("Health Check", test_health()))
    
    # Test 2: API Docs
    results.append(("API Docs", test_api_docs()))
    
    # Test 3: Registration
    reg_result = test_register()
    if reg_result:
        results.append(("Registration", True))
        
        # Test 4: OTP Verification
        otp_verified = test_otp_verify(reg_result['email'], reg_result.get('otp_code'))
        results.append(("OTP Verification", otp_verified))
        
        if otp_verified:
            # Test 5: Login
            token = test_login(reg_result['email'], "SecurePass123!")
            if token:
                results.append(("Login", True))
                
                # Test 6: Protected Endpoint
                results.append(("Protected Endpoint", test_protected_endpoint(token)))
            else:
                results.append(("Login", False))
        else:
            results.append(("Login", False))
    else:
        results.append(("Registration", False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{GREEN}✓ PASS{RESET}" if result else f"{RED}✗ FAIL{RESET}"
        print(f"  {test_name:<25} {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{GREEN}🎉 All tests passed! System is working correctly.{RESET}")
    else:
        print(f"\n{YELLOW}⚠ Some tests failed. Check the logs above.{RESET}")
    
    print("\n" + "="*60)
    print("✅ Test complete!")
    print(f"🌐 API Documentation: {BASE_URL}/docs")
    print("="*60)


if __name__ == "__main__":
    main()
