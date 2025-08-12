#!/usr/bin/env python3
"""
Enhanced VPS authentication test with better debugging
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from enhanced_instagram_auth import enhanced_auth
from instagram_cookie_manager import cookie_manager
from playwright.async_api import async_playwright

async def test_vps_browser_setup():
    """Test if browser can be launched properly on VPS"""
    print("🧪 Testing VPS Browser Setup...")
    
    try:
        async with async_playwright() as p:
            # Enhanced browser launch args for VPS
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-features=TranslateUI',
                    '--disable-ipc-flooding-protection'
                ]
            )
            print("✅ Browser launched successfully")
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York'
            )
            print("✅ Browser context created")
            
            page = await context.new_page()
            print("✅ Page created")
            
            await browser.close()
            return True
            
    except Exception as e:
        print(f"❌ Browser setup failed: {e}")
        return False

async def test_instagram_page_load():
    """Test if Instagram page loads properly on VPS"""
    print("\n🧪 Testing Instagram Page Load...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        try:
            # Block Facebook domains
            await page.route("**facebook.com**", lambda route: route.abort())
            await page.route("**fb.com**", lambda route: route.abort())
            print("🚫 Blocked Facebook domains")
            
            print("🌐 Navigating to Instagram...")
            await page.goto("https://www.instagram.com/accounts/login/", 
                           wait_until='domcontentloaded', timeout=60000)
            
            # Wait for page to stabilize
            await asyncio.sleep(5)
            
            # Check current URL
            current_url = page.url
            print(f"📍 Current URL: {current_url}")
            
            # Check page title
            title = await page.title()
            print(f"📄 Page title: {title}")
            
            # Check if we're on the right page
            if "instagram.com" not in current_url.lower():
                print(f"❌ Not on Instagram page. URL: {current_url}")
                return False
                
            if "facebook.com" in current_url.lower():
                print("❌ Redirected to Facebook - this indicates network/proxy issues")
                return False
            
            # Handle potential blocking dialogs
            blocking_dialogs = [
                'button:has-text("Allow all cookies")',
                'button:has-text("Accept all cookies")',
                'button:has-text("Accept")',
                'button:has-text("OK")',
                'button:has-text("Continue")',
                'button:has-text("Allow")',
                '[aria-label="Close"]'
            ]
            
            for selector in blocking_dialogs:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element and await element.is_visible():
                        await element.click()
                        print(f"✅ Dismissed dialog: {selector}")
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            # Wait longer for Instagram to load its dynamic content
            print("⏳ Waiting for Instagram content to load...")
            await asyncio.sleep(10)
            
            # Check for login form elements
            print("🔍 Looking for login form elements...")
            
            # Check for any input fields
            all_inputs = await page.query_selector_all('input')
            print(f"📊 Found {len(all_inputs)} input fields total")
            
            if len(all_inputs) == 0:
                # Try to get page content for debugging
                print("🔍 No input fields found. Checking page content...")
                page_content = await page.content()
                
                # Check if page contains Instagram login indicators
                content_checks = [
                    "Log in" in page_content,
                    "Instagram" in page_content,
                    "password" in page_content.lower(),
                    "username" in page_content.lower(),
                    "login" in page_content.lower()
                ]
                
                print(f"📊 Content analysis:")
                print(f"  Contains 'Log in': {content_checks[0]}")
                print(f"  Contains 'Instagram': {content_checks[1]}")
                print(f"  Contains 'password': {content_checks[2]}")
                print(f"  Contains 'username': {content_checks[3]}")
                print(f"  Contains 'login': {content_checks[4]}")
                
                # Check for error messages or blocks
                if "blocked" in page_content.lower() or "suspicious" in page_content.lower():
                    print("⚠️ Page content suggests IP/access may be blocked")
                
                return False
            
            # Analyze input fields
            print("🔍 Analyzing input fields...")
            username_found = False
            password_found = False
            
            for i, input_elem in enumerate(all_inputs):
                try:
                    attrs = await input_elem.evaluate('''
                        el => ({
                            name: el.name,
                            placeholder: el.placeholder,
                            type: el.type,
                            ariaLabel: el.ariaLabel,
                            id: el.id,
                            className: el.className,
                            visible: el.offsetParent !== null
                        })
                    ''')
                    
                    print(f"  Input {i+1}: {attrs}")
                    
                    # Check if it's a username field
                    if (attrs.get('name') == 'username' or 
                        'username' in str(attrs.get('ariaLabel', '')).lower() or
                        'email' in str(attrs.get('ariaLabel', '')).lower() or
                        attrs.get('type') == 'text'):
                        username_found = True
                        
                    # Check if it's a password field
                    if (attrs.get('name') == 'password' or 
                        attrs.get('type') == 'password'):
                        password_found = True
                        
                except Exception as e:
                    print(f"  Input {i+1}: Error reading attributes - {e}")
            
            print(f"\n📊 Login Form Analysis:")
            print(f"  Username field detected: {'✅' if username_found else '❌'}")
            print(f"  Password field detected: {'✅' if password_found else '❌'}")
            
            return username_found and password_found
            
        except Exception as e:
            print(f"❌ Error during page load test: {e}")
            return False
        finally:
            await browser.close()

async def test_real_account_auth():
    """Test authentication with a real account if available"""
    print("\n🧪 Testing Real Account Authentication...")
    
    # Check if we have any accounts
    accounts = cookie_manager.get_all_stored_accounts()
    if not accounts:
        print("⚠️ No stored accounts found for authentication testing")
        return
    
    # Use first account for testing
    test_account = accounts[0]['username']
    print(f"🎯 Testing with account: {test_account}")
    
    # Check cookies
    if cookie_manager.are_cookies_valid(test_account):
        print(f"✅ Account has valid cookies")
    else:
        print(f"⚠️ Account cookies are expired or invalid")
    
    # Load account details
    from instagram_accounts import get_account_details
    account_details = get_account_details(test_account)
    
    if account_details:
        print(f"✅ Account details loaded")
        print(f"  Has password: {'password' in account_details}")
        print(f"  Has TOTP: {'totp_secret' in account_details}")
    else:
        print(f"❌ No account details found")

async def main():
    """Run all VPS authentication tests"""
    print("🚀 Starting Enhanced VPS Authentication Test...\n")
    
    # Test 1: Browser setup
    browser_ok = await test_vps_browser_setup()
    if not browser_ok:
        print("❌ Browser setup failed - cannot continue tests")
        return
    
    # Test 2: Instagram page load
    page_ok = await test_instagram_page_load()
    if not page_ok:
        print("❌ Instagram page load failed - check network/proxy settings")
    
    # Test 3: Account authentication readiness
    await test_real_account_auth()
    
    print("\n" + "="*50)
    print("📊 VPS Test Summary:")
    print(f"  Browser Setup: {'✅ PASS' if browser_ok else '❌ FAIL'}")
    print(f"  Instagram Access: {'✅ PASS' if page_ok else '❌ FAIL'}")
    print("="*50)
    
    if browser_ok and page_ok:
        print("✅ VPS environment is ready for authentication!")
        print("💡 You can now run: python backend/instagram_daily_post.py")
    else:
        print("❌ VPS environment needs attention before running automation")
        if not page_ok:
            print("🔧 Suggestions:")
            print("  - Check VPS network connectivity to Instagram")
            print("  - Verify no proxy/firewall is blocking Instagram")
            print("  - Try running from a different VPS location")

if __name__ == "__main__":
    asyncio.run(main())
