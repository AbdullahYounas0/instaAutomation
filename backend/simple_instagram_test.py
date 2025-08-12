#!/usr/bin/env python3
"""
Simplified VPS Instagram test without problematic browser args
"""

import asyncio
import sys
import os
import time
import random
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from playwright.async_api import async_playwright

async def test_simple_instagram_access():
    """Test Instagram access with minimal configuration"""
    print("🚀 Simple Instagram Access Test")
    print("="*50)
    
    # Simple browser args that work on most VPS
    simple_args = [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--no-first-run',
        '--disable-background-timer-throttling'
    ]
    
    try:
        async with async_playwright() as p:
            print("🧪 Launching browser...")
            browser = await p.chromium.launch(
                headless=True,
                args=simple_args
            )
            
            print("✅ Browser launched successfully")
            
            # Create context with realistic settings
            context = await browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            print("✅ Page created")
            
            # Test basic connectivity first
            print("\n🌐 Testing basic connectivity...")
            try:
                await page.goto("https://httpbin.org/ip", timeout=30000)
                ip_content = await page.content()
                print("✅ Basic connectivity working")
            except Exception as e:
                print(f"❌ Basic connectivity failed: {e}")
                await browser.close()
                return False
            
            # Add delays to be more human-like
            print("\n⏳ Adding human-like delay...")
            await asyncio.sleep(random.uniform(3, 7))
            
            # Try Instagram with different strategies
            strategies = [
                ("Main Instagram", "https://www.instagram.com/"),
                ("Login Page", "https://www.instagram.com/accounts/login/"),
                ("Mobile Instagram", "https://www.instagram.com/?hl=en"),
            ]
            
            for strategy_name, url in strategies:
                print(f"\n🧪 Trying {strategy_name}: {url}")
                
                try:
                    # Block known tracking/analytics to appear more like a regular user
                    await page.route("**/*google-analytics*", lambda route: route.abort())
                    await page.route("**/*googletagmanager*", lambda route: route.abort())
                    await page.route("**/*facebook.com*", lambda route: route.abort())
                    await page.route("**/*fb.com*", lambda route: route.abort())
                    
                    response = await page.goto(url, 
                                             wait_until='domcontentloaded', 
                                             timeout=60000)
                    
                    status = response.status
                    print(f"   📊 Status: {status}")
                    
                    # Check current URL
                    current_url = page.url
                    print(f"   📍 Final URL: {current_url}")
                    
                    if status == 200:
                        # Wait for page to stabilize
                        await asyncio.sleep(8)
                        
                        # Get page info
                        title = await page.title()
                        content = await page.content()
                        content_length = len(content)
                        
                        print(f"   📄 Title: {title}")
                        print(f"   📊 Content length: {content_length}")
                        
                        # Check for Instagram indicators
                        content_lower = content.lower()
                        instagram_indicators = {
                            'instagram': 'instagram' in content_lower,
                            'login': 'login' in content_lower,
                            'username': 'username' in content_lower,
                            'password': 'password' in content_lower,
                            'sign in': 'sign in' in content_lower
                        }
                        
                        print("   📊 Content indicators:")
                        for indicator, found in instagram_indicators.items():
                            status_icon = "✅" if found else "❌"
                            print(f"     {indicator}: {status_icon}")
                        
                        # Look for input fields
                        inputs = await page.query_selector_all('input')
                        print(f"   📊 Input fields: {len(inputs)}")
                        
                        # Look for forms
                        forms = await page.query_selector_all('form')
                        print(f"   📊 Forms: {len(forms)}")
                        
                        if content_length > 5000 and any(instagram_indicators.values()):
                            print("   ✅ Instagram page loaded successfully!")
                            
                            # Save debug info
                            debug_filename = f"instagram_debug_{int(time.time())}.html"
                            with open(debug_filename, 'w', encoding='utf-8') as f:
                                f.write(content)
                            print(f"   💾 Debug saved to: {debug_filename}")
                            
                            await browser.close()
                            return True
                        else:
                            print("   ⚠️ Page loaded but content seems incomplete")
                    
                    elif status == 429:
                        print("   ❌ Rate limited (429) - IP is blocked")
                        
                    elif status in [403, 451]:
                        print(f"   ❌ Access forbidden ({status}) - IP/region blocked")
                        
                    else:
                        print(f"   ⚠️ Unexpected status: {status}")
                
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
                
                # Wait between attempts
                if strategy_name != strategies[-1][0]:  # Don't wait after last attempt
                    wait_time = random.uniform(10, 20)
                    print(f"   ⏳ Waiting {wait_time:.1f}s before next strategy...")
                    await asyncio.sleep(wait_time)
            
            await browser.close()
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def test_with_account():
    """Test authentication with the configured account"""
    print("\n🧪 Testing with Configured Account...")
    
    from instagram_accounts import instagram_accounts_manager
    
    accounts = instagram_accounts_manager.get_all_accounts()
    
    if not accounts:
        print("❌ No accounts configured")
        return
    
    account = accounts[0]  # Use first account
    username = account['username']
    
    print(f"👤 Testing account: {username}")
    print(f"   Has password: {'✅' if account.get('password') else '❌'}")
    print(f"   Has 2FA: {'✅' if account.get('totp_secret') else '❌'}")
    
    # Test 2FA if available
    if account.get('totp_secret'):
        try:
            import pyotp
            totp_secret = account['totp_secret']
            totp = pyotp.TOTP(totp_secret)
            current_code = totp.now()
            print(f"   🔐 Current 2FA code: {current_code}")
        except Exception as e:
            print(f"   ❌ 2FA test failed: {e}")

async def main():
    """Main test function"""
    success = await test_simple_instagram_access()
    
    if success:
        print("\n✅ SUCCESS! Instagram access is working")
        await test_with_account()
        print("\n🚀 You can now run: python backend/instagram_daily_post.py")
    else:
        print("\n❌ Instagram access blocked")
        print("\n🔧 Suggested solutions:")
        print("1. Wait 24 hours for rate limit reset")
        print("2. Try from different VPS location/provider")
        print("3. Add proxy configuration")
        print("4. Use different internet connection")
        
        await test_with_account()

if __name__ == "__main__":
    asyncio.run(main())
