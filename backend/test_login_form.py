#!/usr/bin/env python3
"""
Test Login Form Detection
Quick test to check if we can detect the Instagram login form
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import os

async def test_login_form_detection():
    """Test if we can detect Instagram login form"""
    
    def log(message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {message}", flush=True)
    
    print("=" * 60)
    print("🔍 TESTING LOGIN FORM DETECTION")
    print("=" * 60)
    
    try:
        async with async_playwright() as playwright:
            # Try to use Chrome
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.environ.get('USERNAME', '')),
            ]
            
            browser_args = {
                'headless': False,
                'args': ['--no-sandbox', '--disable-dev-shm-usage']
            }
            
            browser = None
            for chrome_path in chrome_paths:
                try:
                    if os.path.exists(chrome_path):
                        browser_args['executable_path'] = chrome_path
                        browser = await playwright.chromium.launch(**browser_args)
                        log(f"✅ Using Chrome from: {chrome_path}")
                        break
                except Exception as e:
                    log(f"⚠️ Failed Chrome path {chrome_path}: {e}")
                    continue
            
            if not browser:
                browser = await playwright.chromium.launch(**browser_args)
                log("✅ Using Chromium fallback")
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                locale='en-US'
            )
            
            page = await context.new_page()
            
            # Navigate to Instagram login
            log("🌐 Navigating to Instagram login page...")
            await page.goto("https://www.instagram.com/accounts/login/", wait_until='networkidle', timeout=60000)
            log("✅ Page loaded")
            
            # Wait for page to stabilize
            await asyncio.sleep(5)
            
            # Try to find login form
            login_form_selectors = [
                'input[name="username"]',
                'input[aria-label="Phone number, username, or email"]',
                'input[aria-label="Phone number, username or email address"]',
                '#loginForm input[name="username"]',
                'form input[name="username"]',
                'input[placeholder*="username"]',
                'input[placeholder*="email"]'
            ]
            
            form_found = False
            working_selector = None
            
            for i, selector in enumerate(login_form_selectors, 1):
                try:
                    log(f"🎯 Testing selector {i}/{len(login_form_selectors)}: {selector}")
                    element = await page.wait_for_selector(selector, state='visible', timeout=5000)
                    if element:
                        log(f"✅ FOUND! Login form with selector: {selector}")
                        form_found = True
                        working_selector = selector
                        break
                except Exception as e:
                    log(f"❌ Selector {i} failed: {str(e)[:100]}")
                    continue
            
            if form_found:
                log("🎉 SUCCESS! Login form detection working!")
                log(f"✅ Best selector: {working_selector}")
                
                # Take screenshot
                await page.screenshot(path="login_form_success.png")
                log("📸 Screenshot saved: login_form_success.png")
                
            else:
                log("❌ FAILED! Could not detect login form")
                
                # Take screenshot for debugging
                await page.screenshot(path="login_form_failed.png")
                log("📸 Debug screenshot saved: login_form_failed.png")
                
                # Get page content for debugging
                content = await page.content()
                with open("page_content.html", "w", encoding="utf-8") as f:
                    f.write(content)
                log("📄 Page content saved: page_content.html")
            
            # Keep browser open for 10 seconds for manual inspection
            log("👀 Keeping browser open for 10 seconds for inspection...")
            await asyncio.sleep(10)
            
            await context.close()
            await browser.close()
            log("🧹 Browser closed")
            
    except Exception as e:
        log(f"💥 Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_login_form_detection())