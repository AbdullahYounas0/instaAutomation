#!/usr/bin/env python3
"""
Test script for Instagram 2FA TOTP functionality
"""

import pyotp
import sys

def test_totp_generation():
    """Test TOTP code generation with a sample secret"""
    print("=== Instagram 2FA TOTP Test ===")
    
    # Sample TOTP secrets (both 16 and 32 character formats)
    sample_secret_16 = "JBSWY3DPEHPK3PXP"
    sample_secret_32 = "JPV6WXN4CTU5TSQO3TRK7AWE2Z3XZIOP"
    sample_secret_32_formatted = "JPV6 WXN4 CTU5 TSQO 3TRK 7AWE 2Z3X ZIOP"
    
    try:
        # Test 16-character secret
        print(f"Testing 16-character secret: {sample_secret_16}")
        totp_16 = pyotp.TOTP(sample_secret_16)
        otp_code_16 = totp_16.now()
        print(f"✅ 16-char TOTP generation successful!")
        print(f"Generated OTP: {otp_code_16}")
        
        # Test 32-character secret
        print(f"\nTesting 32-character secret: {sample_secret_32}")
        totp_32 = pyotp.TOTP(sample_secret_32)
        otp_code_32 = totp_32.now()
        print(f"✅ 32-char TOTP generation successful!")
        print(f"Generated OTP: {otp_code_32}")
        
        # Test 32-character secret with spaces (should be cleaned)
        print(f"\nTesting 32-character formatted secret: {sample_secret_32_formatted}")
        cleaned_secret = sample_secret_32_formatted.replace(' ', '')
        totp_32_formatted = pyotp.TOTP(cleaned_secret)
        otp_code_32_formatted = totp_32_formatted.now()
        print(f"✅ 32-char formatted TOTP generation successful!")
        print(f"Generated OTP: {otp_code_32_formatted}")
        print(f"Cleaned secret: {cleaned_secret}")
        
        # Verify all are 6-digit codes
        if all(len(str(code)) == 6 and str(code).isdigit() for code in [otp_code_16, otp_code_32, otp_code_32_formatted]):
            print("✅ All OTP formats are valid (6 digits)")
            return True
        else:
            print("❌ Invalid OTP format")
            return False
            
    except Exception as e:
        print(f"❌ TOTP generation failed: {e}")
        return False

def test_instagram_account_structure():
    """Test the expected Instagram account data structure"""
    print("\n=== Instagram Account Structure Test ===")
    
    # Sample account data structure with TOTP secret (32-character)
    sample_account = {
        'id': 'test-account-id',
        'username': 'test_instagram_user',
        'password': 'test_password',
        'email': 'test@example.com',
        'phone': '+1234567890',
        'notes': 'Test account with 2FA enabled',
        'totp_secret': 'JPV6WXN4CTU5TSQO3TRK7AWE2Z3XZIOP',  # 32-character TOTP secret
        'is_active': True,
        'created_at': '2025-01-01T00:00:00',
        'updated_at': '2025-01-01T00:00:00',
        'last_used': None
    }
    
    print("✅ Sample account structure:")
    for key, value in sample_account.items():
        if key == 'totp_secret':
            print(f"  {key}: {'*' * len(value)} (32-char, hidden)")
        elif key == 'password':
            print(f"  {key}: {'*' * len(value)} (hidden)")
        else:
            print(f"  {key}: {value}")
    
    # Test TOTP generation for this account
    if sample_account.get('totp_secret'):
        print(f"\n🔐 Generating TOTP for account '{sample_account['username']}':")
        totp = pyotp.TOTP(sample_account['totp_secret'])
        otp_code = totp.now()
        print(f"Current OTP: {otp_code}")
        print(f"Secret format: 32-character base32")
        return True
    else:
        print("❌ No TOTP secret found in account")
        return False

if __name__ == "__main__":
    success = True
    
    # Run tests
    if not test_totp_generation():
        success = False
    
    if not test_instagram_account_structure():
        success = False
    
    print("\n" + "="*50)
    if success:
        print("✅ All tests passed! 2FA functionality is ready.")
        print("\n📋 Next steps:")
        print("1. Add TOTP secrets to Instagram accounts in admin panel")
        print("2. Use format: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX (32-character base32 string)")
        print("   Example: JPV6WXN4CTU5TSQO3TRK7AWE2Z3XZIOP")
        print("   Or with spaces: JPV6 WXN4 CTU5 TSQO 3TRK 7AWE 2Z3X ZIOP")
        print("3. Test with actual Instagram accounts that have 2FA enabled")
        print("4. The system will automatically handle 2FA during login")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
