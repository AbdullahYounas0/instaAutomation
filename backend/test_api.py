#!/usr/bin/env python3
"""
Test script to verify the /api/admin/users endpoint
"""

import requests
import json

def test_admin_users_endpoint():
    # First, login to get a token
    login_url = "http://127.0.0.1:5000/api/auth/login"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    print("🔐 Testing login...")
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get('success'):
                token = login_result.get('token')
                print("✅ Login successful!")
                
                # Now test the admin/users endpoint
                users_url = "http://127.0.0.1:5000/api/admin/users"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                print("📋 Testing /api/admin/users endpoint...")
                users_response = requests.get(users_url, headers=headers)
                print(f"Users endpoint status: {users_response.status_code}")
                
                if users_response.status_code == 200:
                    users_result = users_response.json()
                    print("✅ Users endpoint working!")
                    print(f"Response: {json.dumps(users_result, indent=2)}")
                    
                    if 'users' in users_result:
                        users = users_result['users']
                        print(f"\n📊 Found {len(users)} users:")
                        for user in users:
                            print(f"  - {user.get('username', 'N/A')} (ID: {user.get('id', 'N/A')}, Role: {user.get('role', 'N/A')})")
                    
                    return True
                else:
                    print(f"❌ Users endpoint failed: {users_response.status_code}")
                    print(f"Response: {users_response.text}")
                    return False
            else:
                print(f"❌ Login failed: {login_result}")
                return False
        else:
            print(f"❌ Login request failed: {login_response.status_code}")
            print(f"Response: {login_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_admin_users_endpoint()
