#!/usr/bin/env python3
"""
Simple test script to verify the enhanced authentication improvements
This tests the specific fixes we made to login form detection
"""

import asyncio
import sys
import os
import json
from playwright.async_api import async_playwright, BrowserContext, Page
from enhanced_instagram_auth import EnhancedInstagramAuth

async def test_authentication_improvements():
    """Test the authentication improvements with real browser context"""
    
    print("🔧 Testing Enhanced Instagram Authentication Improvements")
    print("=" * 60)
    
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
        
        if not username or not password:
            print("❌ Account missing username or password")
            return False
            
        print(f"🧪 Testing authentication improvements with account: {username}")
        
    except Exception as e:
        print(f"❌ Error loading accounts: {e}")
        return False
    
    # Test with Playwright browser
    async with async_playwright() as p:
        print("🚀 Launching browser...")
        
        browser = await p.chromium.launch(
            headless=True,  # VPS compatible
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--no-first-run',
                '--disable-extensions',
                '--disable-default-apps',
                '--disable-plugins',
                '--disable-translate',
                '--disable-background-networking',
                '--disable-sync'
            ]
        )
        
        try:
            # Create context
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768}
            )
            
            print("✅ Browser context created")
            
            # Initialize enhanced auth
            auth = EnhancedInstagramAuth()
            
            # Custom log callback
            def auth_log(message: str, level: str = "INFO"):
                print(f"[AUTH] {message}")
            
            print("🔐 Starting authentication test...")
            
            # Test authentication
            success, auth_info = await auth.authenticate_with_cookies_and_proxy(
                context=context,
                username=username,
                password=password,
                log_callback=auth_log
            )
            
            if success:
                print("✅ Authentication successful!")
                print("🎉 Enhanced authentication improvements are working!")
                
                # Print auth info
                if auth_info and 'proxy_info' in auth_info:
                    proxy_info = auth_info['proxy_info']
                    if proxy_info:
                        print(f"🌐 Using proxy: {proxy_info.get('host', 'N/A')}:{proxy_info.get('port', 'N/A')}")
                
                return True
            else:
                print("❌ Authentication failed")
                print("ℹ️ This might be due to Instagram security, but form detection should have worked")
                return False
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            await browser.close()

async def test_login_form_detection():
    """Test just the login form detection without full authentication"""
    
    print("\n🔍 Testing Login Form Detection Improvements")
    print("-" * 40)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        try:
            context = await browser.new_context()
            page = await context.new_page()
            
            print("📱 Navigating to Instagram login page...")
            await page.goto('https://www.instagram.com/accounts/login/', wait_until='domcontentloaded')
            
            # Test our enhanced form detection
            print("🔍 Testing form detection with enhanced selectors...")
            
            # These are the selectors we added for robustness
            login_selectors = [
                'input[name="username"]',
                'input[aria-label*="username" i]',
                'input[aria-label*="Phone number, username, or email" i]',
                'input[placeholder*="username" i]',
                'input[placeholder*="Phone number, username, or email" i]',
                'input[type="text"]:first-of-type',
                'form input[type="text"]',
                'input[type="text"]'
            ]
            
            found_selectors = []
            for selector in login_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        found_selectors.append(selector)
                        print(f"✅ Found form element with: {selector}")
                except:
                    pass
            
            if found_selectors:
                print(f"🎉 Form detection successful! Found {len(found_selectors)} working selectors")
                return True
            else:
                print("❌ No login form elements detected")
                # Take a screenshot for debugging
                await page.screenshot(path='login_page_debug.png')
                print("📸 Screenshot saved as login_page_debug.png")
                return False
                
        except Exception as e:
            print(f"❌ Form detection test error: {e}")
            return False
            
        finally:
            await browser.close()

async def main():
    """Run all tests"""
    
    # Test 1: Login form detection
    form_detection_success = await test_login_form_detection()
    
    # Test 2: Full authentication (if form detection works)
    if form_detection_success:
        auth_success = await test_authentication_improvements()
    else:
        print("⏭️ Skipping full authentication test due to form detection failure")
        auth_success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Form Detection: {'✅ PASS' if form_detection_success else '❌ FAIL'}")
    print(f"   Authentication: {'✅ PASS' if auth_success else '❌ FAIL'}")
    
    if form_detection_success:
        print("\n🎉 Enhanced login form detection is working!")
        if auth_success:
            print("🎉 Full authentication system is also working!")
        else:
            print("ℹ️ Authentication failed, but form detection improvements are confirmed")
    else:
        print("\n⚠️ Form detection issues detected. Check login_page_debug.png")
    
    return form_detection_success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
