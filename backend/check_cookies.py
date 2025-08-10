#!/usr/bin/env python3
"""
Quick script to check saved Instagram cookies
"""

import os
from pathlib import Path
from instagram_cookie_manager import cookie_manager

def check_saved_cookies():
    """Check what cookies are currently saved"""
    
    print("Instagram Cookie Status Check")
    print("=" * 40)
    
    # Check if cookies directory exists
    cookies_dir = Path("instagram_cookies")
    
    if not cookies_dir.exists():
        print("[X] No cookies directory found")
        print("    The instagram_cookies directory hasn't been created yet.")
        print("    This means no account has been logged in with the enhanced auth system.")
        return
    
    # List cookie files
    cookie_files = list(cookies_dir.glob("*.json"))
    
    if not cookie_files:
        print("[X] No cookie files found")
        print("    The instagram_cookies directory exists but is empty.")
        return
    
    print(f"[+] Found {len(cookie_files)} cookie file(s)")
    print()
    
    # Check each saved account
    stored_accounts = cookie_manager.get_all_stored_accounts()
    
    if not stored_accounts:
        print("[!] Cookie files exist but couldn't read account data")
        return
    
    print("Stored Account Details:")
    print("-" * 60)
    
    for account in stored_accounts:
        username = account['username']
        is_valid = account['is_valid']
        status = "[OK] Valid" if is_valid else "[X] Expired/Invalid"
        
        print(f"User: {username}")
        print(f"   Status: {status}")
        print(f"   Saved: {account.get('saved_at', 'Unknown')}")
        print(f"   Last Used: {account.get('last_used', 'Never')}")
        print(f"   Login Count: {account.get('login_count', 0)}")
        print(f"   Has Proxy: {'Yes' if account.get('has_proxy') else 'No'}")
        
        if account.get('proxy_info'):
            proxy = account['proxy_info']
            print(f"   Proxy: {proxy.get('host')}:{proxy.get('port')}")
        
        print()
    
    # Summary
    valid_count = sum(1 for acc in stored_accounts if acc['is_valid'])
    print(f"Summary: {valid_count}/{len(stored_accounts)} accounts have valid cookies")
    
    if valid_count > 0:
        print("[OK] These accounts can login instantly using saved cookies!")
    else:
        print("[!] All cookies are expired - accounts need fresh login")

def check_specific_account(username):
    """Check cookies for a specific account"""
    print(f"Checking cookies for: {username}")
    print("-" * 40)
    
    # Check if cookies are valid
    if cookie_manager.are_cookies_valid(username):
        print("[OK] Valid cookies found!")
        
        # Load cookie data
        cookie_data = cookie_manager.load_cookies(username)
        if cookie_data:
            print(f"   Saved: {cookie_data.get('saved_at')}")
            print(f"   Expires: {cookie_data.get('expires_at')}")
            print(f"   Cookie count: {len(cookie_data.get('cookies', []))}")
            print(f"   Login count: {cookie_data.get('login_count', 0)}")
            
            if cookie_data.get('proxy_info'):
                proxy = cookie_data['proxy_info']
                print(f"   Proxy: {proxy.get('host')}:{proxy.get('port')}")
        
        print("[OK] This account is ready for instant login!")
    else:
        print("[X] No valid cookies found")
        print("    This account needs to login with credentials first")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Check specific account
        username = sys.argv[1]
        check_specific_account(username)
    else:
        # Check all accounts
        check_saved_cookies()