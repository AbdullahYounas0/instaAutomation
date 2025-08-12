#!/usr/bin/env python3
"""
Fix existing account 2FA secret format
"""

import sys
import os
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from instagram_accounts import instagram_accounts_manager

def fix_totp_secrets():
    """Fix TOTP secret formatting for existing accounts"""
    print("🔧 Fixing TOTP Secret Formats...")
    
    accounts = instagram_accounts_manager.get_all_accounts()
    
    if not accounts:
        print("❌ No accounts found")
        return
    
    fixed_count = 0
    
    for account in accounts:
        username = account['username']
        totp_secret = account.get('totp_secret', '')
        
        if totp_secret and (' ' in totp_secret or '-' in totp_secret):
            # Clean the TOTP secret
            cleaned_secret = totp_secret.replace(' ', '').replace('-', '').upper()
            
            print(f"👤 {username}:")
            print(f"   Old: {totp_secret}")
            print(f"   New: {cleaned_secret}")
            
            # Update the account
            success = instagram_accounts_manager.update_account(
                account['id'], 
                {'totp_secret': cleaned_secret}
            )
            
            if success:
                print("   ✅ Fixed!")
                fixed_count += 1
                
                # Test the fixed TOTP
                try:
                    import pyotp
                    totp = pyotp.TOTP(cleaned_secret)
                    current_code = totp.now()
                    print(f"   🔐 Test 2FA code: {current_code}")
                except Exception as e:
                    print(f"   ❌ TOTP test still failed: {e}")
            else:
                print("   ❌ Update failed")
    
    print(f"\n📊 Fixed {fixed_count} account(s)")

if __name__ == "__main__":
    fix_totp_secrets()
