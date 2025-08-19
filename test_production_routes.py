#!/usr/bin/env python3
"""
Test script for production environment
Run this after updating your .env file and restarting the server
"""

import requests
import json
import os

# Production URL
BASE_URL = "https://app.zestal.pro/api"

def test_production_routes():
    """Test all routes in production environment"""
    
    print("Testing Production Routes...")
    print("=" * 50)
    print(f"Base URL: {BASE_URL}")
    
    # Test 1: Check if server is accessible
    print("\n1. Testing server accessibility...")
    try:
        response = requests.get(f"{BASE_URL.replace('/api', '')}/", timeout=10)
        if response.status_code == 200:
            print("✅ Server is accessible")
        else:
            print(f"⚠️  Server returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing server: {e}")
    
    # Test 2: Test CORS preflight
    print("\n2. Testing CORS preflight...")
    try:
        response = requests.options(
            f"{BASE_URL}/auth/login",
            headers={
                'Origin': 'https://app.zestal.pro',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
        )
        if response.status_code == 200:
            print("✅ CORS preflight successful")
            print(f"   CORS Headers: {dict(response.headers)}")
        else:
            print(f"⚠️  CORS preflight returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing CORS: {e}")
    
    # Test 3: Test Facebook login endpoint
    print("\n3. Testing Facebook login endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/facebook/login",
            json={"access_token": "test_token"},
            headers={
                'Content-Type': 'application/json',
                'Origin': 'https://app.zestal.pro'
            }
        )
        if response.status_code in [400, 401]:  # Expected to fail with invalid token
            print("✅ Facebook login endpoint accessible (returned expected error)")
            print(f"   Response: {response.json()}")
        else:
            print(f"⚠️  Facebook login endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing Facebook login: {e}")
    
    # Test 4: Test Facebook callback endpoint
    print("\n4. Testing Facebook callback endpoint...")
    try:
        response = requests.get(
            f"{BASE_URL}/auth/facebook/callback",
            headers={'Origin': 'https://app.zestal.pro'}
        )
        if response.status_code == 400:  # Expected to fail without code parameter
            print("✅ Facebook callback endpoint accessible (returned expected error)")
        else:
            print(f"⚠️  Facebook callback endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing Facebook callback: {e}")
    
    # Test 5: Test with valid callback parameters
    print("\n5. Testing Facebook callback with parameters...")
    try:
        response = requests.get(
            f"{BASE_URL}/auth/facebook/callback?code=test_code&state=test_state",
            headers={'Origin': 'https://app.zestal.pro'}
        )
        if response.status_code == 200:
            data = response.json()
            print("✅ Facebook callback with parameters successful")
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"⚠️  Facebook callback with parameters returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing Facebook callback with parameters: {e}")
    
    print("\n" + "=" * 50)
    print("Production routes testing completed!")

if __name__ == "__main__":
    test_production_routes()
