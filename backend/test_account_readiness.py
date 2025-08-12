#!/usr/bin/env python3
"""
Simple VPS authentication test for existing accounts
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from instagram_accounts import get_all_accounts, get_account_details
from instagram_cookie_manager import cookie_manager

def test_account_data():
    """Test if account data is available"""
    print("🧪 Testing Account Data Availability...")
    
    accounts = get_all_accounts()
    print(f"📊 Found {len(accounts)} total accounts")
    
    if len(accounts) == 0:
        print("❌ No accounts found in instagram_accounts.json")
        return False
    
    valid_accounts = 0
    for account in accounts:
        username = account.get('username')
        if not username:
            continue
            
        print(f"\n👤 Account: {username}")
        
        # Check account details
        details = get_account_details(username)
        has_password = details and 'password' in details and details['password']
        has_totp = details and 'totp_secret' in details and details['totp_secret']
        
        print(f"  Password: {'✅' if has_password else '❌'}")
        print(f"  TOTP Secret: {'✅' if has_totp else '❌'}")
        
        # Check cookies
        has_cookies = cookie_manager.are_cookies_valid(username)
        print(f"  Valid Cookies: {'✅' if has_cookies else '❌'}")
        
        if has_cookies:
            cookie_data = cookie_manager.load_cookies(username)
            if cookie_data:
                print(f"  Cookie Count: {len(cookie_data.get('cookies', []))}")
                print(f"  Last Used: {cookie_data.get('last_used', 'Never')}")
        
        # Account is valid if it has either cookies OR (password + totp)
        account_ready = has_cookies or (has_password and has_totp)
        print(f"  Ready for Auth: {'✅' if account_ready else '❌'}")
        
        if account_ready:
            valid_accounts += 1
    
    print(f"\n📊 Summary: {valid_accounts}/{len(accounts)} accounts ready for authentication")
    return valid_accounts > 0

async def test_basic_instagram_auth():
    """Test basic Instagram authentication without full browser automation"""
    print("\n🧪 Testing Basic Instagram Authentication...")
    
    from enhanced_instagram_auth import EnhancedInstagramAuth
    
    # Initialize auth system
    auth_system = EnhancedInstagramAuth()
    print("✅ Authentication system initialized")
    
    # Test TOTP generation if we have an account with TOTP
    accounts = get_all_accounts()
    totp_tested = False
    
    for account in accounts:
        username = account.get('username')
        details = get_account_details(username)
        
        if details and details.get('totp_secret'):
            print(f"🔐 Testing TOTP generation for {username}...")
            
            try:
                # Test TOTP generation method
                import pyotp
                totp_secret = details['totp_secret']
                totp = pyotp.TOTP(totp_secret)
                code = totp.now()
                
                if code and len(code) == 6 and code.isdigit():
                    print(f"✅ TOTP generation working (code: {code})")
                    totp_tested = True
                else:
                    print(f"❌ TOTP generation failed")
                
                break
                
            except Exception as e:
                print(f"❌ TOTP test failed: {e}")
    
    if not totp_tested:
        print("⚠️ No accounts with TOTP secret found for testing")
    
    return True

async def test_daily_post_readiness():
    """Test if daily post script dependencies are ready"""
    print("\n🧪 Testing Daily Post Script Readiness...")
    
    try:
        # Test if we can import the daily post script
        from instagram_daily_post import InstagramDailyPostAutomation
        print("✅ Daily post script imports successfully")
        
        # Test initialization
        automation = InstagramDailyPostAutomation("test_script_001")
        print("✅ Daily post automation can be initialized")
        
        return True
        
    except Exception as e:
        print(f"❌ Daily post script test failed: {e}")
        return False

def main():
    """Run all account readiness tests"""
    print("🚀 VPS Account Readiness Test\n")
    
    # Test 1: Account data
    accounts_ok = test_account_data()
    
    # Test 2: Basic auth system
    asyncio.run(test_basic_instagram_auth())
    
    # Test 3: Daily post readiness
    daily_post_ok = asyncio.run(test_daily_post_readiness())
    
    print("\n" + "="*50)
    print("📊 Account Readiness Summary:")
    print(f"  Account Data: {'✅ READY' if accounts_ok else '❌ NOT READY'}")
    print(f"  Daily Post Script: {'✅ READY' if daily_post_ok else '❌ NOT READY'}")
    print("="*50)
    
    if accounts_ok and daily_post_ok:
        print("\n✅ Accounts are ready for authentication!")
        print("🚀 Next step: Run python backend/test_vps_auth.py to test browser automation")
    else:
        print("\n❌ Account setup needs attention")
        if not accounts_ok:
            print("🔧 Fix: Check instagram_accounts.json and add passwords/TOTP secrets")

if __name__ == "__main__":
    main()
