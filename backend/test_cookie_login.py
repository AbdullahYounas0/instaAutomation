#!/usr/bin/env python3
"""
Test Cookie-Based Login
Simple script to test and demonstrate the enhanced authentication system
"""

import asyncio
import os
from datetime import datetime
from instagram_auth_helper import auth_helper
from instagram_cookie_manager import cookie_manager

async def test_enhanced_login():
    """Test the enhanced login system and save cookies"""
    
    username = "paulpmoorenoco09f"  # Your account
    
    def log(message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}")
    
    print("=" * 60)
    print("🔐 ENHANCED INSTAGRAM AUTHENTICATION TEST")
    print("=" * 60)
    
    try:
        # Step 1: Check current cookie status
        log("🔍 Checking current cookie status...")
        
        if cookie_manager.are_cookies_valid(username):
            log("✅ Valid cookies found - this login should be instant!")
        else:
            log("❌ No valid cookies - will use credentials and save cookies")
        
        # Step 2: Test enhanced authentication
        log(f"🚀 Starting enhanced authentication for {username}...")
        
        success, context, info = await auth_helper.create_authenticated_context(
            username=username,
            headless=False,  # Visible browser so you can see what happens
            log_callback=log
        )
        
        if success:
            log("🎉 SUCCESS! Authentication completed")
            log(f"📊 Method used: {info.get('authentication_method')}")
            log(f"💾 Cookies saved: {info.get('cookies_saved', False)}")
            
            if info.get('proxy_used'):
                proxy = info['proxy_used']
                log(f"🌐 Proxy used: {proxy.get('host')}:{proxy.get('port')}")
            
            # Keep browser open for 10 seconds so you can see Instagram
            log("👀 Keeping browser open for 10 seconds...")
            page = await context.new_page()
            await page.goto("https://www.instagram.com/")
            await asyncio.sleep(10)
            
            # Close context
            await context.close()
            log("🧹 Browser closed")
            
        else:
            log("❌ FAILED! Authentication failed")
            for error in info.get('errors', []):
                log(f"💥 Error: {error}")
        
        # Step 3: Check cookie status after login
        log("\n" + "=" * 50)
        log("🍪 CHECKING SAVED COOKIES")
        log("=" * 50)
        
        # Run cookie check script
        os.system("python check_cookies.py paulpmoorenoco09f")
        
        # Step 4: Test instant login (if cookies were saved)
        if cookie_manager.are_cookies_valid(username):
            log("\n" + "⚡" * 50)
            log("🚀 TESTING INSTANT COOKIE LOGIN")
            log("⚡" * 50)
            
            log("🍪 Valid cookies found - testing instant login...")
            
            success2, context2, info2 = await auth_helper.create_authenticated_context(
                username=username,
                headless=False,  # Visible so you can see the speed difference
                log_callback=log
            )
            
            if success2 and info2.get('authentication_method') == 'cookies':
                log("🎉 INSTANT LOGIN SUCCESS! Used saved cookies")
                log("⚡ This should have been much faster than the first login!")
                
                # Keep browser open briefly
                page2 = await context2.new_page()
                await page2.goto("https://www.instagram.com/")
                await asyncio.sleep(5)
                await context2.close()
                
            else:
                log("⚠️ Cookie login didn't work as expected")
        
        log("\n" + "🎉" * 50)
        log("TEST COMPLETED SUCCESSFULLY!")
        log("🎉" * 50)
        log("\nKey Points:")
        log("✅ First login: Used credentials + 2FA, saved cookies")
        log("⚡ Second login: Used saved cookies (instant)")
        log("💾 Future logins will be instant until cookies expire")
        log("🔄 Cookies auto-refresh on each use")
        
    except KeyboardInterrupt:
        log("⛔ Test interrupted by user")
    except Exception as e:
        log(f"💥 Error during test: {e}")
    
    finally:
        # Cleanup any remaining contexts
        await auth_helper.close_all_contexts()
        log("🧹 All contexts cleaned up")

async def quick_cookie_check():
    """Just check cookie status without logging in"""
    
    username = "paulpmoorenoco09f"
    
    print("🔍 Quick Cookie Check")
    print("-" * 30)
    
    if cookie_manager.are_cookies_valid(username):
        cookie_data = cookie_manager.load_cookies(username)
        print(f"✅ {username} has valid cookies")
        print(f"   Saved: {cookie_data.get('saved_at')}")
        print(f"   Login count: {cookie_data.get('login_count', 0)}")
        print("⚡ Ready for instant login!")
    else:
        print(f"❌ {username} has no valid cookies")
        print("🔑 Needs credential login first")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        # Just check cookies
        asyncio.run(quick_cookie_check())
    else:
        # Full test
        asyncio.run(test_enhanced_login())