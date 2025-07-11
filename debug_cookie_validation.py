#!/usr/bin/env python3
"""
Debug cookie validation - simulate the PowerShell request issue
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_cookie_validation():
    print("=== Cookie Validation Debug ===")
    
    # Step 1: Normal login flow
    print("\n1. Normal login flow:")
    session = requests.Session()
    login_response = session.post(f"{BASE_URL}/api/auth/login", 
                                 json={"username": "testuser", "password": "testpass"})
    print(f"Login status: {login_response.status_code}")
    print(f"Session cookies: {dict(session.cookies)}")
    
    # Step 2: Test sessions endpoint with proper session
    print("\n2. Sessions with proper session:")
    sessions_response = session.get(f"{BASE_URL}/api/dialogue/sessions")
    print(f"Sessions status: {sessions_response.status_code}")
    print(f"Sessions success: {sessions_response.json().get('success', 'N/A')}")
    
    # Step 3: Simulate PowerShell request (without login cookie)
    print("\n3. Simulating PowerShell request (no session cookie):")
    headers = {
        "Accept": "application/json",
        "Referer": "http://localhost:3000/",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "x-internal-api-request": "1",
        "sec-ch-ua-platform": '"Windows"',
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Request without session cookie (like your PowerShell request)
    no_session_response = requests.get(f"{BASE_URL}/api/dialogue/sessions?_t=1752128498476", 
                                      headers=headers)
    print(f"No session status: {no_session_response.status_code}")
    try:
        no_session_data = no_session_response.json()
        print(f"No session response: {no_session_data}")
    except:
        print(f"No session response (text): {no_session_response.text}")
    
    # Step 4: Test with manually extracted cookie
    print("\n4. Test with manually extracted cookie:")
    extracted_cookies = dict(session.cookies)
    manual_response = requests.get(f"{BASE_URL}/api/dialogue/sessions?_t=1752128498476",
                                  headers=headers,
                                  cookies=extracted_cookies)
    print(f"Manual cookie status: {manual_response.status_code}")
    try:
        manual_data = manual_response.json()
        print(f"Manual cookie success: {manual_data.get('success', 'N/A')}")
    except:
        print(f"Manual cookie response (text): {manual_response.text}")
    
    # Step 5: Check what cookie format is expected
    print("\n5. Cookie format analysis:")
    if extracted_cookies:
        for name, value in extracted_cookies.items():
            print(f"Cookie: {name} = {value[:50]}..." if len(value) > 50 else f"Cookie: {name} = {value}")
    
    # Step 6: Test auth status endpoint
    print("\n6. Auth status check:")
    auth_status_response = requests.get(f"{BASE_URL}/api/auth/status", 
                                       headers=headers,
                                       cookies=extracted_cookies)
    print(f"Auth status: {auth_status_response.status_code}")
    try:
        auth_data = auth_status_response.json()
        print(f"Auth authenticated: {auth_data.get('data', {}).get('authenticated', 'N/A')}")
    except:
        print(f"Auth status response (text): {auth_status_response.text}")

if __name__ == "__main__":
    test_cookie_validation()