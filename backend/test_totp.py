#!/usr/bin/env python3
"""
Test script to verify TOTP generation with different secret formats
"""

from instagram_dm_automation import DMAutomationEngine

def test_totp_generation():
    print("=== TOTP Generation Testing ===\n")
    
    # Create automation instance
    automation = DMAutomationEngine()
    
    # Test 16-character secret
    print("1. Testing 16-character secret:")
    secret_16 = "ABCDEFGHIJKLMNOP"
    try:
        code = automation.generate_totp_code("test_user", secret_16)
        print(f"   Secret: {secret_16}")
        print(f"   TOTP Code: {code}")
        print("   ✅ SUCCESS")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 32-character secret without spaces
    print("2. Testing 32-character secret (no spaces):")
    secret_32 = "JPV6WXN4CTU5TSQO3TRK7AWE2Z3XZIOP"
    try:
        code = automation.generate_totp_code("test_user", secret_32)
        print(f"   Secret: {secret_32}")
        print(f"   TOTP Code: {code}")
        print("   ✅ SUCCESS")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test 32-character secret with spaces
    print("3. Testing 32-character secret (with spaces):")
    secret_32_spaced = "JPV6 WXN4 CTU5 TSQO 3TRK 7AWE 2Z3X ZIOP"
    try:
        code = automation.generate_totp_code("test_user", secret_32_spaced)
        print(f"   Secret: {secret_32_spaced}")
        print(f"   TOTP Code: {code}")
        print("   ✅ SUCCESS")
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
    
    print("\n" + "-"*50 + "\n")
    
    # Test invalid secret
    print("4. Testing invalid secret:")
    invalid_secret = "INVALID"
    try:
        code = automation.generate_totp_code("test_user", invalid_secret)
        if code is None:
            print(f"   Secret: {invalid_secret}")
            print(f"   ❌ Expected Error: Function returned None")
            print("   ✅ ERROR HANDLING WORKS")
        else:
            print(f"   Secret: {invalid_secret}")
            print(f"   TOTP Code: {code}")
            print("   ⚠️  UNEXPECTED SUCCESS")
    except Exception as e:
        print(f"   Secret: {invalid_secret}")
        print(f"   ❌ Expected Error: {e}")
        print("   ✅ ERROR HANDLING WORKS")
    
    print("\n" + "="*50)
    print("TOTP Testing Complete!")

if __name__ == "__main__":
    test_totp_generation()
