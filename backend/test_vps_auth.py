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
                '--disable-gpu',
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--allow-running-insecure-content',
                '--disable-features=VizDisplayCompositor',
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }
        )
        
        page = await context.new_page()
        
        try:
            # Block Facebook domains
            await page.route("**facebook.com**", lambda route: route.abort())
            await page.route("**fb.com**", lambda route: route.abort())
            print("🚫 Blocked Facebook domains")
            
            # Test basic connectivity first
            print("🌐 Testing basic connectivity...")
            try:
                await page.goto("https://httpbin.org/ip", timeout=30000)
                ip_response = await page.content()
                print(f"✅ VPS IP check successful: {ip_response[:100]}...")
            except Exception as e:
                print(f"❌ Basic connectivity failed: {e}")
                return False
            
            # Now try Instagram
            print("🌐 Navigating to Instagram...")
            try:
                response = await page.goto("https://www.instagram.com/accounts/login/", 
                                         wait_until='networkidle', timeout=60000)
                
                print(f"📊 Response status: {response.status}")
                print(f"📊 Response headers: {dict(response.headers)}")
                
            except Exception as e:
                print(f"❌ Navigation to Instagram failed: {e}")
                return False
            
            # Wait for page to stabilize
            await asyncio.sleep(10)
            
            # Check current URL
            current_url = page.url
            print(f"📍 Current URL: {current_url}")
            
            # Check page title
            title = await page.title()
            print(f"📄 Page title: {title}")
            
            # Get full page content for analysis
            page_content = await page.content()
            content_length = len(page_content)
            print(f"📊 Page content length: {content_length} characters")
            
            # Check if we're on the right page
            if "instagram.com" not in current_url.lower():
                print(f"❌ Not on Instagram page. URL: {current_url}")
                return False
                
            if "facebook.com" in current_url.lower():
                print("❌ Redirected to Facebook - this indicates network/proxy issues")
                return False
            
            # Check for common blocking indicators
            blocking_keywords = [
                "blocked", "suspended", "unavailable", "access denied", 
                "forbidden", "not available", "error", "cloudflare"
            ]
            
            page_content_lower = page_content.lower()
            for keyword in blocking_keywords:
                if keyword in page_content_lower:
                    print(f"⚠️ Potential blocking detected: found '{keyword}' in page content")
            
            # Save page content for debugging
            try:
                with open('instagram_page_debug.html', 'w', encoding='utf-8') as f:
                    f.write(page_content)
                print("💾 Page content saved to instagram_page_debug.html")
            except Exception as e:
                print(f"⚠️ Could not save debug file: {e}")
            
            # Check if page is mostly empty
            if content_length < 1000:
                print("❌ Page content is suspiciously small - likely blocked or failed to load")
                print(f"📊 Content preview: {page_content[:500]}...")
                return False
            
            # Check for Instagram-specific content
            instagram_indicators = [
                "instagram" in page_content_lower,
                "log in" in page_content_lower,
                "username" in page_content_lower,
                "password" in page_content_lower,
                "_sharedData" in page_content,  # Instagram's JS data
                "www.instagram.com" in page_content,
            ]
            
            print(f"📊 Instagram content indicators:")
            indicators_passed = 0
            for i, indicator in enumerate(["Instagram", "Log in", "Username", "Password", "SharedData", "Instagram URL"]):
                status = "✅" if instagram_indicators[i] else "❌"
                print(f"  {indicator}: {status}")
                if instagram_indicators[i]:
                    indicators_passed += 1
            
            if indicators_passed < 2:
                print("❌ Page doesn't appear to be Instagram login page")
                return False
            
            # Handle potential blocking dialogs
            dialog_selectors = [
                'button:has-text("Allow all cookies")',
                'button:has-text("Accept all cookies")',
                'button:has-text("Accept")',
                'button:has-text("OK")',
                'button:has-text("Continue")',
                '[aria-label="Close"]',
                '[role="button"]:has-text("Allow")',
            ]
            
            for selector in dialog_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element and await element.is_visible():
                        await element.click()
                        print(f"✅ Dismissed dialog: {selector}")
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            # Wait longer for dynamic content
            print("⏳ Waiting for dynamic content to load...")
            await asyncio.sleep(10)
            
            # Enhanced input field detection
            print("🔍 Looking for login form elements...")
            
            # Try multiple selectors for input fields
            input_selectors = [
                'input',
                'input[type="text"]',
                'input[type="password"]',
                'input[name="username"]',
                'input[name="password"]',
                'input[aria-label*="username"]',
                'input[aria-label*="Password"]',
                'input[placeholder*="username"]',
                'input[placeholder*="Password"]',
                'form input',
                '[role="textbox"]'
            ]
            
            all_inputs = []
            for selector in input_selectors:
                try:
                    inputs = await page.query_selector_all(selector)
                    for inp in inputs:
                        if inp not in all_inputs:
                            all_inputs.append(inp)
                except:
                    continue
            
            print(f"📊 Total input fields found: {len(all_inputs)}")
            
            if len(all_inputs) == 0:
                print("❌ No input fields found - Instagram page may not have loaded properly")
                
                # Try to detect what went wrong
                print("🔍 Diagnostic checks:")
                
                # Check for JavaScript errors
                try:
                    errors = await page.evaluate('''() => {
                        return window.console && window.console.error ? 
                            JSON.stringify(window.console._errors || []) : 'No errors captured';
                    }''')
                    print(f"  JavaScript errors: {errors}")
                except:
                    print("  JavaScript errors: Could not check")
                
                # Check if we can access any form elements
                form_elements = await page.query_selector_all('form')
                print(f"  Forms found: {len(form_elements)}")
                
                button_elements = await page.query_selector_all('button')
                print(f"  Buttons found: {len(button_elements)}")
                
                return False
            
            # Analyze input fields
            print("🔍 Analyzing input fields...")
            username_found = False
            password_found = False
            
            for i, input_elem in enumerate(all_inputs):
                try:
                    attrs = await input_elem.evaluate('''
                        el => ({
                            name: el.name || '',
                            placeholder: el.placeholder || '',
                            type: el.type || '',
                            ariaLabel: el.ariaLabel || '',
                            id: el.id || '',
                            className: el.className || '',
                            visible: el.offsetParent !== null && el.offsetWidth > 0 && el.offsetHeight > 0,
                            value: el.value || ''
                        })
                    ''')
                    
                    print(f"  Input {i+1}: name='{attrs['name']}' type='{attrs['type']}' placeholder='{attrs['placeholder']}' visible={attrs['visible']}")
                    
                    # Check if it's a username field
                    if (attrs.get('name') in ['username', 'email'] or 
                        'username' in str(attrs.get('placeholder', '')).lower() or
                        'email' in str(attrs.get('placeholder', '')).lower() or
                        'username' in str(attrs.get('ariaLabel', '')).lower() or
                        (attrs.get('type') == 'text' and attrs.get('visible'))):
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
            import traceback
            traceback.print_exc()
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
    from instagram_accounts import instagram_accounts_manager, get_account_details
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
