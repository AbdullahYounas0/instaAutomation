#!/usr/bin/env python3
"""
Test the authentication fixes for VPS environment
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

async def test_cookie_validation():
    """Test if cookies are being detected properly"""
    print("🧪 Testing Cookie Validation...")
    
    # List all stored accounts
    accounts = cookie_manager.get_all_stored_accounts()
    print(f"📊 Found {len(accounts)} stored accounts:")
    
    for account in accounts:
        username = account['username']
        is_valid = account['is_valid']
        print(f"  • {username}: {'✅ Valid' if is_valid else '❌ Invalid'}")
        
        # Test individual validation
        print(f"    - Testing cookie_manager.are_cookies_valid('{username}'): {cookie_manager.are_cookies_valid(username)}")
        
        # Load cookie data for debugging
        cookie_data = cookie_manager.load_cookies(username)
        if cookie_data:
            print(f"    - Session expires at: {cookie_data.get('session_expires_at')}")
            print(f"    - Saved at: {cookie_data.get('saved_at')}")
            print(f"    - Last used: {cookie_data.get('last_used')}")
            print(f"    - Login count: {cookie_data.get('login_count')}")
            
            cookies = cookie_data.get('cookies', [])
            cookie_names = [c.get('name') for c in cookies]
            essential_cookies = ['sessionid', 'csrftoken']
            print(f"    - Has sessionid: {'sessionid' in cookie_names}")
            print(f"    - Has csrftoken: {'csrftoken' in cookie_names}")
            print(f"    - Total cookies: {len(cookies)}")

async def test_password_field_detection():
    """Test password field detection on Instagram login page"""
    print("\n🧪 Testing Password Field Detection...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Use headless for VPS testing
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        try:
            print("🌐 Navigating to Instagram login page...")
            await page.goto("https://www.instagram.com/accounts/login/", 
                           wait_until='domcontentloaded', timeout=30000)
            
            print("⏳ Waiting for page to load...")
            await asyncio.sleep(5)
            
            # Check for blocking dialogs
            blocking_selectors = [
                'button:has-text("Allow all cookies")',
                'button:has-text("Accept")',
                'button:has-text("OK")',
                'button:has-text("Continue")'
            ]
            
            for selector in blocking_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=2000)
                    if element:
                        await element.click()
                        print(f"✅ Dismissed blocking element: {selector}")
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            print("🔍 Looking for username and password fields...")
            
            # Test username selectors
            username_selectors = [
                'input[name="username"]',
                'input[aria-label="Phone number, username, or email"]',
                'input[type="text"]'
            ]
            
            username_found = False
            for selector in username_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        attrs = await element.evaluate('el => ({name: el.name, placeholder: el.placeholder, type: el.type, ariaLabel: el.ariaLabel})')
                        print(f"  ✅ Username field found: {selector} - {attrs}")
                        username_found = True
                        break
                except:
                    print(f"  ❌ Username selector failed: {selector}")
            
            # Test password selectors
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[aria-label="Password"]'
            ]
            
            password_found = False
            for selector in password_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        attrs = await element.evaluate('el => ({name: el.name, placeholder: el.placeholder, type: el.type, ariaLabel: el.ariaLabel})')
                        print(f"  ✅ Password field found: {selector} - {attrs}")
                        password_found = True
                        break
                except:
                    print(f"  ❌ Password selector failed: {selector}")
            
            # List all input fields for debugging
            all_inputs = await page.query_selector_all('input')
            print(f"\n📊 Total input fields found: {len(all_inputs)}")
            
            for i, input_elem in enumerate(all_inputs[:10]):  # Show first 10
                try:
                    attrs = await input_elem.evaluate('el => ({name: el.name, placeholder: el.placeholder, type: el.type, ariaLabel: el.ariaLabel, id: el.id, visible: el.offsetParent !== null})')
                    print(f"  Input {i+1}: {attrs}")
                except:
                    pass
            
            print(f"\n📊 Summary:")
            print(f"  Username field: {'✅ Found' if username_found else '❌ Not found'}")
            print(f"  Password field: {'✅ Found' if password_found else '❌ Not found'}")
            
        except Exception as e:
            print(f"❌ Error during test: {e}")
        finally:
            await browser.close()

async def main():
    """Run all tests"""
    print("🚀 Starting Authentication Fixes Test...\n")
    
    await test_cookie_validation()
    await test_password_field_detection()
    
    print("\n✅ Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
