#!/usr/bin/env python3
"""
Test script to verify Instagram Daily Post login functionality works correctly
"""

import asyncio
import sys
import os
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from instagram_daily_post import InstagramDailyPostAutomation

async def test_login_only():
    """Test just the login functionality without posting"""
    
    # Create a test automation instance
    script_id = "test_login_001"
    automation = InstagramDailyPostAutomation(script_id)
    
    print("=" * 60)
    print("INSTAGRAM DAILY POST - LOGIN TEST")
    print("=" * 60)
    print(f"Script ID: {script_id}")
    print("This test will only attempt login, no posting will occur.")
    print("=" * 60)
    
    # Test account (replace with your test account)
    test_username = input("Enter test username: ").strip()
    test_password = input("Enter test password: ").strip()
    
    if not test_username or not test_password:
        print("❌ Username and password required for testing")
        return
    
    print(f"\n🚀 Starting login test for: {test_username}")
    print("-" * 40)
    
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            print("🔧 Launching browser for login test...")
            
            try:
                browser = await p.chromium.launch(
                    headless=False,  # Show browser for manual inspection
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                print("✅ Browser launched successfully")
                print("🔑 Attempting login...")
                
                # Test the login method
                login_success = await automation.login_instagram_with_2fa(
                    page, test_username, test_password, "TEST"
                )
                
                if login_success:
                    print("✅ LOGIN TEST PASSED!")
                    print("✅ Login functionality is working correctly")
                    
                    # Wait a bit to see the result
                    print("📊 Waiting 10 seconds to verify login state...")
                    await asyncio.sleep(10)
                    
                    current_url = page.url
                    print(f"📊 Final URL: {current_url}")
                    
                    if "instagram.com" in current_url and "login" not in current_url:
                        print("✅ Successfully logged in and redirected!")
                    else:
                        print("⚠️ Login may have issues - check browser manually")
                    
                else:
                    print("❌ LOGIN TEST FAILED!")
                    print("❌ Login functionality needs investigation")
                    print("📊 Check browser window for more details")
                    print("📊 Waiting 20 seconds for manual inspection...")
                    await asyncio.sleep(20)
                
                await browser.close()
                
            except Exception as e:
                print(f"❌ Browser test error: {e}")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Instagram Daily Post - Login Test")
    print("This script tests ONLY the login functionality")
    print("No media will be posted during this test")
    print()
    
    try:
        asyncio.run(test_login_only())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
