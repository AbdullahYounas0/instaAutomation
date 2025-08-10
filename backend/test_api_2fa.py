#!/usr/bin/env python3
"""
Test the new Instagram Accounts API with TOTP support
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:5000/api"

def test_instagram_accounts_api():
    """Test the Instagram accounts API endpoints with TOTP support"""
    print("=== Testing Instagram Accounts API with 2FA Support ===")
    
    # First, we need to login to get a token (use admin credentials)
    login_data = {
        "username": "admin",  # Replace with actual admin username
        "password": "admin123"  # Replace with actual admin password
    }
    
    try:
        # Test login
        print("1. Testing admin login...")
        login_response = requests.post(f"{API_BASE_URL}/auth/login", json=login_data)
        if login_response.status_code == 200:
            login_result = login_response.json()
            if login_result.get('success'):
                token = login_result.get('token')
                print(f"✅ Login successful, token obtained")
                
                # Test getting Instagram accounts
                headers = {"Authorization": f"Bearer {token}"}
                
                print("\n2. Testing get Instagram accounts...")
                accounts_response = requests.get(f"{API_BASE_URL}/instagram-accounts", headers=headers)
                if accounts_response.status_code == 200:
                    accounts_result = accounts_response.json()
                    print(f"✅ Get accounts successful: {len(accounts_result.get('accounts', []))} accounts found")
                    
                    # Show account structure with TOTP field
                    accounts = accounts_result.get('accounts', [])
                    if accounts:
                        print("\n📋 Sample account structure:")
                        sample_account = accounts[0]
                        for key, value in sample_account.items():
                            if key in ['password', 'totp_secret'] and value:
                                print(f"  {key}: {'*' * len(str(value))} (hidden)")
                            else:
                                print(f"  {key}: {value}")
                    
                    print("\n3. Testing add Instagram account with TOTP...")
                    # Test adding account with TOTP secret
                    form_data = {
                        'username': 'test_2fa_user',
                        'password': 'test_password_123',
                        'email': 'test@example.com',
                        'phone': '+1234567890',
                        'notes': 'Test account with 2FA',
                        'totp_secret': 'JPV6WXN4CTU5TSQO3TRK7AWE2Z3XZIOP'  # 32-character TOTP secret
                    }
                    
                    add_response = requests.post(f"{API_BASE_URL}/instagram-accounts", headers=headers, data=form_data)
                    if add_response.status_code == 200:
                        add_result = add_response.json()
                        if add_result.get('success'):
                            account_id = add_result.get('account', {}).get('id')
                            print(f"✅ Add account with TOTP successful: {account_id}")
                            
                            # Test updating the account
                            print("\n4. Testing update Instagram account TOTP...")
                            update_data = {
                                'totp_secret': 'ABCD1234EFGH5678IJKL9012MNOP34QR',  # Updated 32-char TOTP secret
                                'notes': 'Updated test account with new 2FA secret'
                            }
                            
                            update_response = requests.put(f"{API_BASE_URL}/instagram-accounts/{account_id}", headers=headers, data=update_data)
                            if update_response.status_code == 200:
                                update_result = update_response.json()
                                if update_result.get('success'):
                                    print("✅ Update account TOTP successful")
                                else:
                                    print(f"❌ Update failed: {update_result.get('message')}")
                            else:
                                print(f"❌ Update request failed: {update_response.status_code}")
                            
                            # Clean up - delete test account
                            print("\n5. Cleaning up test account...")
                            delete_response = requests.delete(f"{API_BASE_URL}/instagram-accounts/{account_id}", headers=headers)
                            if delete_response.status_code == 200:
                                delete_result = delete_response.json()
                                if delete_result.get('success'):
                                    print("✅ Cleanup successful")
                                else:
                                    print(f"⚠️ Cleanup failed: {delete_result.get('message')}")
                            
                        else:
                            print(f"❌ Add account failed: {add_result.get('message')}")
                    else:
                        print(f"❌ Add account request failed: {add_response.status_code} - {add_response.text}")
                        
                else:
                    print(f"❌ Get accounts failed: {accounts_response.status_code}")
            else:
                print(f"❌ Login failed: {login_result.get('message')}")
        else:
            print(f"❌ Login request failed: {login_response.status_code}")
            print("Note: Make sure the backend server is running and admin credentials are correct")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed: Make sure the backend server is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_instagram_accounts_api()
    print("\n" + "="*60)
    print("✅ API testing completed!")
    print("\n📋 Next steps:")
    print("1. Open frontend admin dashboard")
    print("2. Navigate to Instagram Accounts tab")
    print("3. Add accounts with TOTP secrets")
    print("4. Test DM automation with 2FA-enabled accounts")
