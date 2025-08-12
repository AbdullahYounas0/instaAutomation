#!/usr/bin/env python3
"""
Quick Instagram account setup script for VPS
"""

import sys
import os
import json
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from instagram_accounts import instagram_accounts_manager

def setup_test_account():
    """Add a test Instagram account"""
    print("🔧 Instagram Account Setup")
    print("="*50)
    
    # Check current accounts
    accounts = instagram_accounts_manager.get_all_accounts()
    print(f"📊 Current accounts: {len(accounts)}")
    
    if len(accounts) > 0:
        print("\n👤 Existing accounts:")
        for acc in accounts:
            print(f"  - {acc['username']} (Active: {acc.get('is_active', True)})")
        
        choice = input("\n🤔 Add another account? (y/n): ").strip().lower()
        if choice != 'y':
            print("✅ Using existing accounts")
            return
    
    print("\n📝 Enter Instagram account details:")
    
    username = input("Username: ").strip()
    if not username:
        print("❌ Username required")
        return
    
    password = input("Password: ").strip()
    if not password:
        print("❌ Password required")
        return
    
    email = input("Email (optional): ").strip()
    phone = input("Phone (optional): ").strip()
    
    print("\n🔐 2FA Setup (HIGHLY RECOMMENDED):")
    print("If your Instagram account has 2FA enabled with authenticator app:")
    totp_secret = input("TOTP Secret Key (optional): ").strip()
    
    notes = input("Notes (optional): ").strip()
    
    try:
        # Add the account
        new_account = instagram_accounts_manager.add_account(
            username=username,
            password=password,
            email=email,
            phone=phone,
            notes=notes,
            totp_secret=totp_secret
        )
        
        print(f"\n✅ Account '{username}' added successfully!")
        print(f"   Account ID: {new_account['id']}")
        print(f"   Has 2FA: {'Yes' if totp_secret else 'No'}")
        
        # Test TOTP if provided
        if totp_secret:
            try:
                import pyotp
                totp = pyotp.TOTP(totp_secret)
                current_code = totp.now()
                print(f"   🔐 Current 2FA code: {current_code}")
                print("   (Use this to verify 2FA is working)")
            except Exception as e:
                print(f"   ⚠️ 2FA test failed: {e}")
        
    except Exception as e:
        print(f"❌ Failed to add account: {e}")

def show_account_status():
    """Show current account status"""
    print("\n📊 Account Status Summary:")
    print("="*50)
    
    accounts = instagram_accounts_manager.get_all_accounts()
    
    if len(accounts) == 0:
        print("❌ No accounts configured")
        return
    
    for acc in accounts:
        username = acc['username']
        print(f"\n👤 {username}:")
        print(f"   Password: {'✅' if acc.get('password') else '❌'}")
        print(f"   Email: {acc.get('email', 'Not set')}")
        print(f"   2FA Secret: {'✅' if acc.get('totp_secret') else '❌'}")
        print(f"   Active: {'✅' if acc.get('is_active', True) else '❌'}")
        print(f"   Created: {acc.get('created_at', 'Unknown')}")

def main():
    """Main setup function"""
    print("🚀 Instagram Account Setup for VPS")
    print("="*50)
    
    while True:
        print("\nOptions:")
        print("1. Add new Instagram account")
        print("2. Show account status")
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == '1':
            setup_test_account()
        elif choice == '2':
            show_account_status()
        elif choice == '3':
            break
        else:
            print("❌ Invalid choice")
    
    print("\n✅ Setup complete!")
    print("🚀 Next steps:")
    print("   1. Test accounts: python backend/test_account_readiness.py")
    print("   2. Test VPS auth: python backend/test_vps_auth.py")
    print("   3. Run automation: python backend/instagram_daily_post.py")

if __name__ == "__main__":
    main()
