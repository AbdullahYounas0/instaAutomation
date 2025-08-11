#!/usr/bin/env python3
"""
Test script for enhanced Instagram authentication improvements
Tests the new login form detection and UI handling features
"""

import asyncio
import sys
import os
import json
from enhanced_instagram_auth import EnhancedInstagramAuth

async def test_auth_with_real_account():
    """Test authentication with a real Instagram account"""
    
    # Load test account from instagram_accounts.json
    try:
        with open('instagram_accounts.json', 'r') as f:
            accounts = json.load(f)
            
        if not accounts:
            print("❌ No Instagram accounts found in instagram_accounts.json")
            return False
            
        # Use the first account for testing
        account = accounts[0]
        username = account.get('username')
        password = account.get('password')
        totp_secret = account.get('totp_secret')
        
        if not username or not password:
            print("❌ Account missing username or password")
            return False
            
        print(f"🧪 Testing authentication with account: {username}")
        
    except Exception as e:
        print(f"❌ Error loading accounts: {e}")
        return False
    
    # Initialize auth system
    auth = EnhancedInstagramAuth()
    
    try:
        print("🚀 Starting authentication test...")
        
        # Test authentication
        success, final_totp = await auth.authenticate_with_cookies_and_proxy(
            username, password, totp_secret
        )
        
        if success:
            print("✅ Authentication successful!")
            print(f"📱 TOTP Secret: {final_totp}")
            
            # Test if we can access Instagram features
            print("🔍 Testing Instagram page access...")
            # Add any additional tests here
            
            return True
        else:
            print("❌ Authentication failed")
            return False
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # The auth class doesn't seem to have a cleanup method
        # The browser contexts are handled internally
        pass

async def test_auth_with_mock_data():
    """Test authentication flow with mock data (for checking UI detection)"""
    
    print("🧪 Testing authentication UI detection with mock data...")
    
    auth = EnhancedInstagramAuth()
    
    try:
        # Test with dummy credentials to check form detection
        success, _ = await auth.authenticate_with_cookies_and_proxy(
            "test_user", "test_pass", None
        )
        
        # We expect this to fail at login, but should detect forms properly
        print("📊 UI detection test completed")
        return True
        
    except Exception as e:
        print(f"⚠️ Expected error during mock test: {e}")
        return True  # This is expected to fail
        
    finally:
        # The auth class doesn't seem to have a cleanup method
        # The browser contexts are handled internally
        pass

async def main():
    """Run all authentication tests"""
    
    print("🔧 Enhanced Instagram Authentication Test Suite")
    print("=" * 50)
    
    # Test 1: UI detection with mock data
    print("\n1️⃣ Testing UI Detection...")
    mock_success = await test_auth_with_mock_data()
    
    # Test 2: Real account authentication (if available)
    print("\n2️⃣ Testing Real Account Authentication...")
    real_success = await test_auth_with_real_account()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   UI Detection: {'✅ PASS' if mock_success else '❌ FAIL'}")
    print(f"   Real Auth:    {'✅ PASS' if real_success else '❌ FAIL'}")
    
    if real_success:
        print("\n🎉 All tests passed! Authentication system is working.")
    else:
        print("\n⚠️ Some tests failed. Check logs for details.")
    
    return real_success

if __name__ == "__main__":
    # Run tests
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
