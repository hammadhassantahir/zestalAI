#!/usr/bin/env python3
"""
Test script to verify Facebook routes are working
Run this after starting your Flask server
"""

import requests
import json

# Base URL of your Flask server
BASE_URL = "http://147.93.183.79:5000"

def test_facebook_routes():
    """Test all Facebook-related routes"""
    
    print("Testing Facebook Routes...")
    print("=" * 50)
    
    # Test 1: Facebook login page
    print("\n1. Testing Facebook login page...")
    try:
        response = requests.get(f"{BASE_URL}/facebook-login")
        if response.status_code == 200:
            print("✅ Facebook login page accessible")
        else:
            print(f"❌ Facebook login page failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing Facebook login page: {e}")
    
    # Test 2: Facebook login API endpoint
    print("\n2. Testing Facebook login API endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/facebook/login",
            json={"access_token": "test_token"},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code in [400, 401]:  # Expected to fail with invalid token
            print("✅ Facebook login API endpoint accessible (returned expected error)")
        else:
            print(f"⚠️  Facebook login API endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing Facebook login API: {e}")
    
    # Test 3: Facebook callback endpoint
    print("\n3. Testing Facebook callback endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/facebook/callback")
        if response.status_code == 400:  # Expected to fail without code parameter
            print("✅ Facebook callback endpoint accessible (returned expected error)")
        else:
            print(f"⚠️  Facebook callback endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing Facebook callback: {e}")
    
    # Test 4: Facebook redirect endpoint
    print("\n4. Testing Facebook redirect endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/facebook/redirect")
        if response.status_code == 400:  # Expected to fail without code parameter
            print("✅ Facebook redirect endpoint accessible (returned expected error)")
        else:
            print(f"⚠️  Facebook redirect endpoint returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error accessing Facebook redirect: {e}")
    
    # Test 5: Test with valid callback parameters
    print("\n5. Testing Facebook callback with parameters...")
    try:
        response = requests.get(f"{BASE_URL}/api/auth/facebook/callback?code=test_code&state=test_state")
        if response.status_code == 200:
            data = response.json()
            print("✅ Facebook callback with parameters successful")
            print(f"   Response: {json.dumps(data, indent=2)}")
        else:
            print(f"⚠️  Facebook callback with parameters returned: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing Facebook callback with parameters: {e}")
    
    print("\n" + "=" * 50)
    print("Facebook routes testing completed!")

if __name__ == "__main__":
    test_facebook_routes()
